"""Ferramentas adicionais de suporte Windows com comandos fixos e validação local."""

import hashlib
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

MAX_DOWNLOAD_BYTES = 100 * 1024 * 1024
EVENT_LOGS = ("Application", "System", "Setup", "Security")


@dataclass
class SupportToolResult:
    success: bool
    message: str
    output: str = ""


def _run(command: list[str], timeout: int = 120) -> SupportToolResult:
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=timeout, check=False, shell=False,
        )
    except subprocess.TimeoutExpired:
        return SupportToolResult(False, f"Tempo limite excedido ({timeout}s).")
    except OSError as exc:
        return SupportToolResult(False, f"Não foi possível iniciar: {exc}")
    output = "\n".join(x.strip() for x in (result.stdout, result.stderr) if x.strip())
    if result.returncode == 0:
        return SupportToolResult(True, "Operação concluída.", output[-12000:])
    return SupportToolResult(False, f"Código de saída: {result.returncode}.", output[-12000:])


def open_windows_tool(key: str) -> SupportToolResult:
    """Abre somente ferramentas locais previamente autorizadas."""
    commands = {
        "disk_cleanup": ["cleanmgr.exe"],
        "system_info": ["msinfo32.exe"],
        "device_manager": ["mmc.exe", "devmgmt.msc"],
        "powershell": ["powershell.exe", "-NoLogo", "-NoProfile"],
    }
    if key == "speedtest":
        try:
            return SupportToolResult(
                bool(webbrowser.open("https://www.speedtest.net", new=2)),
                "Teste de velocidade aberto no navegador padrão."
            )
        except webbrowser.Error as exc:
            return SupportToolResult(False, f"Não foi possível abrir o navegador: {exc}")
    if key not in commands:
        raise ValueError(f"Ferramenta não autorizada: {key}")
    try:
        subprocess.Popen(commands[key], shell=False)
    except OSError as exc:
        return SupportToolResult(False, f"Não foi possível abrir a ferramenta: {exc}")
    return SupportToolResult(True, "Ferramenta do Windows iniciada.")


def backup_event_logs(log_names: tuple[str, ...] = EVENT_LOGS) -> SupportToolResult:
    """Exporta logs EVTX para pasta datada; nunca limpa os registros."""
    if not log_names or any(name not in EVENT_LOGS for name in log_names):
        raise ValueError("Conjunto de logs não autorizado.")
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    destination = Path.home() / "Documents" / "NRTech" / "TechDesk" / "EventBackups" / stamp
    try:
        destination.mkdir(parents=True, exist_ok=False)
    except OSError as exc:
        return SupportToolResult(False, f"Não foi possível criar a pasta de backup: {exc}")
    exported, failures = [], []
    for name in log_names:
        target = destination / f"{name}.evtx"
        result = _run(["wevtutil.exe", "epl", name, str(target)], timeout=120)
        if result.success and target.exists() and target.stat().st_size > 0:
            exported.append(name)
        else:
            failures.append(f"{name}: {result.message} {result.output}".strip())
    summary = f"Backups exportados: {', '.join(exported) if exported else 'nenhum'}. Pasta: {destination}"
    if failures:
        return SupportToolResult(False, summary + "\nFalhas: " + " | ".join(failures))
    return SupportToolResult(True, summary)


def clear_event_logs_after_backup() -> SupportToolResult:
    """Faz backup de Application/Setup e só então limpa esses dois logs; Security é preservado."""
    backup = backup_event_logs(("Application", "Setup"))
    if not backup.success:
        return SupportToolResult(False, "Limpeza abortada: o backup prévio falhou.", backup.message)
    cleared, failures = [], []
    for name in ("Application", "Setup"):
        result = _run(["wevtutil.exe", "cl", name], timeout=60)
        if result.success:
            cleared.append(name)
        else:
            failures.append(f"{name}: {result.message} {result.output}".strip())
    message = (
        f"Backup prévio realizado. Logs limpos: {', '.join(cleared) if cleared else 'nenhum'}. "
        "O log Security foi preservado."
    )
    if failures:
        return SupportToolResult(False, message + "\nFalhas: " + " | ".join(failures), backup.message)
    return SupportToolResult(True, message, backup.message)


