from techdesk.core.support_tools import _safe_download_filename


def test_reserved_windows_device_names_are_prefixed():
    for name in ("CON.exe", "nul.txt", "COM1", "LPT9.zip"):
        assert _safe_download_filename(name).startswith("download_")


def test_ordinary_download_filename_is_stable():
    assert _safe_download_filename("driver-package.zip") == "driver-package.zip"
