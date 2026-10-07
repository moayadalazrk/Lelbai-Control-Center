@echo off
cd /d "%~dp0"
title Lelbai Control Center

echo ========================================================
echo   Starting Lelbai Control Center Server...
echo ========================================================

if exist "Lelbai_Launcher.exe" (
    Lelbai_Launcher.exe
) else (
    py app_launcher.py
    if %errorlevel% neq 0 (
        python app_launcher.py
    )
)

pause
