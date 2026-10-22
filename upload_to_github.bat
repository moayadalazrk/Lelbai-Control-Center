@echo off
chcp 65001 >nul
title رفع التحديثات إلى GitHub
echo ======================================================================
echo    🚀 جاري رفع كود التحديث ومجلد الاستيراد إلى GitHub تلقائياً...
echo ======================================================================
echo.

git add -A
git commit -m "update: sync changes v1.5.10"
git push origin main
git push origin main:master
git tag -f v1.5.10
git push origin -f v1.5.10

if %errorlevel% equ 0 (
    echo.
    echo ======================================================================
    echo    ✅ تم رفع كافة التحديثات وملفات الـ EXE إلى GitHub بنجاح تام!
    echo    🔗 رابط المستودع: https://github.com/moayadalazrk/Lelbai-Control-Center
    echo ======================================================================
) else (
    echo.
    echo ❌ حدث خطأ أثناء التحديث إلى GitHub. يرجى التحقق من اتصال الإنترنت.
)

pause
