from techdesk.core.config import load_settings


def test_invalid_log_level_falls_back_to_info(monkeypatch):
    monkeypatch.setenv("TECHDESK_LOG_LEVEL", "INVALID")
    assert load_settings().log_level == "INFO"


def test_custom_data_directory_is_respected(monkeypatch, tmp_path):
    monkeypatch.setenv("TECHDESK_DATA_DIR", str(tmp_path))
    settings = load_settings()
    assert settings.data_dir == tmp_path
    assert settings.log_dir == tmp_path / "logs"
