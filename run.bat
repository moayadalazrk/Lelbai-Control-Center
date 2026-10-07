@echo off
cd /d "%~dp0"

py main.py
if %errorlevel% neq 0 (
    python main.py
)

pause
