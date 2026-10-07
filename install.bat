@echo off
cd /d "%~dp0"

if exist setup.py (
    py setup.py
    if %errorlevel% neq 0 (
        python setup.py
    )
) else (
    echo [*] Installing requirements...
    py -m pip install -r requirements.txt 2>nul || python -m pip install -r requirements.txt
    py -m playwright install chromium 2>nul || python -m playwright install chromium
    echo [✔] Done!
)

pause
