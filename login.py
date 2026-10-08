# -*- coding: utf-8 -*-
"""
أداة فتح المتصفح لتسجيل الدخول وحفظ الجلسة يدوياً
تستخدم المتصفح الرسمي (Google Chrome أو Microsoft Edge) المثبت على الجهاز مباشرة
لتفادي أي كشف أتمتة أو تعليق لزر تسجيل الدخول في فيسبوك، مع حفظ الجلسة الدائمة.
"""

import os
import sys
import time
import subprocess
import shutil

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def clean_browser_session_locks(user_data_dir: str):
    os.makedirs(user_data_dir, exist_ok=True)
    try:
        import psutil
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmd = " ".join(proc.info.get('cmdline') or []).lower()
                name = (proc.info.get('name') or "").lower()
                if "browser_session" in cmd and ("chrome" in name or "chromium" in name or "msedge" in name or "node" in name):
                    proc.kill()
            except Exception:
                pass
    except Exception:
        pass

    if sys.platform == "win32":
        try:
            cmd = "Get-CimInstance Win32_Process | Where-Object { ($_.Name -like '*chrome*' -or $_.Name -like '*chromium*' -or $_.Name -like '*edge*') -and $_.CommandLine -like '*browser_session*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
            subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, timeout=5)
        except Exception:
            pass

    time.sleep(0.5)

    lock_files = ["lockfile", "SingletonLock", "SingletonCookie", "SingletonSocket"]
    for lock in lock_files:
        lock_path = os.path.join(user_data_dir, lock)
        if os.path.exists(lock_path):
            try:
                os.remove(lock_path)
            except Exception:
                pass

    snapshots_dir = os.path.join(user_data_dir, "Snapshots")
    if os.path.exists(snapshots_dir):
        try:
            shutil.rmtree(snapshots_dir, ignore_errors=True)
        except Exception:
            pass

    parent_dir = os.path.dirname(user_data_dir) or "."
    session_basename = os.path.basename(user_data_dir)
    try:
        for item in os.listdir(parent_dir):
            if item.startswith(session_basename) and "CHROME_DELETE" in item:
                del_path = os.path.join(parent_dir, item)
                if os.path.isdir(del_path):
                    shutil.rmtree(del_path, ignore_errors=True)
                elif os.path.isfile(del_path):
                    del_path_f = os.path.join(parent_dir, item)
                    os.remove(del_path_f)
    except Exception:
        pass

    for cache_sub in ["GPUPersistentCache", "ShaderCache", "GrShaderCache"]:
        cp = os.path.join(user_data_dir, cache_sub)
        if os.path.exists(cp):
            try:
                shutil.rmtree(cp, ignore_errors=True)
            except Exception:
                pass

    pref_file = os.path.join(user_data_dir, "Default", "Preferences")
    if os.path.exists(pref_file):
        try:
            import json
            with open(pref_file, "r", encoding="utf-8") as f:
                pref_data = json.load(f)
            if "profile" in pref_data and isinstance(pref_data["profile"], dict):
                pref_data["profile"]["exit_type"] = "Normal"
                pref_data["profile"]["exited_cleanly"] = True
            with open(pref_file, "w", encoding="utf-8") as f:
                json.dump(pref_data, f)
        except Exception:
            pass

def find_installed_browser():
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"),
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe")
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None

def get_playwright_channel():
    b = find_installed_browser()
    if b:
        return "chrome" if "chrome" in b.lower() else "msedge"
    return None

