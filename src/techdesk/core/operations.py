"""Operações locais allowlisted, com confirmação, privilégio mínimo e auditoria."""

from collections.abc import Callable
import ctypes
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import json
import logging
from pathlib import Path
import platform
import subprocess
import tempfile


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
        "flush_dns", "Limpar cache DNS",
        "Descarta o cache DNS local; novas consultas serão resolvidas novamente.",
        "L1 — baixo impacto", True, 30,
    ),
    "cleanup_temp": Operation(
        "cleanup_temp", "Limpar arquivos temporários antigos",
        "Remove somente arquivos regulares na pasta TEMP do usuário com mais de 7 dias. "
        "Pastas, links simbólicos e arquivos recentes são preservados.",
        "L2 — exclusão de arquivos", False, 120,
    ),
    "restart_spooler": Operation(
        "restart_spooler", "Reiniciar serviço de impressão",
        "Interrompe e inicia o Spooler de Impressão; trabalhos pendentes podem ser afetados.",
        "L2 — impacto em impressão", True, 60,
    ),
    "sfc_scan": Operation(
        "sfc_scan", "Verificar e reparar arquivos do Windows (SFC)",
        "Executa sfc /scannow. Pode levar vários minutos.",
        "L2 — reparo do sistema", True, 1800,
    ),
    "dism_restore": Operation(
        "dism_restore", "Reparar imagem do Windows (DISM)",
        "Executa DISM /Online /Cleanup-Image /RestoreHealth. Pode levar bastante tempo "
        "e utilizar Windows Update.",
        "L2 — reparo do sistema", True, 3600,
    ),
    "restart_explorer": Operation(
        "restart_explorer", "Reiniciar Windows Explorer",
        "Reinicia o shell da sessão atual; a barra de tarefas e a área de trabalho podem piscar.",
        "L1 — reinício do shell", False, 30,
    ),
    "clear_print_queue": Operation(
        "clear_print_queue", "Esvaziar fila de impressão",
        "Remove todos os trabalhos pendentes da fila local e reinicia o Spooler. "
        "Trabalhos removidos não poderão ser impressos.",
        "L3 — exclusão de trabalhos", True, 90,
    ),
    "create_restore_point": Operation(
        "create_restore_point", "Criar ponto de restauração",
        "Solicita ao Windows um ponto de restauração antes de mudanças futuras. "
        "Depende da Proteção do Sistema estar habilitada.",
        "L1 — proteção preventiva", True, 120,
    ),
    "check_disk": Operation(
        "check_disk", "Verificar unidade do Windows",
        "Executa CHKDSK online com /scan na unidade do sistema, sem agendar reinicialização.",
        "L1 — verificação", True, 900,
    ),
    "renew_ip": Operation(
        "renew_ip", "Renovar endereço IP (DHCP)",
        "Solicita nova concessão DHCP; a conectividade pode oscilar durante a renovação.",
        "L2 — impacto temporário na rede", False, 90,
    ),
    "reset_winsock": Operation(
        "reset_winsock", "Redefinir catálogo Winsock",
        "Redefine o catálogo de rede do Windows. A reinicialização do computador é recomendada.",
        "L3 — alteração de rede", True, 60,
    ),
    "empty_recycle_bin": Operation(
        "empty_recycle_bin", "Esvaziar Lixeira",
        "Exclui permanentemente os itens da Lixeira do usuário atual. Não é possível desfazer.",
        "L3 — exclusão permanente", False, 120,
    ),
    "restart_audio": Operation(
        "restart_audio", "Reiniciar serviço de áudio",
        "Reinicia o serviço de áudio do Windows; aplicativos em uso podem perder áudio por instantes.",
        "L2 — impacto em áudio", True, 60,
    ),
    "flush_arp": Operation(
        "flush_arp", "Limpar cache ARP",
        "Remove entradas dinâmicas do cache ARP; elas serão reaprendidas conforme a comunicação.",
        "L1 — baixo impacto", True, 30,
    ),
    "quick_defender_scan": Operation(
        "quick_defender_scan", "Executar verificação rápida do Defender",
        "Inicia uma verificação rápida com o Microsoft Defender. O exame continua em segundo plano.",
        "L1 — verificação de segurança", True, 120,
    ),
    "update_defender_signatures": Operation(
        "update_defender_signatures", "Atualizar assinaturas do Defender",
        "Solicita ao Microsoft Defender a atualização das definições de segurança.",
        "L1 — atualização de segurança", True, 180,
    ),
    "restart_windows_update": Operation(
        "restart_windows_update", "Reiniciar serviço Windows Update",
        "Reinicia o serviço wuauserv; downloads ou instalações em andamento podem ser interrompidos.",
        "L2 — impacto em atualizações", True, 90,
    ),
    "clear_thumbnail_cache": Operation(
        "clear_thumbnail_cache", "Reconstruir cache de miniaturas",
        "Fecha temporariamente o Explorer, remove caches de miniaturas do usuário e reinicia o shell.",
        "L2 — reinício do shell", False, 90,
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
        LOGGER.exception("Não foi possível gravar a auditoria da operação %s", operation)


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
        return OperationResult(False, f"Tempo limite excedido ({timeout}s).")
    except OSError as exc:
        return OperationResult(False, f"Não foi possível iniciar a operação: {exc}")

    output = "\n".join(part.strip() for part in (completed.stdout, completed.stderr) if part.strip())
    if completed.returncode == 0:
        return OperationResult(True, "Operação concluída.", output[-12000:])
    return OperationResult(
        False,
        f"Comando finalizado com código {completed.returncode}.",
        output[-12000:],
    )


def preview_temp_cleanup(now: datetime | None = None) -> tuple[int, int]:
    """Conta arquivos elegíveis e bytes; não remove nem altera nada."""
    root = Path(tempfile.gettempdir()).resolve()
    cutoff = (now or datetime.now()).timestamp() - timedelta(days=7).total_seconds()
    count = total_bytes = 0
    try:
        for path in root.rglob("*"):
            try:
                if path.is_symlink() or not path.is_file():
                    continue
                resolved = path.resolve()
                if root not in resolved.parents:
                    continue
                stat = path.stat()
                if stat.st_mtime < cutoff:
                    count += 1
                    total_bytes += stat.st_size
            except (OSError, PermissionError):
                continue
    except OSError:
        return 0, 0
    return count, total_bytes


def _cleanup_temp() -> OperationResult:
    root = Path(tempfile.gettempdir()).resolve()
    cutoff = (datetime.now() - timedelta(days=7)).timestamp()
    removed = failed = freed = 0
    try:
        for path in root.rglob("*"):
            try:
                if path.is_symlink() or not path.is_file():
                    continue
                resolved = path.resolve()
                if root not in resolved.parents:
                    continue
                stat = path.stat()
                if stat.st_mtime >= cutoff:
                    continue
                path.unlink()
                removed += 1
                freed += stat.st_size
            except (OSError, PermissionError):
                failed += 1
    except OSError as exc:
        return OperationResult(False, f"Falha ao percorrer a pasta TEMP: {exc}")
    return OperationResult(
        True,
        f"Limpeza concluída: {removed} arquivo(s) removido(s), "
        f"{freed / (1024**2):.2f} MiB liberados; {failed} ignorado(s) por bloqueio/permissão.",
    )


def execute_operation(
    key: str,
    confirm: Callable[[Operation], bool],
) -> OperationResult:
    """Executa uma operação conhecida apenas após confirmação explícita."""
    if key not in OPERATIONS:
        raise ValueError(f"Operação não autorizada: {key}")
    operation = OPERATIONS[key]

    if not is_windows():
        return OperationResult(False, "Operações administrativas disponíveis somente no Windows.")
    if not confirm(operation):
        _audit(key, "cancelled")
        return OperationResult(False, "Operação cancelada pelo usuário.")
    if operation.requires_admin and not is_admin():
        _audit(key, "blocked_not_admin")
        return OperationResult(
            False,
            "Esta operação exige PowerShell/terminal executado como Administrador. "
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
