from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class Settings:
    app_name: str = "TECH DESK"
    log_level: str = "INFO"
    data_dir: Path = Path.home() / ".techdesk"
    log_dir: Path = Path.home() / ".techdesk" / "logs"


def load_settings() -> Settings:
    data_dir = Path(
        os.getenv("TECHDESK_DATA_DIR", str(Settings.data_dir))
    ).expanduser()
    log_dir = Path(
        os.getenv("TECHDESK_LOG_DIR", str(data_dir / "logs"))
    ).expanduser()
    level = os.getenv("TECHDESK_LOG_LEVEL", "INFO").upper()

    if level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        level = "INFO"

    return Settings(log_level=level, data_dir=data_dir, log_dir=log_dir)
