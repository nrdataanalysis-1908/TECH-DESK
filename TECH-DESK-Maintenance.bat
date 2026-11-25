@echo off
setlocal
title TECH DESK - Automated Maintenance

rem Permite executar o pacote diretamente do checkout, sem alterar o PATH.
set "PYTHONPATH=%~dp0src;%PYTHONPATH%"

if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" -m techdesk.maintenance %*
) else (
    where py >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Python Launcher not found. Install Python 3.11 or later.
        pause
        exit /b 1
    )
    py -m techdesk.maintenance %*
)

set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" (
    echo.
    echo [WARNING] Maintenance finished with a warning. Check the log at:
    echo %LOCALAPPDATA%\NRTech\TechDesk\logs\maintenance.log
)
if "%~1"=="" pause
exit /b %RESULT%
