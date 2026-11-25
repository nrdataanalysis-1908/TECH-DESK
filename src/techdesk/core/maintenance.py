"""Automated Windows endpoint maintenance."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from techdesk.core.operations import OperationResult, _cleanup_temp

TASK_NAMES = (
    "TECH DESK - Daily cleanup 8 AM",
    "TECH DESK - Daily cleanup 6 PM",
)


def _powershell_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _run_powershell(script: str, timeout: int = 60) -> OperationResult:
    try:
        completed = subprocess.run(
            [
                "powershell.exe",
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                script,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
            shell=False,
        )
    except subprocess.TimeoutExpired:
        return OperationResult(False, f"PowerShell exceeded the timeout of {timeout}s.")
    except OSError as exc:
        return OperationResult(False, f"Unable to start PowerShell: {exc}")

    output = "\n".join(
        part.strip() for part in (completed.stdout, completed.stderr) if part.strip()
    )
    if completed.returncode == 0:
        return OperationResult(True, "Command completed.", output[-8000:])
    return OperationResult(
        False,
        f"PowerShell returned exit code {completed.returncode}.",
        output[-8000:],
    )


def _log_paths() -> tuple[Path, Path]:
    root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
    log_dir = root / "NRTech" / "TechDesk" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "maintenance.log", log_dir / "maintenance.jsonl"


def _write_log(event: dict[str, object]) -> None:
    try:
        text_log, json_log = _log_paths()
        timestamp = str(event["timestamp"])
        with text_log.open("a", encoding="utf-8") as stream:
            stream.write(
                f"[{timestamp}] {event['component']}: {event['status']} — "
                f"{event['message']}\n"
            )
        with json_log.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, ensure_ascii=False) + "\n")
    except OSError:
        # A logging failure must not interrupt endpoint maintenance.
        pass


def clear_recycle_bin() -> OperationResult:
    """Uses the native mechanism only; never removes internal $Recycle.Bin files."""
    script = (
        "$ErrorActionPreference = 'Stop'; "
        "try { Clear-RecycleBin -Force -ErrorAction Stop; exit 0 } "
        "catch { [Console]::Error.WriteLine($_.Exception.Message); exit 23 }"
    )
    result = _run_powershell(script, timeout=120)
    if result.success:
        return OperationResult(True, "Recycle Bin processed by Windows.", result.output)
    return OperationResult(
        False,
        "Windows could not empty the Recycle Bin. No internal metadata was removed.",
        result.output or result.message,
    )


def run_maintenance() -> OperationResult:
    """Runs TEMP and Recycle Bin cleanup, recording partial success without hiding failures."""
    temp_result = _cleanup_temp()
    _write_log({
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "component": "TEMP",
        "status": "success" if temp_result.success else "failure",
        "message": temp_result.message,
    })

    recycle_result = clear_recycle_bin()
    _write_log({
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "component": "RecycleBin",
        "status": "success" if recycle_result.success else "warning",
        "message": recycle_result.message,
        "detail": recycle_result.output,
    })

    message = f"TEMP: {temp_result.message}\nRecycle Bin: {recycle_result.message}"
    output = recycle_result.output
    return OperationResult(
        temp_result.success and recycle_result.success,
        message,
        output,
    )


def install_schedule() -> OperationResult:
    """Registers or updates the daily 8 AM/6 PM tasks for the current user."""
    python_exe = str(Path(sys.executable).resolve())
    working_dir = str(Path(__file__).resolve().parents[2])
    script = (
        "$ErrorActionPreference = 'Stop'; "
        f"$python = {_powershell_quote(python_exe)}; "
        f"$work = {_powershell_quote(working_dir)}; "
        "$action = New-ScheduledTaskAction -Execute $python "
        "-Argument '-m techdesk.maintenance --run' -WorkingDirectory $work; "
        "$principal = New-ScheduledTaskPrincipal "
        "-UserId ($env:USERDOMAIN + '\\' + $env:USERNAME) "
        "-LogonType Interactive -RunLevel Limited; "
        "foreach ($hour in @(8, 18)) { "
        "$timeLabel = if ($hour -eq 8) { '8 AM' } else { '6 PM' }; "
        "$name = 'TECH DESK - Daily cleanup ' + $timeLabel; "
        "$trigger = New-ScheduledTaskTrigger -Daily "
        "-At ([datetime]::Today.AddHours($hour)); "
        "Register-ScheduledTask -TaskName $name -Action $action "
        "-Trigger $trigger -Principal $principal -Force | Out-Null; "
        "Write-Output ('Registered: ' + $name) }"
    )
    result = _run_powershell(script)
    return OperationResult(
        result.success,
        "Daily schedules at 8 AM and 6 PM configured." if result.success
        else "Unable to configure scheduled tasks.",
        result.output or result.message,
    )


def schedule_status() -> OperationResult:
    names = ",".join(_powershell_quote(name) for name in TASK_NAMES)
    script = (
        "$ErrorActionPreference = 'Stop'; "
        f"$names = @({names}); "
        "foreach ($name in $names) { "
        "$task = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue; "
        "if ($null -eq $task) { Write-Output ($name + ': not found') } "
        "else { Write-Output ($task.TaskName + ': ' + $task.State) } }"
    )
    result = _run_powershell(script)
    return OperationResult(result.success, "Scheduled task status.", result.output)


def remove_schedule() -> OperationResult:
    names = ",".join(_powershell_quote(name) for name in TASK_NAMES)
    script = (
        "$ErrorActionPreference = 'Stop'; "
        f"$names = @({names}); "
        "foreach ($name in $names) { "
        "Unregister-ScheduledTask -TaskName $name -Confirm:$false "
        "-ErrorAction SilentlyContinue; "
        "Write-Output ('Removed, if present: ' + $name) }"
    )
    result = _run_powershell(script)
    return OperationResult(
        result.success,
        "Scheduled task removal request completed."
        if result.success else "Failed to remove scheduled tasks.",
        result.output or result.message,
    )
