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
from techdesk.core.maintenance import (
    install_schedule,
    remove_schedule,
    run_maintenance,
    schedule_status,
)
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
    "01  |  IT SUPPORT DASHBOARD": [
        ("1", "Clean temporary files", "operation:cleanup_temp"),
        ("2", "Run Disk Cleanup (cleanmgr)", "tool:disk_cleanup"),
        ("3", "Verify system files (SFC)", "operation:sfc_scan"),
        ("4", "Repair Windows image (DISM)", "operation:dism_restore"),
        ("5", "Restart Windows Update service", "operation:restart_windows_update"),
        ("6", "Reset network catalog (Winsock)", "operation:reset_winsock"),
        ("7", "Update Group Policies (GPO)", "operation:update_group_policy"),
        ("8", "Selective event log cleanup", "operation:clear_event_logs"),
        ("9", "System Information (msinfo32)", "tool:system_info"),
        ("10", "Device Manager", "tool:device_manager"),
        ("11", "View network adapters", "adapters"),
        ("12", "Upgrade installed applications with Winget", "operation:winget_upgrade_all"),
        ("13", "View running processes", "processes"),
        ("14", "View key service status", "services"),
    ],
    "02  |  ADDITIONAL DIAGNOSTICS": [
        ("15", "System summary and diagnostics", "system"),
        ("16", "Storage and disk space", "storage"),
        ("17", "Full IP configuration", "ipconfig"),
        ("18", "DNS servers", "dns"),
        ("19", "Connectivity test", "connectivity"),
        ("20", "Firewall status", "firewall"),
        ("21", "Microsoft Defender status", "defender"),
        ("22", "Check for available updates (Winget)", "winget"),
        ("23", "Installed software inventory", "software"),
        ("24", "Critical Windows events and errors", "events"),
        ("25", "USB device inventory", "usb"),
        ("26", "Top memory-consuming processes", "memory_processes"),
        ("27", "Real-time CPU and memory usage", "performance"),
    ],
    "03  |  ADDITIONAL TOOLS": [
        ("28", "Export event logs (EVTX)", "operation:backup_event_logs"),
        ("29", "Open PowerShell", "tool:powershell"),
        ("30", "Internet speed test", "tool:speedtest"),
        ("31", "Download file over HTTPS (without execution)", "download_https"),
        ("32", "Request graceful process shutdown", "close_process"),
        ("33", "Memory Optimizer (submenu)", "memory_optimizer"),
        ("34", "Restart Windows Explorer", "operation:restart_explorer"),
        ("35", "Empty Recycle Bin", "operation:empty_recycle_bin"),
    ],
    "04  |  AUTOMATED MAINTENANCE": [
        ("36", "Automated maintenance (TEMP + Recycle Bin + schedule)", "maintenance"),
    ],
}


def _enable_ansi() -> bool:
    """Enables ANSI sequences in modern Windows consoles; fails safely."""
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
        help="collects and displays a local read-only diagnostic report",
    )
    parser.add_argument(
        "--diagnostic",
        choices=sorted(WINDOWS_DIAGNOSTICS),
        help="runs a specific read-only Windows query",
    )
    return parser


def _show_section(title: str, values: dict[str, object]) -> None:
    print("\n" + _paint(title, BLUE))
    print("-" * 48)
    for label, value in values.items():
        print(f"  {label:<22}: {value if value is not None else 'Not available'}")


def _show_diagnostics() -> None:
    report = collect_diagnostics()
    for section, values in report.items():
        _show_section(section.upper(), values)


def _pause_before_menu(input_fn: collections.abc.Callable[[str], str]) -> None:
    """Keeps results visible until the user chooses to return to the menu."""
    try:
        input_fn("\nPress ENTER to return to the menu...")
    except (EOFError, KeyboardInterrupt):
        print("\nReturning to the menu.")


