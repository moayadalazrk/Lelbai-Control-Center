@echo off
cd /d "%~dp0"

py review_server.py
if %errorlevel% neq 0 (
    python review_server.py
)

pause
