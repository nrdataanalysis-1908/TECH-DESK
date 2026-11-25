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
        return SupportToolResult(False, f"Timed out ({timeout}s).")
    except OSError as exc:
        return SupportToolResult(False, f"Unable to start: {exc}")
    output = "\n".join(x.strip() for x in (result.stdout, result.stderr) if x.strip())
    if result.returncode == 0:
        return SupportToolResult(True, "Operation completed.", output[-12000:])
    return SupportToolResult(False, f"Exit code: {result.returncode}.", output[-12000:])


def open_windows_tool(key: str) -> SupportToolResult:
    """Opens only pre-authorized local tools."""
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
                "Speed test opened in the default browser."
            )
        except webbrowser.Error as exc:
            return SupportToolResult(False, f"Unable to open the browser: {exc}")
    if key not in commands:
        raise ValueError(f"Ferramenta not authorized: {key}")
    try:
        subprocess.Popen(commands[key], shell=False)
    except OSError as exc:
        return SupportToolResult(False, f"Unable to open the tool: {exc}")
    return SupportToolResult(True, "Windows tool started.")


def backup_event_logs(log_names: tuple[str, ...] = EVENT_LOGS) -> SupportToolResult:
    """Exports EVTX logs to a dated folder; never clears the records."""
    if not log_names or any(name not in EVENT_LOGS for name in log_names):
        raise ValueError("Unauthorized log set.")
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    destination = Path.home() / "Documents" / "NRTech" / "TechDesk" / "EventBackups" / stamp
    try:
        destination.mkdir(parents=True, exist_ok=False)
    except OSError as exc:
        return SupportToolResult(False, f"Unable to create backup directory: {exc}")
    exported, failures = [], []
    for name in log_names:
        target = destination / f"{name}.evtx"
        result = _run(["wevtutil.exe", "epl", name, str(target)], timeout=120)
        if result.success and target.exists() and target.stat().st_size > 0:
            exported.append(name)
        else:
            failures.append(f"{name}: {result.message} {result.output}".strip())
    summary = f"Backups exported: {', '.join(exported) if exported else 'none'}. Pasta: {destination}"
    if failures:
        return SupportToolResult(False, summary + "\nFailures: " + " | ".join(failures))
    return SupportToolResult(True, summary)


def clear_event_logs_after_backup() -> SupportToolResult:
    """Backs up Application/Setup before clearing those two logs; Security is preserved."""
    backup = backup_event_logs(("Application", "Setup"))
    if not backup.success:
        return SupportToolResult(False, "Cleanup aborted: the backup failed.", backup.message)
    cleared, failures = [], []
    for name in ("Application", "Setup"):
        result = _run(["wevtutil.exe", "cl", name], timeout=60)
        if result.success:
            cleared.append(name)
        else:
            failures.append(f"{name}: {result.message} {result.output}".strip())
    message = (
        f"Backup completed. Cleared logs: {', '.join(cleared) if cleared else 'none'}. "
        "The Security log was preserved."
    )
    if failures:
        return SupportToolResult(False, message + "\nFailures: " + " | ".join(failures), backup.message)
    return SupportToolResult(True, message, backup.message)


def top_memory_processes() -> SupportToolResult:
    script = (
        "Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 15 "
        "Name, Id, CPU, @{N='MemoryMB';E={[math]::Round($_.WorkingSet64/1MB,1)}} "
        "| Format-Table -AutoSize"
    )
    return _run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script], 30)


def close_process_gracefully(pid: int) -> SupportToolResult:
    """Solicita fechamento pela janela principal; nunca força a terminação."""
    if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
        raise ValueError("Invalid PID.")
    script = (
        f"$p=Get-Process -Id {pid} -ErrorAction Stop; "
        "if(-not $p.MainWindowHandle -or -not $p.CloseMainWindow()){ "
        "Write-Output 'The process did not accept a graceful shutdown.'; exit 2 }; "
        "if($p.WaitForExit(5000)){ Write-Output 'Process exited normally.' } "
        "else { Write-Output 'Request sent; process is still running.'; exit 3 }"
    )
    return _run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script], 15)


class _HTTPSOnlyRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        try:
            _parse_https_url(newurl)
        except ValueError as exc:
            raise urllib.error.HTTPError(
                newurl, code, "Invalid HTTPS redirect destination", headers, fp
            ) from exc
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _parse_https_url(url: str) -> urllib.parse.ParseResult:
    """Validate an HTTPS URL before opening a network connection."""
    if (
        not isinstance(url, str) or not url or url != url.strip()
        or any(ord(character) < 0x20 or ord(character) == 0x7F for character in url)
    ):
        raise ValueError("URL must be an HTTPS string without surrounding whitespace or control characters.")
    try:
        parsed = urllib.parse.urlparse(url)
        port = parsed.port
    except ValueError as exc:
        raise ValueError("HTTPS URL contains an invalid authority or port.") from exc
    if (
        parsed.scheme.lower() != "https" or not parsed.hostname
        or parsed.username is not None or parsed.password is not None
        or port not in (None, 443)
    ):
        raise ValueError("Only HTTPS on the default port without credentials is allowed.")
    return parsed


_WINDOWS_RESERVED_BASENAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{number}" for number in range(1, 10)),
    *(f"LPT{number}" for number in range(1, 10)),
    "COM¹", "COM²", "COM³", "LPT¹", "LPT²", "LPT³",
}


def _safe_download_filename(raw_name: str) -> str:
    filename = re.sub(r"[^A-Za-z0-9._-]", "_", raw_name).strip("._")
    if not filename:
        filename = "downloaded-file"
    if filename.split(".", 1)[0].upper() in _WINDOWS_RESERVED_BASENAMES:
        filename = f"download_{filename}"
    return filename[:180]


def download_https_file(url: str) -> SupportToolResult:
    """Downloads an HTTPS file to Downloads, enforces a size limit, and calculates SHA-256; never executes the file."""
    try:
        parsed = _parse_https_url(url)
    except ValueError as exc:
        return SupportToolResult(False, f"Invalid URL: {exc}")
    raw_name = Path(urllib.parse.unquote(parsed.path)).name
    filename = _safe_download_filename(raw_name)
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
            _parse_https_url(response.geturl())
            declared = response.headers.get("Content-Length")
            if declared is not None:
                if not declared.strip().isdigit():
                    raise ValueError("Server returned an invalid Content-Length.")
                if int(declared) > MAX_DOWNLOAD_BYTES:
                    raise ValueError("File exceeds the 100 MiB limit.")
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_DOWNLOAD_BYTES:
                    raise ValueError("Download aborted: 100 MiB limit exceeded.")
                stream.write(chunk)
                digest.update(chunk)
        if declared is not None and total != int(declared):
            raise ValueError(
                f"Content-Length mismatch: expected {int(declared)} bytes, received {total}."
            )
        if total == 0:
            raise ValueError("The server returned an empty file.")
        temporary.replace(destination)
        return SupportToolResult(
            True,
            f"Download completed: {destination}\nSize: {total} bytes\nSHA-256: {digest.hexdigest()}",
            "The file was saved only. TECH DESK does not execute it."
        )
    except (OSError, ValueError, urllib.error.URLError, urllib.error.HTTPError) as exc:
        if temporary and temporary.exists():
            temporary.unlink(missing_ok=True)
        return SupportToolResult(False, f"Download failed: {exc}")
