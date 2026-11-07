from unittest.mock import patch

from techdesk.core import maintenance


def test_clear_recycle_bin_uses_native_command_and_reports_failure():
    with patch(
        "techdesk.core.maintenance._run_powershell",
        return_value=maintenance.OperationResult(False, "failed", "file not found"),
    ) as run:
        result = maintenance.clear_recycle_bin()

    assert not result.success
    assert "Nenhum metadado interno" in result.message
    assert "Clear-RecycleBin" in run.call_args.args[0]


def test_run_maintenance_records_partial_failure():
    with (
        patch(
            "techdesk.core.maintenance._cleanup_temp",
            return_value=maintenance.OperationResult(True, "TEMP ok"),
        ),
        patch(
            "techdesk.core.maintenance.clear_recycle_bin",
            return_value=maintenance.OperationResult(False, "Recycle Bin warning"),
        ),
        patch("techdesk.core.maintenance._write_log") as log,
    ):
        result = maintenance.run_maintenance()

    assert not result.success
    assert "TEMP ok" in result.message
    assert "Recycle Bin warning" in result.message
    assert log.call_count == 2


def test_install_schedule_is_idempotent_and_uses_expected_hours():
    with patch(
        "techdesk.core.maintenance._run_powershell",
        return_value=maintenance.OperationResult(True, "registered"),
    ) as run:
        result = maintenance.install_schedule()

    assert result.success
    script = run.call_args.args[0]
    assert "Register-ScheduledTask" in script
    assert "@(8, 18)" in script
    assert "-Force" in script


def test_task_names_are_stable():
    assert maintenance.TASK_NAMES == (
        "TECH DESK - Limpeza diaria 8h",
        "TECH DESK - Limpeza diaria 18h",
    )
