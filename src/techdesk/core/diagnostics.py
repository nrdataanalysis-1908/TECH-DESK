"""Coleta local de informações de endpoint; todas as rotinas são somente leitura."""

import os
import platform
import shutil
import socket
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
