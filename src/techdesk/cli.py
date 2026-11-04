import argparse
import collections.abc
import logging
import platform
import sys

from techdesk import __version__
from techdesk.core.config import load_settings
from techdesk.core.diagnostics import (
    WINDOWS_DIAGNOSTICS,
    collect_diagnostics,
    run_windows_diagnostic,
)
from techdesk.core.logging_config import configure_logging
from techdesk.core.operations import (
    OPERATIONS,
    execute_operation,
    preview_temp_cleanup,
)\n\nCYAN = "\033[96m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RESET = "\033[0m"

MENU_GROUPS = {
    "01  |  EXECUÇÃO E MANUTENÇÃO": [
        ("1", "Limpar cache DNS", "operation:flush_dns"),
        ("2", "Limpar arquivos temporários antigos", "operation:cleanup_temp"),
        ("3", "Esvaziar Lixeira", "operation:empty_recycle_bin"),
        ("4", "Reiniciar Windows Explorer", "operation:restart_explorer"),
        ("5", "Reconstruir cache de miniaturas", "operation:clear_thumbnail_cache"),
        ("6", "Renovar endereço IP (DHCP)", "operation:renew_ip"),
        ("7", "Limpar cache ARP", "operation:flush_arp"),
        ("8", "Reiniciar serviço de impressão", "operation:restart_spooler"),
        ("9", "Esvaziar fila de impressão", "operation:clear_print_queue"),
        ("10", "Reiniciar serviço de áudio", "operation:restart_audio"),
        ("11", "Atualizar assinaturas do Defender", "operation:update_defender_signatures"),
        ("12", "Executar verificação rápida do Defender", "operation:quick_defender_scan"),
        ("13", "Reiniciar serviço Windows Update", "operation:restart_windows_update"),
        ("14", "Criar ponto de restauração", "operation:create_restore_point"),
        ("15", "Verificar unidade do Windows (CHKDSK)", "operation:check_disk"),
        ("16", "Redefinir catálogo Winsock", "operation:reset_winsock"),
        ("17", "Verificar e reparar arquivos do Windows (SFC)", "operation:sfc_scan"),
        ("18", "Reparar imagem do Windows (DISM)", "operation:dism_restore"),
    ],
    "02  |  DIAGNÓSTICO DO SISTEMA": [
        ("19", "Resumo do sistema", "sistema"),
        ("20", "Processador e memória", "sistema"),
        ("21", "Armazenamento", "armazenamento"),
        ("22", "Tempo ligado (uptime)", "uptime"),
        ("23", "Processos em execução", "processes"),
        ("24", "Serviços do Windows", "services"),
    ],
    "03  |  REDE E CONECTIVIDADE": [
        ("25", "Configuração IP completa", "ipconfig"),
        ("26", "Servidores DNS", "dns"),
        ("27", "Adaptadores de rede", "adapters"),
        ("28", "Teste de conectividade", "connectivity"),
    ],
    "04  |  SEGURANÇA": [
        ("29", "Status do Firewall", "firewall"),
        ("30", "Status do Microsoft Defender", "defender"),
    ],
}


def _enable_ansi() -> bool:
    """Habilita sequências ANSI no console Windows moderno; falha de forma segura."""
    if not sys.stdout.isatty():
        return False
    if platform.system() != "Windows":
        return True
    try:
        import ctypes
        import msvcrt

        handle = msvcrt.get_osfhandle(sys.stdout.fileno())
        mode = ctypes.c_uint()
        kernel32 = ctypes.windll.kernel32
        if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            return False
        return bool(kernel32.SetConsoleMode(handle, mode.value | 0x0004))
    except (AttributeError, OSError, ValueError):
        return False


ANSI_ENABLED = _enable_ansi()


def _paint(value: str, color: str) -> str:
    return f"{color}{value}{RESET}" if ANSI_ENABLED else value


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
    parser.add_argument(
        "--diagnostic",
        choices=sorted(WINDOWS_DIAGNOSTICS),
        help="executa uma consulta Windows específica, somente para leitura",
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
    print("\n" + _paint("╔══════════════════════════════════════════════════════════════╗", CYAN))
    print(_paint("║                    TECH DESK  |  NR TECH                     ║", CYAN))
    print(_paint("║             IT MANAGEMENT & SUPPORT CENTER                   ║", BLUE))
    print(_paint("╚══════════════════════════════════════════════════════════════╝", CYAN))
    print("  [CONSULTA]  Somente leitura")
    print("  [EXECUÇÃO]  Altera o sistema após confirmação")
    print("  [ADMIN]     Exige privilégios elevados")
    for group, entries in MENU_GROUPS.items():
        print("\n" + _paint(group, BLUE))
        for number, label, topic in entries:
            if topic.startswith("operation:"):
                key = topic.split(":", 1)[1]
                tag = "ADMIN" if OPERATIONS[key].requires_admin else "EXECUÇÃO"
                color = YELLOW if tag == "ADMIN" else GREEN
            else:
                tag, color = "CONSULTA", CYAN
            print(f"  [{number:>2}] {label:<49} {_paint('[' + tag + ']', color)}")
    print("\n  [ 0] Encerrar TECH DESK")


def _menu(input_fn: collections.abc.Callable[[str], str] = input) -> int:
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
            if topic == "armazenamento":
                _show_section(label.upper(), report["armazenamento"])
            elif choice == "2":
                _show_section(label.upper(), {
                    key: report["sistema"][key]
                    for key in ("processador", "nucleos_logicos", "memoria_total", "memoria_disponivel")
                })
            else:
                _show_section(label.upper(), report["sistema"])
        elif topic.startswith("operation:"):
            operation_key = topic.split(":", 1)[1]
            operation = OPERATIONS[operation_key]
            print("\n" + "=" * 68)
            print(_paint(f" CENTRAL DE EXECUÇÃO | {operation.title.upper()}", BLUE))
            print("=" * 68)
            print(f" Ação             : {operation.title}")
            print(f" Nível de risco   : {operation.risk}")
            print(f" Privilégio       : {'Administrador' if operation.requires_admin else 'Usuário padrão'}")
            print(f" O que será feito : {operation.description}")
            if operation_key == "cleanup_temp":
                count, size = preview_temp_cleanup()
                print(f" Prévia           : {count} arquivo(s), {size / (1024**2):.2f} MiB elegíveis")
            print("-" * 68)
            print(" Para executar, digite SIM. Qualquer outra resposta cancela.")
            try:
                answer = input_fn(" Confirmação: ").strip().upper()
            except (EOFError, KeyboardInterrupt):
                print("\n Operação cancelada.", flush=True)
                continue

            if answer != "SIM":
                execute_operation(operation_key, confirm=lambda _: False)
                print(_paint("\n STATUS: CANCELADA — nenhuma ação foi executada.", YELLOW), flush=True)
                try:
                    input_fn("\nPressione ENTER para retornar ao menu...")
                except (EOFError, KeyboardInterrupt):
                    pass
                continue

            print("\n" + "=" * 68, flush=True)
            print(_paint(" EXECUTANDO OPERAÇÃO — NÃO FECHE ESTA JANELA", YELLOW), flush=True)
            print("=" * 68, flush=True)
            try:
                result = execute_operation(operation_key, confirm=lambda _: True)
            except Exception:
                logging.getLogger("techdesk").exception(
                    "Falha inesperada ao executar a operação %s", operation_key
                )
                print(_paint("\n STATUS: ERRO INTERNO — consulte o log do TECH DESK.", YELLOW), flush=True)
                try:
                    input_fn("\nPressione ENTER para retornar ao menu...")
                except (EOFError, KeyboardInterrupt):
                    pass
                continue

            print("\n" + "=" * 68)
            if result.success:
                print(_paint(" STATUS FINAL: EXECUÇÃO CONCLUÍDA", GREEN))
            else:
                print(_paint(" STATUS FINAL: FALHA NA EXECUÇÃO", YELLOW))
            print(f" Resultado: {result.message}")
            print("-" * 68)
            if result.output:
                print(" SAÍDA DO COMANDO:")
                print(result.output)
            else:
                print(" SAÍDA DO COMANDO: o Windows não retornou texto.")
            print("=" * 68, flush=True)
            try:
                input_fn("\nPressione ENTER para retornar ao menu...")
            except (EOFError, KeyboardInterrupt):
                pass
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
    if args.diagnostic:
        print(run_windows_diagnostic(args.diagnostic))
        return 0
    return _menu()


if __name__ == "__main__":
    raise SystemExit(main())
