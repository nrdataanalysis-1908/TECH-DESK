import argparse
import logging
import platform
import sys
from collections.abc import Callable

from techdesk import __version__
from techdesk.core.config import load_settings
from techdesk.core.diagnostics import (
    WINDOWS_DIAGNOSTICS,
    collect_diagnostics,
    run_windows_diagnostic,
)
from techdesk.core.logging_config import configure_logging


CYAN = "\033[96m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RESET = "\033[0m"

MENU_GROUPS = {
    "DIAGNÓSTICO DO SISTEMA": [
        ("1", "Resumo do sistema", "sistema"),
        ("2", "Processador e memória", "sistema"),
        ("3", "Armazenamento", "armazenamento"),
        ("4", "Tempo ligado (uptime)", "uptime"),
        ("5", "Variáveis de ambiente", "environment"),
    ],
    "REDE E CONECTIVIDADE": [
        ("6", "Configuração IP completa", "ipconfig"),
        ("7", "Servidores DNS", "dns"),
        ("8", "Gateway padrão", "gateway"),
        ("9", "Adaptadores de rede", "adapters"),
        ("10", "Conexões TCP ativas", "connections"),
        ("11", "Tabela de rotas", "routes"),
        ("12", "Tabela ARP", "arp"),
        ("13", "Teste de conectividade", "connectivity"),
    ],
    "HARDWARE E DISPOSITIVOS": [
        ("14", "Bateria", "battery"),
        ("15", "Dispositivos USB", "usb"),
        ("16", "Impressoras", "printers"),
    ],
    "PROCESSOS E SERVIÇOS": [
        ("17", "Processos em execução", "processes"),
        ("18", "Serviços do Windows", "services"),
        ("19", "Programas na inicialização", "startup"),
        ("20", "Tarefas agendadas", "tasks"),
    ],
    "SEGURANÇA E AUDITORIA": [
        ("21", "Status do Firewall", "firewall"),
        ("22", "Status do Microsoft Defender", "defender"),
        ("23", "Atualizações instaladas", "updates"),
        ("24", "Eventos críticos do sistema", "events"),
        ("25", "Contas locais", "users"),
        ("26", "Softwares instalados", "software"),
    ],
}


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


def _show_menu() -> None:
    print("\n" + _paint("╔══════════════════════════════════════════════════════╗", CYAN))
    print(_paint("║              TECH DESK  |  NR TECH                   ║", CYAN))
    print(_paint("║           IT MANAGEMENT & SUPPORT CENTER             ║", BLUE))
    print(_paint("╚══════════════════════════════════════════════════════╝", CYAN))
    for group, entries in MENU_GROUPS.items():
        print("\n" + _paint(group, BLUE))
        for number, label, _ in entries:
            print(f"  [{number:>2}] {label}")
    print("\n  [ 0] Sair")


def _menu(input_fn: Callable[[str], str] = input) -> int:
    actions = {
        number: (label, topic)
        for entries in MENU_GROUPS.values()
        for number, label, topic in entries
    }
    while True:
        _show_menu()
        try:
            choice = input_fn("\nSelecione uma opção: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nEncerrando TECH DESK.")
            return 0

        if choice == "0":
            print("TECH DESK encerrado.")
            return 0
        if choice not in actions:
            print(_paint("Opção inválida. Tente novamente.", YELLOW))
            continue

        label, topic = actions[choice]
        if topic in {"sistema", "armazenamento"}:
            report = collect_diagnostics()
            section = "sistema" if topic == "sistema" else "armazenamento"
            _show_section(label.upper(), report[section])
            if topic == "sistema" and choice == "2":
                _show_section("PROCESSADOR E MEMÓRIA", {
                    key: report["sistema"][key]
                    for key in ("processador", "nucleos_logicos", "memoria_total", "memoria_disponivel")
                })
        elif topic in WINDOWS_DIAGNOSTICS:
            print("\n" + _paint(label.upper(), BLUE))
            print("-" * 60)
            print(run_windows_diagnostic(topic))
        else:
            print(_paint("Diagnóstico não configurado.", YELLOW))


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