def top_memory_processes() -> SupportToolResult:
    script = (
        "Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 15 "
        "Name, Id, CPU, @{N='MemoriaMB';E={[math]::Round($_.WorkingSet64/1MB,1)}} "
        "| Format-Table -AutoSize"
    )
    return _run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script], 30)


def close_process_gracefully(pid: int) -> SupportToolResult:
    """Solicita fechamento pela janela principal; nunca força a terminação."""
    if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
        raise ValueError("PID inválido.")
    script = (
        f"$p=Get-Process -Id {pid} -ErrorAction Stop; "
        "if(-not $p.MainWindowHandle -or -not $p.CloseMainWindow()){ "
        "Write-Output 'O processo não aceitou fechamento gracioso.'; exit 2 }; "
        "if($p.WaitForExit(5000)){ Write-Output 'Processo encerrado normalmente.' } "
        "else { Write-Output 'Solicitação enviada; processo continua em execução.'; exit 3 }"
    )
    return _run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script], 15)


class _HTTPSOnlyRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urllib.parse.urlparse(newurl)
        if parsed.scheme.lower() != "https" or parsed.username or parsed.password:
            raise urllib.error.HTTPError(newurl, code, "Redirecionamento não HTTPS bloqueado", headers, fp)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def download_https_file(url: str) -> SupportToolResult:
    """Baixa arquivo HTTPS para Downloads, limita tamanho e calcula SHA-256; não executa o arquivo."""
    parsed = urllib.parse.urlparse(url.strip())
    if (
        parsed.scheme.lower() != "https" or not parsed.hostname
        or parsed.username or parsed.password or parsed.port not in (None, 443)
    ):
        return SupportToolResult(False, "URL inválida: somente HTTPS na porta padrão é permitido.")
    raw_name = Path(urllib.parse.unquote(parsed.path)).name
    filename = re.sub(r"[^A-Za-z0-9._-]", "_", raw_name).strip("._")
    if not filename or filename in {".", ".."}:
        filename = "downloaded-file"
    destination_dir = Path.home() / "Downloads"
    temporary = None
    try:
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination = destination_dir / filename
        if destination.exists():
            stem, suffix = destination.stem, destination.suffix
            index = 1
            while (destination_dir / f"{stem}-{index}{suffix}").exists():
                index += 1
            destination = destination_dir / f"{stem}-{index}{suffix}"
        temporary = destination.with_name(destination.name + ".part")
        opener = urllib.request.build_opener(_HTTPSOnlyRedirect())
        request = urllib.request.Request(url.strip(), headers={"User-Agent": "NR-TECH-TECH-DESK/1.0"})
        digest = hashlib.sha256()
        total = 0
        with opener.open(request, timeout=20) as response, temporary.open("xb") as stream:
            if urllib.parse.urlparse(response.geturl()).scheme.lower() != "https":
                raise ValueError("O destino final não utiliza HTTPS.")
            declared = response.headers.get("Content-Length")
            if declared and int(declared) > MAX_DOWNLOAD_BYTES:
                raise ValueError("Arquivo excede o limite de 100 MiB.")
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_DOWNLOAD_BYTES:
                    raise ValueError("Download interrompido: limite de 100 MiB excedido.")
                stream.write(chunk)
                digest.update(chunk)
        if total == 0:
            raise ValueError("O servidor retornou um arquivo vazio.")
        temporary.replace(destination)
        return SupportToolResult(
            True,
            f"Download concluído: {destination}\nTamanho: {total} bytes\nSHA-256: {digest.hexdigest()}",
            "O arquivo foi apenas salvo. O TECH DESK não o executa."
        )
    except (OSError, ValueError, urllib.error.URLError, urllib.error.HTTPError) as exc:
        if temporary and temporary.exists():
            temporary.unlink(missing_ok=True)
        return SupportToolResult(False, f"Download não concluído: {exc}")
