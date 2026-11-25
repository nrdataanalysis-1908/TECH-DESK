"""Operações locais allowlisted, com confirmação, privilégio mínimo e auditoria."""

import collections.abc
import ctypes
import json
import logging
import os
import platform
import stat
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from techdesk.core.support_tools import (
    backup_event_logs,
    clear_event_logs_after_backup,
)

LOGGER = logging.getLogger("techdesk.operations")


@dataclass(frozen=True)
class Operation:
    key: str
    title: str
    description: str
    risk: str
    requires_admin: bool
    timeout_seconds: int


OPERATIONS = {
    "flush_dns": Operation(
        "flush_dns", "Flush DNS cache",
        "Clears the local DNS cache; subsequent queries will be resolved again.",
        "L1 — low impact", True, 30,
    ),
    "cleanup_temp": Operation(
        "cleanup_temp", "Clean temporary files",
        "Removes all regular files from the user's TEMP directory, regardless of age. "
        "Directories and symbolic links are preserved; locked or inaccessible files are skipped.",
        "L2 — file deletion", False, 120,
    ),
    "restart_spooler": Operation(
        "restart_spooler", "Restart Print Spooler",
        "Stops and starts the Print Spooler; pending jobs may be affected.",
        "L2 — printing impact", True, 60,
    ),
    "sfc_scan": Operation(
        "sfc_scan", "Verify and repair Windows system files (SFC)",
        "Runs sfc /scannow. This may take several minutes.",
        "L2 — system repair", True, 1800,
    ),
    "dism_restore": Operation(
        "dism_restore", "Repair Windows image (DISM)",
        "Runs DISM /Online /Cleanup-Image /RestoreHealth. This may take a while "
        "and may use Windows Update.",
        "L2 — system repair", True, 3600,
    ),
    "restart_explorer": Operation(
        "restart_explorer", "Restart Windows Explorer",
        "Restarts the current session shell; the taskbar and desktop may briefly flicker.",
        "L1 — shell restart", False, 30,
    ),
    "clear_print_queue": Operation(
        "clear_print_queue", "Clear print queue",
        "Removes all pending jobs from the local queue and restarts the Spooler. "
        "Removed jobs cannot be printed.",
        "L3 — job deletion", True, 90,
    ),
    "create_restore_point": Operation(
        "create_restore_point", "Create restore point",
        "Requests a Windows restore point before future changes. "
        "Requires System Protection to be enabled.",
        "L1 — preventive protection", True, 120,
    ),
    "check_disk": Operation(
        "check_disk", "Scan Windows drive",
        "Runs CHKDSK online with /scan on the system drive without scheduling a restart.",
        "L1 — scan", True, 900,
    ),
    "renew_ip": Operation(
        "renew_ip", "Renew IP address (DHCP)",
        "Requests a new DHCP lease; connectivity may briefly fluctuate during renewal.",
        "L2 — temporary network impact", True, 90,
    ),
    "reset_winsock": Operation(
        "reset_winsock", "Reset Winsock catalog",
        "Resets the Windows network catalog. Restarting the computer is recommended.",
        "L3 — network change", True, 60,
    ),
    "empty_recycle_bin": Operation(
        "empty_recycle_bin", "Empty Recycle Bin",
        "Permanently deletes the current user's Recycle Bin items. This cannot be undone.",
        "L3 — permanent deletion", False, 120,
    ),
    "restart_audio": Operation(
        "restart_audio", "Restart audio service",
        "Restarts the Windows audio service; active applications may briefly lose audio.",
        "L2 — audio impact", True, 60,
    ),
    "flush_arp": Operation(
        "flush_arp", "Flush ARP cache",
        "Removes dynamic entries from the ARP cache; they will be relearned as communication resumes.",
        "L1 — low impact", True, 30,
    ),
    "quick_defender_scan": Operation(
        "quick_defender_scan", "Run Microsoft Defender quick scan",
        "Starts a Microsoft Defender quick scan. The scan continues in the background.",
        "L1 — scan de segurança", True, 120,
    ),
    "update_defender_signatures": Operation(
        "update_defender_signatures", "Update Microsoft Defender signatures",
        "Requests a Microsoft Defender security intelligence update.",
        "L1 — security update", True, 180,
    ),
    "restart_windows_update": Operation(
        "restart_windows_update", "Restart Windows Update service",
        "Restarts the wuauserv service; active downloads or installations may be interrupted.",
        "L2 — update impact", True, 90,
    ),
    "clear_thumbnail_cache": Operation(
        "clear_thumbnail_cache", "Rebuild thumbnail cache",
        "Temporarily closes Explorer, removes the user's thumbnail caches, and restarts the shell.",
        "L2 — shell restart", False, 90,
    ),
    "update_group_policy": Operation(
        "update_group_policy", "Update Group Policies (GPO)",
        "Runs gpupdate /force to refresh user and computer policies.",
        "L2 — policy change", True, 240,
    ),
    "backup_event_logs": Operation(
        "backup_event_logs", "Export event logs",
        "Exports Application, System, Setup, and Security logs to EVTX files in a dated folder.",
        "L1 — diagnostic backup", True, 300,
    ),
    "clear_event_logs": Operation(
        "clear_event_logs", "Clear Application and Setup logs (with backup)",
        "Exports Application and Setup before cleanup. The Security log is never cleared.",
        "L3 — audit modification", True, 300,
    ),
    "winget_upgrade_all": Operation(
        "winget_upgrade_all", "Upgrade applications with Winget",
        "Runs winget upgrade --all. Updates may change versions and close applications.",
        "L2 — software change", False, 3600,
    ),

}