def _show_menu() -> None:
    print("\n" + _paint("╔══════════════════════════════════════════════════════════════╗", CYAN))
    print(_paint("║                    TECH DESK  |  NR TECH                     ║", CYAN))
    print(_paint("║             IT MANAGEMENT & SUPPORT CENTER                   ║", BLUE))
    print(_paint("╚══════════════════════════════════════════════════════════════╝", CYAN))
    print("  [QUERY]     Read-only")
    print("  [EXECUTION] Changes the system after confirmation")
    print("  [ADMIN]     Requires elevated privileges")
    for group, entries in MENU_GROUPS.items():
        print("\n" + _paint(group, BLUE))
        for number, label, topic in entries:
            if topic.startswith("operation:"):
                key = topic.split(":", 1)[1]
                tag = "ADMIN" if OPERATIONS[key].requires_admin else "EXECUTION"
            elif topic == "maintenance":
                tag = "EXECUTION"
            else:
                tag = "QUERY"
            print(_paint(f"  [{number:>2}] {label:<49} [{tag}]", CYAN))
    print(_paint("\n  [ 0] Exit TECH DESK", BLUE))


def _run_memory_operation(key: str, input_fn: collections.abc.Callable[[str], str]) -> None:
    operation = OPERATIONS[key]
    print("\n" + _paint(f"OPTIMIZER | {operation.title.upper()}", BLUE))
    print(f"Risk: {operation.risk}")
    print(operation.description)
    if key == "cleanup_temp":
        count, size = preview_temp_cleanup()
        print(f"Preview: {count} file(s), {size / (1024**2):.2f} MiB eligible")
    try:
        answer = input_fn("To confirm, type YES: ").strip().upper()
    except (EOFError, KeyboardInterrupt):
        print("Operation cancelled.")
        return
    if answer != "YES":
        print("Operation cancelled.")
        return
    try:
        result = execute_operation(key, confirm=lambda _: True)
    except Exception:
        logging.getLogger("techdesk").exception("Optimizer failed: %s", key)
        print(_paint("Unexpected failure. Check the log.", BLUE))
        return
    print(_paint(result.message, CYAN if result.success else BLUE))
    if result.output:
        print(result.output)


def _memory_optimizer_menu(input_fn: collections.abc.Callable[[str], str]) -> None:
    """Guided submenu; cleanup actions require individual confirmation."""
    while True:
        print("\n" + _paint("╔══════════════════════════════════════════════════════╗", BLUE))
        print(_paint("║                  MEMORY OPTIMIZER                  ║", CYAN))
        print(_paint("╚══════════════════════════════════════════════════════╝", BLUE))
        print(_paint("[1] View top memory-consuming processes", CYAN))
        print(_paint("[2] Request graceful shutdown by PID", CYAN))
        print(_paint("[3] Clean old temporary files", CYAN))
        print(_paint("[4] Empty Recycle Bin", CYAN))
        print(_paint("[5] Restart Windows Explorer", CYAN))
        print(_paint("[6] Guided optimization (3, 4, and 5)", CYAN))
        print(_paint("[0] Return to the main menu", BLUE))
        try:
            choice = input_fn("Select an option: ").strip()
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
            raw_pid = input_fn("Enter the target PID: ").strip()
            if not raw_pid.isdecimal() or int(raw_pid) <= 0:
                print(_paint("Invalid PID.", BLUE))
                continue
            pid = int(raw_pid)
            answer = input_fn(f"Request normal shutdown of PID {pid}? Type CLOSE: ").strip().upper()
            if answer == "CLOSE":
                result = close_process_gracefully(pid)
                print(result.message)
                if result.output:
                    print(result.output)
            else:
                print("Action cancelled.")
        elif choice in {"3", "4", "5"}:
            key = {"3": "cleanup_temp", "4": "empty_recycle_bin", "5": "restart_explorer"}[choice]
            _run_memory_operation(key, input_fn)
        elif choice == "6":
            for key in ("cleanup_temp", "empty_recycle_bin", "restart_explorer"):
                _run_memory_operation(key, input_fn)
        else:
            print(_paint("Invalid option.", BLUE))
        try:
            input_fn("Press ENTER to continue...")
        except (EOFError, KeyboardInterrupt):
            return


