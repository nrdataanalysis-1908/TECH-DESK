"""Operações locais allowlisted, com confirmação, privilégio mínimo e auditoria."""

import ctypes
import json
import logging
import platform
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable


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
        "L1 — baixo impacto", False, 30,
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
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "operation": operation,
            "result": result,
            "host": platform.node(),
        }
        with (audit_dir / "operations.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        LOGGER.exception("Não foi possível gravar a auditoria da operação %s", operation)


def _run(command: list[str], timeout: int) -> OperationResult:
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
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
    else:
        raise ValueError(f"Operação sem executor: {key}")

    _audit(key, "success" if result.success else "failure")
    return result
