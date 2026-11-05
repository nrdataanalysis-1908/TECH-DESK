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
)
from techdesk.core.support_tools import (
    close_process_gracefully,
    download_https_file,
    open_windows_tool,
    top_memory_processes,
)

CYAN = "\033[96m"
BLUE = "\033[94m"
YELLOW = BLUE
GREEN = CYAN
RESET = "\033[0m"

MENU_GROUPS = {
    "01  |  PAINEL DE SUPORTE TÉCNICO": [
        ("1", "Limpeza de arquivos temporários", "operation:cleanup_temp"),
        ("2", "Executar Limpeza de Disco (cleanmgr)", "tool:disk_cleanup"),
        ("3", "Verificação de arquivos do sistema (SFC)", "operation:sfc_scan"),
        ("4", "Reparo da imagem do Windows (DISM)", "operation:dism_restore"),
        ("5", "Reiniciar serviço do Windows Update", "operation:restart_windows_update"),
        ("6", "Redefinir catálogo de rede (Winsock)", "operation:reset_winsock"),
        ("7", "Atualizar políticas de grupo (GPO)", "operation:update_group_policy"),
        ("8", "Limpeza seletiva de logs de eventos", "operation:clear_event_logs"),
        ("9", "Informações do sistema (msinfo32)", "tool:system_info"),
        ("10", "Gerenciador de Dispositivos", "tool:device_manager"),
        ("11", "Ver adaptadores de rede", "adapters"),
        ("12", "Atualizar programas instalados via Winget", "operation:winget_upgrade_all"),
        ("13", "Ver processos em execução", "processes"),
        ("14", "Ver status dos principais serviços", "services"),
    ],
    "02  |  CONSULTAS COMPLEMENTARES": [
        ("15", "Resumo e diagnóstico do sistema", "sistema"),
        ("16", "Armazenamento e espaço em disco", "armazenamento"),
        ("17", "Configuração IP completa", "ipconfig"),
        ("18", "Servidores DNS", "dns"),
        ("19", "Teste de conectividade", "connectivity"),
        ("20", "Status do Firewall", "firewall"),
        ("21", "Status do Microsoft Defender", "defender"),
        ("22", "Verificar atualizações disponíveis (Winget)", "winget"),
        ("23", "Inventário de softwares instalados", "software"),
        ("24", "Eventos críticos e erros do Windows", "events"),
        ("25", "Inventário de dispositivos USB", "usb"),
        ("26", "Processos com maior consumo de memória", "memory_processes"),
        ("27", "Uso de CPU e memória em tempo real", "performance"),
    ],
    "03  |  FERRAMENTAS ADICIONAIS": [
        ("28", "Exportar logs de eventos (EVTX)", "operation:backup_event_logs"),
        ("29", "Abrir PowerShell", "tool:powershell"),
        ("30", "Teste de velocidade da internet", "tool:speedtest"),
        ("31", "Baixar arquivo por HTTPS (sem executar)", "download_https"),
        ("32", "Solicitar fechamento gracioso de processo", "close_process"),
        ("33", "Otimizador de Memória (submenu)", "memory_optimizer"),
        ("34", "Reiniciar Windows Explorer", "operation:restart_explorer"),
        ("35", "Esvaziar Lixeira", "operation:empty_recycle_bin"),
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


def _pause_before_menu(input_fn: collections.abc.Callable[[str], str]) -> None:
    """Mantém o resultado visível até o usuário decidir retornar ao menu."""
    try:
        input_fn("\nPressione ENTER para retornar ao menu...")
    except (EOFError, KeyboardInterrupt):
        print("\nRetornando ao menu.")


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
            else:
                tag = "CONSULTA"
            print(_paint(f"  [{number:>2}] {label:<49} [{tag}]", CYAN))
    print(_paint("\n  [ 0] Encerrar TECH DESK", BLUE))


def _run_memory_operation(key: str, input_fn: collections.abc.Callable[[str], str]) -> None:
    operation = OPERATIONS[key]
    print("\n" + _paint(f"OTIMIZADOR | {operation.title.upper()}", BLUE))
    print(f"Risco: {operation.risk}")
    print(operation.description)
    if key == "cleanup_temp":
        count, size = preview_temp_cleanup()
        print(f"Prévia: {count} arquivo(s), {size / (1024**2):.2f} MiB elegíveis")
    try:
        answer = input_fn("Para confirmar, digite SIM: ").strip().upper()
    except (EOFError, KeyboardInterrupt):
        print("Operação cancelada.")
        return
    if answer != "SIM":
        print("Operação cancelada.")
        return
    try:
        result = execute_operation(key, confirm=lambda _: True)
    except Exception:
        logging.getLogger("techdesk").exception("Falha no otimizador: %s", key)
        print(_paint("Falha inesperada. Consulte o log.", BLUE))
        return
    print(_paint(result.message, CYAN if result.success else BLUE))
    if result.output:
        print(result.output)


def _memory_optimizer_menu(input_fn: collections.abc.Callable[[str], str]) -> None:
    """Submenu guiado; ações de limpeza exigem confirmação individual."""
    while True:
        print("\n" + _paint("╔══════════════════════════════════════════════════════╗", BLUE))
        print(_paint("║              OTIMIZADOR DE MEMÓRIA                  ║", CYAN))
        print(_paint("╚══════════════════════════════════════════════════════╝", BLUE))
        print(_paint("[1] Ver processos com maior consumo de memória", CYAN))
        print(_paint("[2] Solicitar fechamento gracioso por PID", CYAN))
        print(_paint("[3] Limpar temporários antigos", CYAN))
        print(_paint("[4] Esvaziar Lixeira", CYAN))
        print(_paint("[5] Reiniciar Windows Explorer", CYAN))
        print(_paint("[6] Otimização guiada (3, 4 e 5)", CYAN))
        print(_paint("[0] Voltar ao menu principal", BLUE))
        try:
            choice = input_fn("Selecione uma opção: ").strip()
        except (EOFError, KeyboardInterrupt):
            return
        if choice == "0":
            return
        if choice == "1":
            result = top_memory_processes()
            print(result.message)
            print(result.output)
        elif choice == "2":
            result = top_memory_processes()
            print(result.output)
            raw_pid = input_fn("Informe o PID desejado: ").strip()
            if not raw_pid.isdecimal() or int(raw_pid) <= 0:
                print(_paint("PID inválido.", BLUE))
                continue
            pid = int(raw_pid)
            answer = input_fn(f"Solicitar fechamento normal do PID {pid}? Digite FECHAR: ").strip().upper()
            if answer == "FECHAR":
                result = close_process_gracefully(pid)
                print(result.message)
                if result.output:
                    print(result.output)
            else:
                print("Ação cancelada.")
        elif choice in {"3", "4", "5"}:
            key = {"3": "cleanup_temp", "4": "empty_recycle_bin", "5": "restart_explorer"}[choice]
            _run_memory_operation(key, input_fn)
        elif choice == "6":
            for key in ("cleanup_temp", "empty_recycle_bin", "restart_explorer"):
                _run_memory_operation(key, input_fn)
        else:
            print(_paint("Opção inválida.", BLUE))
        try:
            input_fn("Pressione ENTER para continuar...")
        except (EOFError, KeyboardInterrupt):
            return


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
            elif choice == "20":
                _show_section(label.upper(), {
                    key: report["sistema"][key]
                    for key in ("processador", "nucleos_logicos", "memoria_total", "memoria_disponivel")
                })
            else:
                _show_section(label.upper(), report["sistema"])
            _pause_before_menu(input_fn)
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
        elif topic.startswith("tool:"):
            result = open_windows_tool(topic.split(":", 1)[1])
            print(f"\n{label}: {result.message}")
            if result.output:
                print(result.output)
            try:
                input_fn("\nPressione ENTER para retornar ao menu...")
            except (EOFError, KeyboardInterrupt):
                pass
        elif topic == "download_https":
            url = input_fn("\nInforme a URL HTTPS do arquivo: ").strip()
            if not url:
                print(_paint("Download cancelado: URL vazia.", YELLOW))
                continue
            answer = input_fn("Confirma baixar (limite 100 MiB, sem executar)? Digite BAIXAR: ").strip().upper()
            if answer != "BAIXAR":
                print("Download cancelado.")
                continue
            result = download_https_file(url)
            logging.getLogger("techdesk").info("Download HTTPS: %s", "success" if result.success else "failure")
            print(f"\n{label}: {result.message}")
            if result.output:
                print(result.output)
            try:
                input_fn("\nPressione ENTER para retornar ao menu...")
            except (EOFError, KeyboardInterrupt):
                pass
        elif topic == "memory_processes":
            result = top_memory_processes()
            print(f"\n{label}\n{result.message}\n{result.output}")
            try:
                input_fn("\nPressione ENTER para retornar ao menu...")
            except (EOFError, KeyboardInterrupt):
                pass
        elif topic == "memory_optimizer":
            _memory_optimizer_menu(input_fn)
        elif topic == "close_process":
            raw_pid = input_fn("\nInforme o PID exibido no inventário: ").strip()
            if not raw_pid.isdecimal() or int(raw_pid) <= 0:
                print(_paint("PID inválido.", YELLOW))
                continue
            pid = int(raw_pid)
            answer = input_fn(f"Solicitar fechamento normal do PID {pid}? Digite FECHAR: ").strip().upper()
            if answer != "FECHAR":
                print("Ação cancelada.")
                continue
            result = close_process_gracefully(pid)
            print(f"\n{result.message}\n{result.output}")
            try:
                input_fn("\nPressione ENTER para retornar ao menu...")
            except (EOFError, KeyboardInterrupt):
                pass
        elif topic in WINDOWS_DIAGNOSTICS:
            print("\n" + _paint(label.upper(), BLUE))
            print("-" * 60)
            print(run_windows_diagnostic(topic))
            _pause_before_menu(input_fn)
        else:
            print(_paint("Diagnóstico não configurado.", YELLOW))
            _pause_before_menu(input_fn)


def main() -> int:
    args = build_parser().parse_args()
    settings = load_settings()
    configure_logging(settings)
    logging.getLogger("techdesk").info("TECH DESK iniciado")

    print(f"TECH DESK | NR TECH — {platform.system()} {platform.release()}")
    print(_paint("Desenvolvido por Nadison Roberto | © 2026 NR TECH", CYAN))
    if args.diagnostics:
        _show_diagnostics()
        return 0
    if args.diagnostic:
        print(run_windows_diagnostic(args.diagnostic))
        return 0
    return _menu()


if __name__ == "__main__":
    raise SystemExit(main())
