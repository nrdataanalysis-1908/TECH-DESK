"""Entrada de linha de comando para a manutenção automatizada."""

import argparse

from techdesk.core.maintenance import (
    install_schedule,
    remove_schedule,
    run_maintenance,
    schedule_status,
)


def _show(result) -> None:
    print(result.message)
    if result.output:
        print(result.output)


def _interactive() -> int:
    while True:
        print("\nTECH DESK | MANUTENÇÃO AUTOMÁTICA")
        print("[1] Executar manutenção agora")
        print("[2] Configurar agendamento diário (08h e 18h)")
        print("[3] Consultar agendamentos")
        print("[4] Remover agendamentos")
        print("[0] Sair")
        try:
            choice = input("Selecione: ").strip()
        except (EOFError, KeyboardInterrupt):
            return 0

        if choice == "0":
            return 0
        if choice == "1":
            if input("Executar limpeza de TEMP e Lixeira? Digite SIM: ").strip().upper() != "SIM":
                print("Operação cancelada.")
                continue
            result = run_maintenance()
        elif choice == "2":
            if input("Registrar tarefas às 08h e 18h? Digite SIM: ").strip().upper() != "SIM":
                print("Operação cancelada.")
                continue
            result = install_schedule()
        elif choice == "3":
            result = schedule_status()
        elif choice == "4":
            if input("Remover as duas tarefas agendadas? Digite REMOVER: ").strip().upper() != "REMOVER":
                print("Operação cancelada.")
                continue
            result = remove_schedule()
        else:
            print("Opção inválida.")
            continue
        _show(result)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="TECH DESK — manutenção automatizada")
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--run", action="store_true", help="executa TEMP e Lixeira")
    actions.add_argument("--install-schedule", action="store_true", help="agenda 08h e 18h")
    actions.add_argument("--status", action="store_true", help="consulta as tarefas")
    actions.add_argument("--remove-schedule", action="store_true", help="remove as tarefas")
    args = parser.parse_args()

    if args.run:
        result = run_maintenance()
    elif args.install_schedule:
        result = install_schedule()
    elif args.status:
        result = schedule_status()
    elif args.remove_schedule:
        result = remove_schedule()
    else:
        return _interactive()
    _show(result)
    return 0 if result.success else 2


if __name__ == "__main__":
    raise SystemExit(main())
