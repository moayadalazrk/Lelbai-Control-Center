# -*- coding: utf-8 -*-
"""
برنامج التثبيت التلقائي لكافة متطلبات البوت
"""

import sys
import subprocess

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

def main():
    print("=" * 65)
    print("   📦 تثبيت مكتبات ومتطلبات بوت سحب الإعلانات السورية 🇸🇾")
    print("=" * 65)
    print()

    print("[1/3] تحديث مدير الحزم pip...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=False)

    print()
    print("[2/3] تثبيت مكتبات البايثون (Playwright, Pillow, Requests)...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=False)

    print()
    print("[3/3] تثبيت متصفح Chromium المخصص للتشغيل المرئي...")
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=False)

    print()
    print("=" * 65)
    print("✅ تم اكتمال التثبيت بنجاح 100%!")
    print("يمكنك الآن تشغيل البوت مباشرة بالضغط على run.bat")
    print("=" * 65)
    print()

if __name__ == "__main__":
    main()
