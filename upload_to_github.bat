@echo off
chcp 65001 >nul
title رفع المنظومة إلى GitHub
echo ======================================================================
echo    🚀 جاري رفع منظومة مركز التحكم إلى GitHub تلقائياً...
echo ======================================================================
echo.

git push -u origin master
if %errorlevel% neq 0 (
    echo.
    echo ⚠️ المستودع غير موجود بعد على حسابك في GitHub.
    echo 🌐 جاري فتح صفحة إنشاء المستودع في المتصفح الآن (الاسم مكتوب جاهز)...
    start https://github.com/new?name=Lelbai-Control-Center^&description=Lelbai+Control+Center+and+Scraper
    echo.
    echo ----------------------------------------------------------------------
    echo 📌 في صفحة المتصفح المفتوحة:
    echo 1. اختر (Public) ليعمل التنزيل والتحديث تلقائياً دون أي مفاتيح أو تسجيل دخول.
    echo 2. اضغط على الزر الأخضر بالأسفل "Create repository".
    echo ----------------------------------------------------------------------
    echo.
    echo بعد الضغط على إنشاء المستودع في المتصفح، اضغط أي زر هنا لإتمام الرفع تلقائياً:
    pause >nul
    echo.
    echo 🚀 جاري رفع كافة الملفات إلى GitHub...
    git push -u origin master
)

if %errorlevel% equ 0 (
    echo.
    echo ======================================================================
    echo    ✅ تم رفع كافة الملفات ومشغل الـ EXE إلى GitHub بنجاح تام!
    echo    🔗 رابط المستودع: https://github.com/moayadalazrk/Lelbai-Control-Center
    echo ======================================================================
)

pause