def run_login_helper(target_url: str = "https://m.facebook.com/", user_data_dir: str = None):
    if not user_data_dir:
        user_data_dir = os.path.join(BASE_DIR, "browser_session")
    session_path = os.path.abspath(user_data_dir)
    os.makedirs(session_path, exist_ok=True)

    clean_browser_session_locks(session_path)

    browser_exe = find_installed_browser()

    if browser_exe:
        browser_name = "Google Chrome" if "chrome" in browser_exe.lower() else "Microsoft Edge"
        print(f"""
================================================================
          🌐 تشغيل المتصفح المباشر لتسجيل الدخول السريع
================================================================
  🟢 تم العثور على المتصفح: {browser_name}
  🚀 تم فتح النسخة المباشرة الخفيفة (m.facebook.com).
  ✨ النسخة الخفيفة لا تعلق إطلاقاً، وتظهر شاشة الكود فوراً!
  
  💡 تعليمات هامة:
  1. أدخل البريد الإلكتروني أو الهاتف وكلمة المرور.
  2. اضغط تسجيل الدخول (سيرسل الطلب فوراً وبدون أي تعليق).
  3. ستظهر لك شاشة إدخال رمز التأكيد (الكود) المكون من 6 أرقام.
  4. انسخ الكود من بريدك أو هاتفك واكتبه واضغط متابعة.
  5. عند إتمام الدخول وظهور حسابك بنجاح:
     👉 ببساطة أغلق نافذة المتصفح (زر X).
  6. سيتم حفظ الجلسة والكوكيز للاستخدام الدائم مع البوت تلقائياً!
================================================================
""")
        cmd = [
            browser_exe,
            f"--user-data-dir={session_path}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-session-crashed-bubble",
            "--start-maximized",
            target_url
        ]
        
        try:
            proc = subprocess.Popen(cmd)
            proc.wait()
        except KeyboardInterrupt:
            pass

        time.sleep(1)

        # محاولة عمل نسخة احتياطية من auth_state.json عبر Playwright في الخلفية إن أمكن
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                ch = get_playwright_channel()
                kw = {"user_data_dir": session_path, "headless": True}
                if ch: kw["channel"] = ch
                ctx = p.chromium.launch_persistent_context(**kw)
                ctx.storage_state(path=os.path.join(session_path, "auth_state.json"))
                ctx.close()
        except Exception:
            pass

        print("\n" + "="*50)
        print("🎉 تم حفظ الجلسة والكوكيز بنجاح في: " + session_path)
        print("🚀 الحساب الآن متصل ومحفوظ، ويمكنك تشغيل بوت سحب الإعلانات في أي وقت!")
        print("="*50)
        return

    # Fallback to Playwright if no installed Chrome/Edge found
    print("""
================================================================
          🌐 فتح المتصفح لتسجيل الدخول وحفظ الجلسة
================================================================
  1. تم فتح المتصفح أمامك.
  2. سجّل دخولك وتصفح بحريتك الكاملة.
  3. عندما تنتهي: أغلق نافذة المتصفح بيدك (زر X).
================================================================
""")
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        print("[+] جاري تشغيل المتصفح...")
        ch = get_playwright_channel()
        kwargs = {
            "user_data_dir": session_path,
            "headless": False,
            "viewport": None,
            "ignore_default_args": ["--enable-automation"],
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "locale": "ar-SY",
            "timezone_id": "Asia/Damascus",
            "args": [
                "--start-maximized",
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--no-sandbox"
            ]
        }
        if ch:
            kwargs["channel"] = ch

        context = p.chromium.launch_persistent_context(**kwargs)

        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.chrome = {
                app: { isInstalled: false },
                runtime: {},
                loadTimes: () => ({}),
                csi: () => ({})
            };
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['ar-SY', 'ar', 'en-US', 'en'] });
        """)

        page = context.pages[0] if context.pages else context.new_page()

        print(f"[+] فتح صفحة تسجيل الدخول: {target_url}")
        try:
            page.goto(target_url, wait_until="domcontentloaded", timeout=45000)
        except Exception as e:
            print(f"[!] تنبيه أثناء التحميل: {e}")

        try:
            page.bring_to_front()
        except Exception:
            pass

        try:
            while True:
                time.sleep(1)
                try:
                    if not context.pages or all(p.is_closed() for p in context.pages):
                        print("\n[+] تم رصد إغلاق نافذة المتصفح.")
                        break
                except Exception:
                    break
        except KeyboardInterrupt:
            pass

        try:
            storage_file = os.path.join(session_path, "auth_state.json")
            context.storage_state(path=storage_file)
            print(f"[✔] تم حفظ ملف حالة التوثيق في: {storage_file}")
        except Exception:
            pass

        try:
            context.close()
        except Exception:
            pass

        print("\n" + "="*50)
        print("🎉 تم حفظ الجلسة بنجاح في: " + session_path)
        print("🚀 الحساب الآن متصل، ويمكنك تشغيل بوت سحب الإعلانات في أي وقت!")
        print("="*50)

if __name__ == "__main__":
    try:
        run_login_helper()
    except KeyboardInterrupt:
        print("\n[!] تم الإنهاء.")
    except Exception as e:
        print(f"\n[❌] خطأ: {e}")
