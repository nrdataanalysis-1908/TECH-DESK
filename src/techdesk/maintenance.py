"""Command-line entry point for automated maintenance."""

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
        print("\nTECH DESK | AUTOMATED MAINTENANCE")
        print("[1] Run maintenance now")
        print("[2] Configure daily schedule (8 AM and 6 PM)")
        print("[3] View scheduled tasks")
        print("[4] Remove scheduled tasks")
        print("[0] Sair")
        try:
            choice = input("Select: ").strip()
        except (EOFError, KeyboardInterrupt):
            return 0

        if choice == "0":
            return 0
        if choice == "1":
            if input("Run TEMP and Recycle Bin cleanup? Type YES: ").strip().upper() != "YES":
                print("Operation cancelled.")
                continue
            result = run_maintenance()
        elif choice == "2":
            if input("Register tasks at 8 AM and 6 PM? Type YES: ").strip().upper() != "YES":
                print("Operation cancelled.")
                continue
            result = install_schedule()
        elif choice == "3":
            result = schedule_status()
        elif choice == "4":
            if input("Remove both scheduled tasks? Type REMOVE: ").strip().upper() != "REMOVE":
                print("Operation cancelled.")
                continue
            result = remove_schedule()
        else:
            print("Invalid option.")
            continue
        _show(result)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="TECH DESK — automated maintenance")
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--run", action="store_true", help="runs TEMP and Recycle Bin cleanup")
    actions.add_argument("--install-schedule", action="store_true", help="schedules tasks at 8 AM and 6 PM")
    actions.add_argument("--status", action="store_true", help="checks scheduled tasks")
    actions.add_argument("--remove-schedule", action="store_true", help="removes scheduled tasks")
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
