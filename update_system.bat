@echo off
chcp 65001 >nul
cd /d "%~dp0"
title تحديث منصة للبيع من GitHub

echo ==========================================================================
echo   🔄 جاري تحديث ملفات المنظومة من GitHub...
echo ==========================================================================

where git >nul 2>nul
if %errorlevel% equ 0 (
    echo [+] جاري التحديث المباشر عبر Git...
    git remote set-url origin https://github.com/moayadalazrk/Lelbai-Control-Center.git
    git fetch origin --prune --tags
    git reset --hard origin/main
    git pull origin main --force
) else (
    echo [+] جاري تنزيل أحدث حزمة من GitHub عبر PowerShell...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri 'https://github.com/moayadalazrk/Lelbai-Control-Center/archive/refs/heads/main.zip' -OutFile 'temp_update.zip'; Expand-Archive -Path 'temp_update.zip' -DestinationPath 'temp_extracted' -Force; Copy-Item -Path 'temp_extracted\Lelbai-Control-Center-main\*' -Destination '.' -Recurse -Force; Remove-Item 'temp_extracted' -Recurse -Force; Remove-Item 'temp_update.zip' -Force"
)

echo.
echo ==========================================================================
echo   ✅ تم سحب وتطبيق التحديث بنجاح! جاري تشغيل المنظومة...
echo ==========================================================================
echo.

call start_app.bat
