@echo off
chcp 65001 >nul
cd /d "%~dp0"
title منصة للبيع - مركز التحكم الشامل

echo ======================================================================
echo    🚀 جاري بدء تشغيل منصة للبيع (مركز التحكم وإدارة الإعلانات) 🇸🇾
echo ======================================================================
echo.

:: 1. البحث عن بايثون في النظام
set "PY_CMD="

where py >nul 2>nul
if %errorlevel% equ 0 (
    set "PY_CMD=py"
    goto :PYTHON_FOUND
)

where python >nul 2>nul
if %errorlevel% equ 0 (
    set "PY_CMD=python"
    goto :PYTHON_FOUND
)

for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python*") do (
    if exist "%%D\python.exe" (
        set "PY_CMD=%%D\python.exe"
        goto :PYTHON_FOUND
    )
)

for /d %%D in ("C:\Python*") do (
    if exist "%%D\python.exe" (
        set "PY_CMD=%%D\python.exe"
        goto :PYTHON_FOUND
    )
)

:: إذا لم يتم العثور على بايثون
echo.
echo ======================================================================
echo    ⚠️  تنبيه: لغة Python غير مثبتة على هذا الكمبيوتر!
echo ======================================================================
echo.
echo  لكي تعمل المنظومة، يلزم توفر لغة بايثون (Python 3.10 أو أحدث).
echo  جاري محاولة تثبيت بايثون تلقائياً... يرجى الانتظار دقيقة واحدة...
echo.

where winget >nul 2>nul
if %errorlevel% equ 0 (
    echo [*] جاري التثبيت الذكي عبر متجر ويندوز (winget)...
    winget install Python.Python.3.11 --accept-source-agreements --accept-package-agreements --silent
    if %errorlevel% equ 0 (
        echo [✔] تم تثبيت بايثون بنجاح!
        set "PY_CMD=python"
        goto :PYTHON_FOUND
    )
)

echo [*] جاري تحميل مثبت بايثون الرسمي من موقع Python.org...
powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object Net.WebClient).DownloadFile('https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe', '$env:TEMP\python_installer.exe')"

if exist "%TEMP%\python_installer.exe" (
    echo [*] جاري تشغيل مثبت بايثون... يرجى الانتظار...
    start /wait "" "%TEMP%\python_installer.exe" /passive InstallAllUsers=0 PrependPath=1 Include_pip=1
    del "%TEMP%\python_installer.exe" 2>nul
    
    where python >nul 2>nul
    if %errorlevel% equ 0 (
        set "PY_CMD=python"
        goto :PYTHON_FOUND
    )
)

echo.
echo ❌ تعذر تثبيت بايثون تلقائياً.
echo يرجى تنزيل بايثون وتثبيته يدوياً من: https://www.python.org/downloads/
echo (تأكد من تفعيل خيار Add python.exe to PATH أثناء التثبيت)
echo.
pause
exit /b 1

:PYTHON_FOUND
echo [✔] تم العثور على مفسر بايثون: %PY_CMD%

:: 2. التحقق من وجود الحزم والمكتبات وتثبيتها تلقائياً
%PY_CMD% -c "import playwright, PIL, requests" 2>nul
if %errorlevel% neq 0 (
    echo.
    echo [*] جاري تثبيت الحزم والمكتبات المطلوبة لأول مرة تلقائياً...
    %PY_CMD% -m pip install -r requirements.txt
    %PY_CMD% -m playwright install chromium
    echo [✔] اكتمل تثبيت المكتبات بنجاح!
    echo.
)

:: 3. تشغيل سيرفر لوحة التحكم
echo [*] جاري تشغيل السيرفر وفتح لوحة التحكم في المتصفح...
%PY_CMD% web_app.py

if %errorlevel% neq 0 (
    echo.
    echo ======================================================================
    echo ❌ حدث خطأ أثناء تشغيل السيرفر. يرجى مراجعة الرسائل أعلاه.
    echo ======================================================================
    pause
)
