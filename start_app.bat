@echo off
cd /d "%~dp0"
title Lelbai Control Center

echo ========================================================
echo   Starting Lelbai Control Center Server...
echo ========================================================

if exist "C:\Lelbai_Control_Center\Lelbai_Launcher.exe" (
    "C:\Lelbai_Control_Center\Lelbai_Launcher.exe"
    exit /b
)

if exist "Lelbai_Launcher.exe" (
    Lelbai_Launcher.exe
) else (
    py web_app.py
    if %errorlevel% neq 0 (
        python web_app.py
    )
)

pause
