"""Typed, serializable data models for endpoint telemetry."""

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class DiskMetric:
    device: str
    mountpoint: str
    filesystem: str
    total_bytes: int
    used_bytes: int
    free_bytes: int
    percent_used: float


@dataclass(frozen=True)
class NetworkMetric:
    bytes_sent: int
    bytes_received: int
    packets_sent: int
    packets_received: int
    errors_in: int
    errors_out: int
    drops_in: int
    drops_out: int


@dataclass(frozen=True)
class ProcessMetric:
    pid: int
    name: str
    cpu_percent: float
    memory_rss_bytes: int


@dataclass(frozen=True)
class TemperatureMetric:
    sensor: str
    label: str
    celsius: float


@dataclass(frozen=True)
class SystemSnapshot:
    captured_at: datetime
    hostname: str
    operating_system: str
    platform_release: str
    architecture: str
    cpu_percent: float
    logical_cpu_count: int
    cpu_frequency_mhz: float | None
    memory_total_bytes: int
    memory_available_bytes: int
    memory_used_bytes: int
    memory_percent: float
    disks: tuple[DiskMetric, ...]
    network: NetworkMetric | None
    top_processes: tuple[ProcessMetric, ...]
    temperatures: tuple[TemperatureMetric, ...]
    temperature_status: str

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation with ISO-8601 timestamps."""
        result = asdict(self)
        result["captured_at"] = self.captured_at.isoformat()
        return result
