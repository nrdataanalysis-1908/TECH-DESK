import argparse
import logging
import platform
import sys
from collections.abc import Callable

from techdesk import __version__
from techdesk.core.config import load_settings
from techdesk.core.diagnostics import collect_diagnostics
from techdesk.core.logging_config import configure_logging


CYAN = "\033[96m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def _paint(value: str, color: str) -> str:
    return f"{color}{value}{RESET}" if sys.stdout.isatty() else value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="techdesk",
        description="TECH DESK | NR TECH — IT Management & Support Center",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--diagnostics",
        action="store_true",
        help="coleta e exibe diagnóstico local somente para leitura",
    )
    return parser


def _show_section(title: str, values: dict[str, object]) -> None:
    print("\n" + _paint(title, BLUE))
    print("-" * 48)
    for label, value in values.items():
        print(f"  {label:<22}: {value if value is not None else 'Não disponível'}")


def _show_diagnostics() -> None:
    report = collect_diagnostics()
    for section, values in report.items():
        _show_section(section.upper(), values)


def _menu(input_fn: Callable[[str], str] = input) -> int:
    while True:
        print("\n" + _paint("╔══════════════════════════════════════════════╗", CYAN))
        print(_paint("║          TECH DESK  |  NR TECH               ║", CYAN))
        print(_paint("║       IT MANAGEMENT & SUPPORT CENTER         ║", BLUE))
        print(_paint("╚══════════════════════════════════════════════╝", CYAN))
        print("  [1] Diagnóstico do sistema")
        print("  [2] Diagnóstico de rede")
        print("  [3] Informações de armazenamento")
        print("  [0] Sair")
        try:
            choice = input_fn("\nSelecione uma opção: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nEncerrando TECH DESK.")
            return 0

        if choice == "1":
            _show_section("SISTEMA", collect_diagnostics()["sistema"])
        elif choice == "2":
            _show_section("REDE", collect_diagnostics()["rede"])
        elif choice == "3":
            _show_section("ARMAZENAMENTO", collect_diagnostics()["armazenamento"])
        elif choice == "0":
            print("TECH DESK encerrado.")
            return 0
        else:
            print(_paint("Opção inválida. Tente novamente.", YELLOW))


def main() -> int:
    args = build_parser().parse_args()
    settings = load_settings()
    configure_logging(settings)
    logging.getLogger("techdesk").info("TECH DESK iniciado")

    print(f"TECH DESK | NR TECH — {platform.system()} {platform.release()}")
    if args.diagnostics:
        _show_diagnostics()
        return 0
    return _menu()


if __name__ == "__main__":
    raise SystemExit(main())
