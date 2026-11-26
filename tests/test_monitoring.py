from datetime import UTC
from types import SimpleNamespace

import pytest

from techdesk.monitoring.collector import (
    MonitoringDependencyError,
    collect_snapshot,
)


class FakeProcess:
    def __init__(self, pid, name, rss, cpu):
        self.info = {
            "pid": pid,
            "name": name,
            "memory_info": SimpleNamespace(rss=rss),
        }
        self._cpu = cpu

    def cpu_percent(self, interval=None):
        return self._cpu


def fake_psutil(monkeypatch):
    import sys

    fake = SimpleNamespace(
        virtual_memory=lambda: SimpleNamespace(
            total=16_000, available=6_000, used=10_000, percent=62.5
        ),
        cpu_freq=lambda: SimpleNamespace(current=2400.0),
        disk_partitions=lambda all=False: [
            SimpleNamespace(device="C:", mountpoint="C:\\", fstype="NTFS")
        ],
        disk_usage=lambda mount: SimpleNamespace(
            total=100_000, used=40_000, free=60_000, percent=40.0
        ),
        net_io_counters=lambda: SimpleNamespace(
            bytes_sent=100, bytes_recv=200, packets_sent=10, packets_recv=20,
            errin=0, errout=1, dropin=0, dropout=0,
        ),
        process_iter=lambda attrs, ad_value=None: [
            FakeProcess(11, "large.exe", 900, 2.0),
            FakeProcess(12, "small.exe", 100, 1.0),
        ],
        cpu_percent=lambda interval=None: 37.5,
        cpu_count=lambda logical=True: 8,
        sensors_temperatures=lambda fahrenheit=False: {},
        NoSuchProcess=type("NoSuchProcess", (Exception,), {}),
        AccessDenied=type("AccessDenied", (Exception,), {}),
        ZombieProcess=type("ZombieProcess", (Exception,), {}),
    )
    monkeypatch.setitem(sys.modules, "psutil", fake)


def test_collect_snapshot_returns_typed_metrics(monkeypatch):
    fake_psutil(monkeypatch)
    snapshot = collect_snapshot()

    assert snapshot.cpu_percent == 37.5
    assert snapshot.logical_cpu_count == 8
    assert snapshot.memory_percent == 62.5
    assert snapshot.disks[0].mountpoint == "C:\\"
    assert snapshot.network.bytes_received == 200
    assert snapshot.top_processes[0].name == "large.exe"
    assert snapshot.temperature_status.startswith("unavailable:")
    assert snapshot.captured_at.tzinfo == UTC


def test_collect_snapshot_limits_processes(monkeypatch):
    fake_psutil(monkeypatch)
    snapshot = collect_snapshot(top_process_limit=1)
    assert len(snapshot.top_processes) == 1
    assert snapshot.top_processes[0].pid == 11


def test_collect_snapshot_can_skip_process_enumeration(monkeypatch):
    fake_psutil(monkeypatch)
    snapshot = collect_snapshot(top_process_limit=0)
    assert snapshot.top_processes == ()


def test_collect_snapshot_rejects_negative_process_limit():
    with pytest.raises(ValueError, match="zero or greater"):
        collect_snapshot(top_process_limit=-1)


def test_missing_optional_dependency_has_actionable_error(monkeypatch):
    import sys

    monkeypatch.delitem(sys.modules, "psutil", raising=False)
    monkeypatch.setattr("builtins.__import__", lambda name, *args, **kwargs: (_ for _ in ()).throw(ImportError()) if name == "psutil" else __import__(name, *args, **kwargs))
    with pytest.raises(MonitoringDependencyError, match="tech-desk\[monitoring\]"):
        collect_snapshot()
