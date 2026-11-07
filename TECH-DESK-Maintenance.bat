@echo off
setlocal
title TECH DESK - Manutencao automatica

rem Permite executar o pacote diretamente do checkout, sem alterar o PATH.
set "PYTHONPATH=%~dp0src;%PYTHONPATH%"

if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" -m techdesk.maintenance %*
) else (
    where py >nul 2>&1
    if errorlevel 1 (
        echo [ERRO] Python Launcher nao encontrado. Instale Python 3.11 ou superior.
        pause
        exit /b 1
    )
    py -m techdesk.maintenance %*
)

set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" (
    echo.
    echo [AVISO] A manutencao terminou com alerta. Consulte o log em:
    echo %LOCALAPPDATA%\NRTech\TechDesk\logs\maintenance.log
)
if "%~1"=="" pause
exit /b %RESULT%
