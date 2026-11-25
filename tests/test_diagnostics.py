from unittest.mock import patch

from techdesk.core.diagnostics import (
    WINDOWS_DIAGNOSTICS,
    _format_bytes,
    collect_diagnostics,
    run_windows_diagnostic,
)


def test_format_bytes_handles_missing_value():
    assert _format_bytes(None) is None


def test_format_bytes_formats_gib():
    assert _format_bytes(1024**3) == "1.00 GiB"


def test_collect_diagnostics_returns_expected_sections():
    report = collect_diagnostics()
    assert set(report) == {"system", "network", "storage"}
    assert "operating_system" in report["system"]
    assert "ip_addresses" in report["network"]
    assert "used_percentage" in report["storage"]


def test_windows_catalog_contains_21_read_only_topics():
    assert len(WINDOWS_DIAGNOSTICS) >= 21
    assert "ipconfig" in WINDOWS_DIAGNOSTICS
    assert "defender" in WINDOWS_DIAGNOSTICS



def test_environment_diagnostic_lists_names_without_exposing_values():
    command = WINDOWS_DIAGNOSTICS["environment"]
    assert "Select-Object -ExpandProperty Name" in command
    assert "Format-Table -AutoSize" in command
    assert "Value" not in command


def test_unknown_diagnostic_is_rejected():
    try:
        run_windows_diagnostic("arbitrary-command")
    except ValueError as exc:
        assert "Unknown" in str(exc)
    else:
        raise AssertionError("Unknown diagnostics should be rejected.")


def test_non_windows_diagnostic_is_not_executed():
    with patch("techdesk.core.diagnostics.platform.system", return_value="Linux"):
        assert "available on Windows only" in run_windows_diagnostic("ipconfig")
