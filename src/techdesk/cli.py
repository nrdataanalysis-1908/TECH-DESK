import argparse
import logging
import platform

from techdesk import __version__
from techdesk.core.config import load_settings
from techdesk.core.logging_config import configure_logging


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="techdesk",
        description="TECH DESK | NR TECH — IT Management & Support Center",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main() -> int:
    build_parser().parse_args()
    settings = load_settings()
    configure_logging(settings)
    logging.getLogger("techdesk").info("TECH DESK iniciado")

    print("\nTECH DESK | NR TECH")
    print("IT MANAGEMENT & SUPPORT CENTER")
    print("=" * 46)
    print(f"Sistema : {platform.system()} {platform.release()}")
    print(f"Python  : {platform.python_version()}")
    print(f"Logs    : {settings.log_dir}")
    print("\nFundação carregada. Módulos administrativos ainda não habilitados.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