@dataclass
class OperationResult:
    success: bool
    message: str
    output: str = ""


def is_windows() -> bool:
    return platform.system() == "Windows"


def is_admin() -> bool:
    if not is_windows():
        return False
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except (AttributeError, OSError):
        return False


def _audit(operation: str, result: str) -> None:
    """Registra metadados sem incluir saída potencialmente sensível dos comandos."""
    try:
        audit_dir = Path.home() / "AppData" / "Local" / "NRTech" / "TechDesk" / "logs"
        audit_dir.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "operation": operation,
            "result": result,
            "host": platform.node(),
        }
        with (audit_dir / "operations.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        LOGGER.exception("Unable to write audit record for operation %s", operation)


def _output_encoding() -> str:
    """Usa a página OEM do Windows para decodificar utilitários nativos."""
    if not is_windows():
        return "utf-8"
    try:
        code_page = int(ctypes.windll.kernel32.GetOEMCP())
        return f"cp{code_page}" if code_page else "utf-8"
    except (AttributeError, OSError, ValueError):
        return "utf-8"


def _run(command: list[str], timeout: int) -> OperationResult:
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding=_output_encoding(),
            errors="replace",
            timeout=timeout,
            check=False,
            shell=False,
        )
    except subprocess.TimeoutExpired:
        return OperationResult(False, f"Timed out ({timeout}s).")
    except OSError as exc:
        return OperationResult(False, f"Unable to start operation: {exc}")

    output = "\n".join(part.strip() for part in (completed.stdout, completed.stderr) if part.strip())
    if completed.returncode == 0:
        return OperationResult(True, "Operation completed.", output[-12000:])
    return OperationResult(
        False,
        f"Command finished with exit code {completed.returncode}.",
        output[-12000:],
    )


def _iter_temp_files(root: Path):
    """Percorre somente arquivos regulares; não segue links nem pontos de reanálise."""
    pending = [root]
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    while pending:
        current = pending.pop()
        try:
            with os.scandir(current) as entries:
                for entry in entries:
                    try:
                        metadata = entry.stat(follow_symlinks=False)
                        attributes = getattr(metadata, "st_file_attributes", 0)
                        if stat.S_ISLNK(metadata.st_mode) or attributes & reparse_flag:
                            continue
                        if stat.S_ISDIR(metadata.st_mode):
                            pending.append(Path(entry.path))
                        elif stat.S_ISREG(metadata.st_mode):
                            yield Path(entry.path), metadata.st_size
                    except OSError:
                        continue
        except OSError:
            continue


def preview_temp_cleanup(now: datetime | None = None) -> tuple[int, int]:
    """Conta todos os arquivos regulares eligible, sem limite de idade."""
    del now  # Mantido por compatibilidade com chamadas existentes.
    root = Path(tempfile.gettempdir()).resolve()
    count = total_bytes = 0
    for _, size in _iter_temp_files(root):
        count += 1
        total_bytes += size
    return count, total_bytes


def _cleanup_temp() -> OperationResult:
    """Remove arquivos regulares da TEMP, sem limite de idade e sem seguir reparse points."""
    root = Path(tempfile.gettempdir()).resolve()
    removed = failed = freed = 0
    for path, size in _iter_temp_files(root):
        try:
            path.unlink()
            removed += 1
            freed += size
        except OSError:
            failed += 1
    return OperationResult(
        True,
        f"Limpeza concluída: {removed} file(s) removido(s), "
        f"{freed / (1024**2):.2f} MiB liberados; {failed} ignorado(s) por bloqueio/permissão.",
    )


