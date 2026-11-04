from unittest.mock import patch

from techdesk.core.operations import (
    OPERATIONS,
    OperationResult,
    execute_operation,
    preview_temp_cleanup,
)


def test_operations_are_allowlisted():
    assert set(OPERATIONS) == {
        "flush_dns", "cleanup_temp", "restart_spooler", "sfc_scan", "dism_restore",
        "restart_explorer", "clear_print_queue", "create_restore_point", "check_disk",
        "renew_ip", "reset_winsock", "empty_recycle_bin", "restart_audio", "flush_arp",
        "quick_defender_scan", "update_defender_signatures", "restart_windows_update",
        "clear_thumbnail_cache",
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


def test_all_operations_have_a_dispatcher():
    with (
        patch("techdesk.core.operations.is_windows", return_value=True),
        patch("techdesk.core.operations.is_admin", return_value=True),
        patch("techdesk.core.operations._run", return_value=OperationResult(True, "ok")),
        patch("techdesk.core.operations._cleanup_temp", return_value=OperationResult(True, "ok")),
    ):
        for key in OPERATIONS:
            result = execute_operation(key, lambda _: True)
            assert result.success, key


def test_all_privileged_operations_are_blocked_without_elevation():
    privileged = [key for key, operation in OPERATIONS.items() if operation.requires_admin]
    with (
        patch("techdesk.core.operations.is_windows", return_value=True),
        patch("techdesk.core.operations.is_admin", return_value=False),
    ):
        for key in privileged:
            result = execute_operation(key, lambda _: True)
            assert not result.success, key
            assert "Administrador" in result.message, key


def test_output_encoding_uses_utf8_off_windows():
    with patch("techdesk.core.operations.is_windows", return_value=False):
        from techdesk.core.operations import _output_encoding

        assert _output_encoding() == "utf-8"


def test_temp_cleanup_preview_is_non_destructive():
    count, size = preview_temp_cleanup()
    assert count >= 0
    assert size >= 0


def test_operation_result_shape():
    result = OperationResult(True, "ok", "output")
    assert result.success
    assert result.message == "ok"
