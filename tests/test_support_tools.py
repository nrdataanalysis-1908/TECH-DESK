import urllib.error
from unittest.mock import patch

import pytest

from techdesk.core.support_tools import (
    SupportToolResult,
    _HTTPSOnlyRedirect,
    clear_event_logs_after_backup,
    close_process_gracefully,
    download_https_file,
    open_windows_tool,
)


def test_download_rejects_non_https_without_network():
    result = download_https_file("http://example.com/file.zip")
    assert not result.success
    assert "somente HTTPS" in result.message

def test_download_rejects_credentials_and_nonstandard_port():
    assert not download_https_file("https://user:pass@example.com/file").success
    assert not download_https_file("https://example.com:8443/file").success

@pytest.mark.parametrize("pid", [0, -1, True, "123", None])
def test_close_process_rejects_invalid_pid(pid):
    with pytest.raises(ValueError):
        close_process_gracefully(pid)

def test_unknown_windows_tool_is_rejected():
    with pytest.raises(ValueError):
        open_windows_tool("arbitrary-command")

def test_event_logs_are_not_cleared_when_backup_fails():
    with patch("techdesk.core.support_tools.backup_event_logs", return_value=SupportToolResult(False, "backup failed")), patch("techdesk.core.support_tools._run") as run:
        result = clear_event_logs_after_backup()
    assert not result.success
    assert "abortada" in result.message
    run.assert_not_called()

def test_event_log_cleanup_only_targets_application_and_setup_after_backup():
    with patch("techdesk.core.support_tools.backup_event_logs", return_value=SupportToolResult(True, "backup ok")), patch("techdesk.core.support_tools._run", return_value=SupportToolResult(True, "ok")) as run:
        result = clear_event_logs_after_backup()
    assert result.success
    assert [call.args[0] for call in run.call_args_list] == [
        ["wevtutil.exe", "cl", "Application"],
        ["wevtutil.exe", "cl", "Setup"],
    ]
    assert "Security" in result.message

def test_https_redirect_handler_rejects_downgrade():
    handler = _HTTPSOnlyRedirect()
    with pytest.raises(urllib.error.HTTPError):
        handler.redirect_request(None, None, 302, "Found", {}, "http://example.com/file")
