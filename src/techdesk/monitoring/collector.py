"""Non-destructive endpoint metrics collection using psutil."""

from __future__ import annotations

import platform
import socket
from datetime import UTC, datetime

from techdesk.monitoring.models import (
    DiskMetric,
    NetworkMetric,
    ProcessMetric,
    SystemSnapshot,
    TemperatureMetric,
)


class MonitoringDependencyError(RuntimeError):
    """Raised when the optional monitoring dependency is not installed."""


def collect_snapshot(top_process_limit: int = 10) -> SystemSnapshot:
    """Collect one local metrics snapshot without changing system state.

    The first CPU percentages reported by psutil can be zero because psutil needs
    an initial sample. Temperature readings are optional and explicitly marked
    unavailable when the operating system or hardware does not expose sensors.
    """
    if top_process_limit < 0:
        raise ValueError("top_process_limit must be zero or greater")

    try:
        import psutil
    except ImportError as exc:
        raise MonitoringDependencyError(
            "System monitoring requires the optional dependency: pip install 'tech-desk[monitoring]'"
        ) from exc

    virtual_memory = psutil.virtual_memory()
    cpu_frequency = psutil.cpu_freq()
    disks: list[DiskMetric] = []
    seen_mountpoints: set[str] = set()

    try:
        partitions = psutil.disk_partitions(all=False)
    except (OSError, PermissionError):
        partitions = []

    for partition in partitions:
        mountpoint = str(partition.mountpoint)
        if mountpoint in seen_mountpoints:
            continue
        seen_mountpoints.add(mountpoint)
        try:
            usage = psutil.disk_usage(mountpoint)
        except (OSError, PermissionError):
            continue
        disks.append(
            DiskMetric(
                device=str(partition.device),
                mountpoint=mountpoint,
                filesystem=str(partition.fstype),
                total_bytes=int(usage.total),
                used_bytes=int(usage.used),
                free_bytes=int(usage.free),
                percent_used=float(usage.percent),
            )
        )

    counters = psutil.net_io_counters()
    network = None
    if counters is not None:
        network = NetworkMetric(
            bytes_sent=int(counters.bytes_sent),
            bytes_received=int(counters.bytes_recv),
            packets_sent=int(counters.packets_sent),
            packets_received=int(counters.packets_recv),
            errors_in=int(counters.errin),
            errors_out=int(counters.errout),
            drops_in=int(counters.dropin),
            drops_out=int(counters.dropout),
        )

    processes: list[ProcessMetric] = []
    if top_process_limit:
        for process in psutil.process_iter(
            attrs=["pid", "name", "memory_info"],
            ad_value=None,
        ):
            try:
                info = process.info
                memory_info = info.get("memory_info")
                if not info.get("pid") or memory_info is None:
                    continue
                processes.append(
                    ProcessMetric(
                        pid=int(info["pid"]),
                        name=str(info.get("name") or "Unknown process"),
                        cpu_percent=float(process.cpu_percent(interval=None)),
                        memory_rss_bytes=int(memory_info.rss),
                    )
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        processes.sort(key=lambda item: item.memory_rss_bytes, reverse=True)

    temperatures: list[TemperatureMetric] = []
    temperature_status = "unavailable: sensor readings are not exposed by this platform"
    sensor_reader = getattr(psutil, "sensors_temperatures", None)
    if callable(sensor_reader):
        try:
            sensor_groups = sensor_reader(fahrenheit=False) or {}
            for sensor_name, entries in sensor_groups.items():
                for entry in entries:
                    current = getattr(entry, "current", None)
                    if current is None:
                        continue
                    temperatures.append(
                        TemperatureMetric(
                            sensor=str(sensor_name),
                            label=str(getattr(entry, "label", "") or sensor_name),
                            celsius=float(current),
                        )
                    )
            temperature_status = "available" if temperatures else temperature_status
        except (NotImplementedError, OSError, PermissionError):
            pass

    return SystemSnapshot(
        captured_at=datetime.now(UTC),
        hostname=socket.gethostname(),
        operating_system=platform.system(),
        platform_release=platform.release(),
        architecture=platform.machine(),
        cpu_percent=float(psutil.cpu_percent(interval=None)),
        logical_cpu_count=int(psutil.cpu_count(logical=True) or 0),
        cpu_frequency_mhz=(float(cpu_frequency.current) if cpu_frequency else None),
        memory_total_bytes=int(virtual_memory.total),
        memory_available_bytes=int(virtual_memory.available),
        memory_used_bytes=int(virtual_memory.used),
        memory_percent=float(virtual_memory.percent),
        disks=tuple(disks),
        network=network,
        top_processes=tuple(processes[:top_process_limit]),
        temperatures=tuple(temperatures),
        temperature_status=temperature_status,
    )
