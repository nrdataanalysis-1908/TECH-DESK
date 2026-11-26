"""System monitoring primitives for TECH-DESK."""

from techdesk.monitoring.collector import collect_snapshot
from techdesk.monitoring.models import (
    DiskMetric,
    NetworkMetric,
    ProcessMetric,
    SystemSnapshot,
    TemperatureMetric,
)

__all__ = [
    "DiskMetric",
    "NetworkMetric",
    "ProcessMetric",
    "SystemSnapshot",
    "TemperatureMetric",
    "collect_snapshot",
]