def _maintenance_menu(input_fn: collections.abc.Callable[[str], str]) -> None:
    while True:
        print("\n" + _paint("AUTOMATED MAINTENANCE | TECH DESK", BLUE))
        print("[1] Run maintenance now (TEMP + Recycle Bin)")
        print("[2] Configure daily schedule (8 AM and 6 PM)")
        print("[3] View scheduled tasks")
        print("[4] Remove scheduled tasks")
        print("[0] Return to the main menu")
        try:
            choice = input_fn("Select an option: ").strip()
        except (EOFError, KeyboardInterrupt):
            return
        if choice == "0":
            return
        if choice == "1":
            if input_fn("Run maintenance now? Type YES: ").strip().upper() != "YES":
                print("Operation cancelled.")
                continue
            result = run_maintenance()
        elif choice == "2":
            if input_fn("Register tasks at 8 AM and 6 PM? Type YES: ").strip().upper() != "YES":
                print("Operation cancelled.")
                continue
            result = install_schedule()
        elif choice == "3":
            result = schedule_status()
        elif choice == "4":
            if input_fn("Remove scheduled tasks? Type REMOVE: ").strip().upper() != "REMOVE":
                print("Operation cancelled.")
                continue
            result = remove_schedule()
        else:
            print(_paint("Invalid option.", YELLOW))
            continue
        print(_paint(result.message, CYAN if result.success else YELLOW))
        if result.output:
            print(result.output)
        try:
            input_fn("Press ENTER to continue...")
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
            choice = input_fn("\nSelect an option: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting TECH DESK.")
            return 0

        if choice == "0":
            print("TECH DESK has exited.")
            return 0
        if choice not in actions:
            print(_paint("Invalid option. Try again.", YELLOW))
            continue

        label, topic = actions[choice]
        if topic in {"system", "storage"}:
            report = collect_diagnostics()
            if topic == "storage":
                _show_section(label.upper(), report["storage"])
            elif choice == "20":
                _show_section(label.upper(), {
                    key: report["system"][key]
                    for key in ("processor", "logical_cores", "total_memory", "available_memory")
                })
            else:
                _show_section(label.upper(), report["system"])
            _pause_before_menu(input_fn)
        elif topic.startswith("operation:"):
            operation_key = topic.split(":", 1)[1]
            operation = OPERATIONS[operation_key]
            print("\n" + "=" * 68)
            print(_paint(f" EXECUTION CENTER | {operation.title.upper()}", BLUE))
            print("=" * 68)
            print(f" Action            : {operation.title}")
            print(f" Risk level        : {operation.risk}")
            print(f" Privilege         : {'Administrator' if operation.requires_admin else 'Standard user'}")
            print(f" Planned action    : {operation.description}")
            if operation_key == "cleanup_temp":
                count, size = preview_temp_cleanup()
                print(f" Preview           : {count} file(s), {size / (1024**2):.2f} MiB eligible")
            print("-" * 68)
            print(" To execute, type YES. Any other response cancels.")
            try:
                answer = input_fn(" Confirmation: ").strip().upper()
            except (EOFError, KeyboardInterrupt):
                print("\n Operation cancelled.", flush=True)
                continue

            if answer != "YES":
                execute_operation(operation_key, confirm=lambda _: False)
                print(_paint("\n STATUS: CANCELLED — no action was performed.", YELLOW), flush=True)
                try:
                    input_fn("\nPress ENTER to return to the menu...")
                except (EOFError, KeyboardInterrupt):
                    pass
                continue

            print("\n" + "=" * 68, flush=True)
            print(_paint(" RUNNING OPERATION — DO NOT CLOSE THIS WINDOW", YELLOW), flush=True)
            print("=" * 68, flush=True)
            try:
                result = execute_operation(operation_key, confirm=lambda _: True)
            except Exception:
                logging.getLogger("techdesk").exception(
                    "Unexpected failure while running operation %s", operation_key
                )
                print(_paint("\n STATUS: INTERNAL ERROR — check the TECH DESK log.", YELLOW), flush=True)
                try:
                    input_fn("\nPress ENTER to return to the menu...")
                except (EOFError, KeyboardInterrupt):
                    pass
                continue

            print("\n" + "=" * 68)
            if result.success:
                print(_paint(" FINAL STATUS: EXECUTION COMPLETED", GREEN))
            else:
                print(_paint(" FINAL STATUS: EXECUTION FAILED", YELLOW))
            print(f" Result: {result.message}")
            print("-" * 68)
            if result.output:
                print(" COMMAND OUTPUT:")
                print(result.output)
            else:
                print(" COMMAND OUTPUT: Windows returned no text.")
            print("=" * 68, flush=True)
            try:
                input_fn("\nPress ENTER to return to the menu...")
            except (EOFError, KeyboardInterrupt):
                pass
        elif topic.startswith("tool:"):
            result = open_windows_tool(topic.split(":", 1)[1])
            print(f"\n{label}: {result.message}")
            if result.output:
                print(result.output)
            try:
                input_fn("\nPress ENTER to return to the menu...")
            except (EOFError, KeyboardInterrupt):
                pass
        elif topic == "download_https":
            url = input_fn("\nEnter the file's HTTPS URL: ").strip()
            if not url:
                print(_paint("Download cancelled: empty URL.", YELLOW))
                continue
            answer = input_fn("Confirm download (100 MiB limit, no execution)? Type DOWNLOAD: ").strip().upper()
            if answer != "DOWNLOAD":
                print("Download cancelled.")
                continue
            result = download_https_file(url)
            logging.getLogger("techdesk").info("Download HTTPS: %s", "success" if result.success else "failure")
            print(f"\n{label}: {result.message}")
            if result.output:
                print(result.output)
            try:
                input_fn("\nPress ENTER to return to the menu...")
            except (EOFError, KeyboardInterrupt):
                pass
        elif topic == "memory_processes":
            result = top_memory_processes()
            print(f"\n{label}\n{result.message}\n{result.output}")
            try:
                input_fn("\nPress ENTER to return to the menu...")
            except (EOFError, KeyboardInterrupt):
                pass
        elif topic == "memory_optimizer":
            _memory_optimizer_menu(input_fn)
        elif topic == "maintenance":
            _maintenance_menu(input_fn)
        elif topic == "close_process":
            raw_pid = input_fn("\nEnter the PID shown in the inventory: ").strip()
            if not raw_pid.isdecimal() or int(raw_pid) <= 0:
                print(_paint("Invalid PID.", YELLOW))
                continue
            pid = int(raw_pid)
            answer = input_fn(f"Request normal shutdown of PID {pid}? Type CLOSE: ").strip().upper()
            if answer != "CLOSE":
                print("Action cancelled.")
                continue
            result = close_process_gracefully(pid)
            print(f"\n{result.message}\n{result.output}")
            try:
                input_fn("\nPress ENTER to return to the menu...")
            except (EOFError, KeyboardInterrupt):
                pass
        elif topic in WINDOWS_DIAGNOSTICS:
            print("\n" + _paint(label.upper(), BLUE))
            print("-" * 60)
            print(run_windows_diagnostic(topic))
            _pause_before_menu(input_fn)
        else:
            print(_paint("Diagnostic is not configured.", YELLOW))
            _pause_before_menu(input_fn)


def main() -> int:
    args = build_parser().parse_args()
    settings = load_settings()
    configure_logging(settings)
    logging.getLogger("techdesk").info("TECH DESK iniciado")

    print(f"TECH DESK | NR TECH — {platform.system()} {platform.release()}")
    print(_paint("Developed by Nadison Roberto | © 2026 NR TECH", CYAN))
    if args.diagnostics:
        _show_diagnostics()
        return 0
    if args.diagnostic:
        print(run_windows_diagnostic(args.diagnostic))
        return 0
    return _menu()


if __name__ == "__main__":
    raise SystemExit(main())
