"""Diagnósticos locais somente para leitura e consultas fixas ao Windows."""

import os
import platform
import shutil
import socket
import subprocess
from pathlib import Path
from typing import Any


def _memory_bytes() -> tuple[int | None, int | None]:
    """Retorna memória total e disponível em bytes, sem dependências externas."""
    if platform.system() == "Windows":
        try:
            import ctypes

            class MemoryStatus(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            status = MemoryStatus()
            status.dwLength = ctypes.sizeof(MemoryStatus)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                return int(status.ullTotalPhys), int(status.ullAvailPhys)
        except (AttributeError, OSError):
            return None, None

    meminfo = Path("/proc/meminfo")
    if meminfo.exists():
        try:
            values: dict[str, int] = {}
            for line in meminfo.read_text(encoding="utf-8").splitlines():
                key, raw = line.split(":", 1)
                values[key] = int(raw.strip().split()[0]) * 1024
            return values.get("MemTotal"), values.get("MemAvailable")
        except (OSError, ValueError, IndexError):
            return None, None
    return None, None


def _format_bytes(value: int | None) -> str | None:
    if value is None:
        return None
    return f"{value / (1024**3):.2f} GiB"


def _network_addresses() -> str:
    hostname = socket.gethostname()
    try:
        addresses = sorted(
            {
                item[4][0]
                for item in socket.getaddrinfo(hostname, None)
                if item[4] and not item[4][0].startswith("127.")
            }
        )
        return ", ".join(addresses) if addresses else "Nenhum IP não-loopback identificado"
    except socket.gaierror:
        return "Não foi possível resolver os endereços locais"


def collect_diagnostics() -> dict[str, dict[str, Any]]:
    """Monta um relatório básico sem alterar configurações do endpoint."""
    total_memory, available_memory = _memory_bytes()
    disk = shutil.disk_usage(Path.home())

    return {
        "sistema": {
            "sistema_operacional": platform.system(),
            "versao": platform.version(),
            "release": platform.release(),
            "arquitetura": platform.machine(),
            "processador": platform.processor() or "Não identificado",
            "nucleos_logicos": os.cpu_count(),
            "memoria_total": _format_bytes(total_memory),
            "memoria_disponivel": _format_bytes(available_memory),
            "hostname": socket.gethostname(),
            "python": platform.python_version(),
        },
        "rede": {
            "hostname": socket.gethostname(),
            "enderecos_ip": _network_addresses(),
        },
        "armazenamento": {
            "unidade_analisada": str(Path.home()),
            "total": _format_bytes(disk.total),
            "utilizado": _format_bytes(disk.used),
            "livre": _format_bytes(disk.free),
            "percentual_utilizado": (
                f"{(disk.used / disk.total) * 100:.1f}%" if disk.total else None
            ),
        },
    }


# Scripts constantes: nenhuma entrada do usuário é interpolada ou executada.
WINDOWS_DIAGNOSTICS: dict[str, str] = {
    "ipconfig": "ipconfig /all",
    "dns": "Get-DnsClientServerAddress | Format-Table -AutoSize",
    "gateway": "Get-NetRoute -DestinationPrefix '0.0.0.0/0' | Format-Table -AutoSize",
    "adapters": "Get-NetAdapter | Format-Table Name, InterfaceDescription, Status, LinkSpeed -AutoSize",
    "connections": "Get-NetTCPConnection -State Established -ErrorAction SilentlyContinue | Select-Object -First 40 | Format-Table -AutoSize",
    "routes": "route.exe print",
    "arp": "arp.exe -a",
    "connectivity": "Test-NetConnection -ComputerName 1.1.1.1 -Port 443 -InformationLevel Detailed | Format-List",
    "processes": "Get-Process | Sort-Object CPU -Descending | Select-Object -First 20 Name, Id, CPU, WorkingSet64 | Format-Table -AutoSize",
    "services": "Get-Service | Sort-Object Status, DisplayName | Select-Object -First 60 Status, Name, DisplayName | Format-Table -AutoSize",
    "startup": "Get-CimInstance Win32_StartupCommand | Select-Object Name, Location, User | Format-Table -AutoSize",
    "software": "Get-ItemProperty 'HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*','HKLM:\\Software\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*' -ErrorAction SilentlyContinue | Where-Object DisplayName | Select-Object -First 80 DisplayName, DisplayVersion, Publisher | Sort-Object DisplayName | Format-Table -AutoSize",
    "tasks": "Get-ScheduledTask | Select-Object -First 60 TaskName, TaskPath, State | Format-Table -AutoSize",
    "firewall": "Get-NetFirewallProfile | Format-Table Name, Enabled, DefaultInboundAction, DefaultOutboundAction -AutoSize",
    "defender": "Get-MpComputerStatus | Select-Object AntivirusEnabled, RealTimeProtectionEnabled, AntivirusSignatureLastUpdated, AMServiceEnabled | Format-List",
    "updates": "Get-HotFix | Sort-Object InstalledOn -Descending | Select-Object -First 25 HotFixID, Description, InstalledOn | Format-Table -AutoSize",
    "events": "Get-WinEvent -FilterHashtable @{LogName='System'; Level=2} -MaxEvents 20 -ErrorAction SilentlyContinue | Select-Object TimeCreated, Id, ProviderName, Message | Format-List",
    "battery": "Get-CimInstance Win32_Battery -ErrorAction SilentlyContinue | Format-List Name, Status, EstimatedChargeRemaining, BatteryStatus",
    "usb": "Get-PnpDevice -PresentOnly -ErrorAction SilentlyContinue | Where-Object InstanceId -Like 'USB*' | Select-Object -First 40 Status, Class, FriendlyName | Format-Table -AutoSize",
    "printers": "Get-Printer -ErrorAction SilentlyContinue | Format-Table Name, DriverName, PrinterStatus, Shared -AutoSize",
    "environment": "Get-ChildItem Env: | Sort-Object Name | Format-Table -AutoSize",
    "uptime": "Get-CimInstance Win32_OperatingSystem | Select-Object CSName, LastBootUpTime, LocalDateTime | Format-List",
    "users": "Get-LocalUser | Select-Object Name, Enabled, LastLogon, PasswordRequired | Format-Table -AutoSize",
}


def run_windows_diagnostic(topic: str) -> str:
    """Executa uma consulta PowerShell predefinida, somente leitura e com timeout."""
    if topic not in WINDOWS_DIAGNOSTICS:
        raise ValueError(f"Diagnóstico desconhecido: {topic}")
    if platform.system() != "Windows":
        return "Este diagnóstico está disponível somente no Windows."

    command = [
        "powershell.exe",
        "-NoLogo",
        "-NoProfile",
        "-NonInteractive",
        "-Command",
        "$ErrorActionPreference = 'Continue'; " + WINDOWS_DIAGNOSTICS[topic],
    ]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=25,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"Falha ao executar diagnóstico: {exc}"

    output = (result.stdout or "").strip()
    errors = (result.stderr or "").strip()
    if output and errors:
        output += f"\n\nAvisos: {errors}"
    elif errors and not output:
        output = errors
    if not output:
        output = "Nenhum dado retornado."
    return output[:16000]