def execute_operation(
    key: str,
    confirm: collections.abc.Callable[[Operation], bool],
) -> OperationResult:
    """Executa uma operação conhecida apenas após confirmação explícita."""
    if key not in OPERATIONS:
        raise ValueError(f"Operação not authorized: {key}")
    operation = OPERATIONS[key]

    if not is_windows():
        return OperationResult(False, "Operações administrativas disponíveis Windows only.")
    if not confirm(operation):
        _audit(key, "cancelled")
        return OperationResult(False, "Operação cancelled pelo usuário.")
    if operation.requires_admin and not is_admin():
        _audit(key, "blocked_not_admin")
        return OperationResult(
            False,
            "Esta operação exige PowerShell/terminal executado como Administrator. "
            "Feche o TECH DESK e reabra-o com privilégios elevados.",
        )

    if key == "cleanup_temp":
        result = _cleanup_temp()
    elif key == "flush_dns":
        result = _run(["ipconfig.exe", "/flushdns"], operation.timeout_seconds)
    elif key == "restart_spooler":
        result = _run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
             "Restart-Service -Name Spooler -Force -ErrorAction Stop"],
            operation.timeout_seconds,
        )
    elif key == "sfc_scan":
        result = _run(["sfc.exe", "/scannow"], operation.timeout_seconds)
    elif key == "dism_restore":
        result = _run(
            ["DISM.exe", "/Online", "/Cleanup-Image", "/RestoreHealth"],
            operation.timeout_seconds,
        )
    elif key == "restart_explorer":
        result = _run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
             ("$ErrorActionPreference='Stop'; Get-Process explorer -ErrorAction SilentlyContinue | "
              "Stop-Process -Force; Start-Sleep -Milliseconds 700; Start-Process explorer.exe")],
            operation.timeout_seconds,
        )
    elif key == "clear_print_queue":
        script = (
            "$ErrorActionPreference='Stop'; Stop-Service Spooler -Force; "
            "try { Get-ChildItem -LiteralPath ($env:windir + "
            "'\\System32\\spool\\PRINTERS') -File -ErrorAction Stop | "
            "Remove-Item -Force -ErrorAction Stop } "
            "finally { Start-Service Spooler -ErrorAction Stop }"
        )
        result = _run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
            operation.timeout_seconds,
        )
    elif key == "create_restore_point":
        result = _run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
             ("Checkpoint-Computer -Description 'TECH DESK - Ponto de restauracao' "
              "-RestorePointType MODIFY_SETTINGS -ErrorAction Stop")],
            operation.timeout_seconds,
        )
    elif key == "check_disk":
        result = _run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
             "chkdsk.exe $env:SystemDrive /scan"],
            operation.timeout_seconds,
        )
    elif key == "renew_ip":
        result = _run(["ipconfig.exe", "/renew"], operation.timeout_seconds)
    elif key == "reset_winsock":
        result = _run(["netsh.exe", "winsock", "reset"], operation.timeout_seconds)
    elif key == "empty_recycle_bin":
        result = _run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
             "Clear-RecycleBin -Force -ErrorAction Stop"],
            operation.timeout_seconds,
        )
    elif key == "restart_audio":
        result = _run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
             "Restart-Service -Name Audiosrv -Force -ErrorAction Stop"],
            operation.timeout_seconds,
        )
    elif key == "flush_arp":
        result = _run(["arp.exe", "-d", "*"], operation.timeout_seconds)
    elif key == "quick_defender_scan":
        result = _run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
             "Start-MpScan -ScanType QuickScan -ErrorAction Stop"],
            operation.timeout_seconds,
        )
    elif key == "update_defender_signatures":
        result = _run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
             "Update-MpSignature -ErrorAction Stop"],
            operation.timeout_seconds,
        )
    elif key == "restart_windows_update":
        result = _run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
             "Restart-Service -Name wuauserv -Force -ErrorAction Stop"],
            operation.timeout_seconds,
        )
    elif key == "update_group_policy":
        result = _run(["gpupdate.exe", "/force"], operation.timeout_seconds)
    elif key == "backup_event_logs":
        backup = backup_event_logs()
        result = OperationResult(backup.success, backup.message, backup.output)
    elif key == "clear_event_logs":
        backup = clear_event_logs_after_backup()
        result = OperationResult(backup.success, backup.message, backup.output)
    elif key == "winget_upgrade_all":
        result = _run(
            ["winget.exe", "upgrade", "--all", "--accept-source-agreements",
             "--accept-package-agreements"],
            operation.timeout_seconds,
        )

    elif key == "clear_thumbnail_cache":
        script = (
            "$ErrorActionPreference='Stop'; "
            "Get-Process explorer -ErrorAction SilentlyContinue | Stop-Process -Force; "
            "try { Start-Sleep -Milliseconds 700; "
            "Get-ChildItem -LiteralPath ($env:LOCALAPPDATA + "
            "'\\Microsoft\\Windows\\Explorer') -Filter 'thumbcache_*.db' -File "
            "-ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction Stop } "
            "finally { Start-Process explorer.exe }"
        )
        result = _run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
            operation.timeout_seconds,
        )
    else:
        raise ValueError(f"Operação sem executor: {key}")

    _audit(key, "success" if result.success else "failure")
    return result
