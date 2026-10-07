@echo off
cd /d "%~dp0"

py login.py
if %errorlevel% neq 0 (
    python login.py
)

pause
