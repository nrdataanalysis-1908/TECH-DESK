from unittest.mock import patch

from techdesk.core.operations import (
    OPERATIONS,
    OperationResult,
    execute_operation,
    preview_temp_cleanup,
)


def test_operations_are_allowlisted():
    assert set(OPERATIONS) == {
        "flush_dns", "cleanup_temp", "restart_spooler", "sfc_scan", "dism_restore"
    }


def test_unknown_operation_is_rejected():
    try:
        execute_operation("run-anything", lambda _: True)
    except ValueError as exc:
        assert "não autorizada" in str(exc)
    else:
        raise AssertionError("Operação arbitrária deveria ser rejeitada.")


def test_cancelled_operation_does_not_run():
    with patch("techdesk.core.operations.is_windows", return_value=True):
        result = execute_operation("flush_dns", lambda _: False)
    assert not result.success
    assert "cancelada" in result.message


def test_non_windows_operation_does_not_run():
    with patch("techdesk.core.operations.is_windows", return_value=False):
        result = execute_operation("flush_dns", lambda _: True)
    assert not result.success
    assert "somente no Windows" in result.message


def test_admin_operation_is_blocked_without_elevation():
    with (
        patch("techdesk.core.operations.is_windows", return_value=True),
        patch("techdesk.core.operations.is_admin", return_value=False),
    ):
        result = execute_operation("sfc_scan", lambda _: True)
    assert not result.success
    assert "Administrador" in result.message


def test_temp_cleanup_preview_is_non_destructive():
    count, size = preview_temp_cleanup()
    assert count >= 0
    assert size >= 0


def test_operation_result_shape():
    result = OperationResult(True, "ok", "output")
    assert result.success
    assert result.message == "ok"
