@echo off
chcp 65001 >nul
title رفع المنظومة إلى GitHub
echo ======================================================================
echo    🚀 جاري رفع منظومة مركز التحكم إلى GitHub تلقائياً...
echo ======================================================================
echo.

git add -A
git commit -m "update: sync changes"
git push origin main
git push origin main:master
git tag -f v1.1.0
git push origin -f v1.1.0

if %errorlevel% equ 0 (
    echo.
    echo ======================================================================
    echo    ✅ تم رفع كافة الملفات ومشغل الـ EXE إلى GitHub بنجاح تام!
    echo    🔗 رابط المستودع: https://github.com/moayadalazrk/Lelbai-Control-Center
    echo ======================================================================
) else (
    echo.
    echo ❌ حدث خطأ أثناء المزامنة مع GitHub. يرجى التحقق من اتصال الإنترنت.
)

pause
