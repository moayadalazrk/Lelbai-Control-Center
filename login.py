# -*- coding: utf-8 -*-
"""
أداة فتح المتصفح لتسجيل الدخول وحفظ الجلسة يدوياً
تفتح المتصفح فقط وتتركه مفتوحاً بالكامل تحت تحكم المستخدم.
لا تقوم بأي إجراء تلقائي ولا تغلق المتصفح حتى يقوم المستخدم بإغلاقه بنفسه أو الضغط على Enter.
"""

import os
import sys
import time

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from playwright.sync_api import sync_playwright

def clean_browser_session_locks(user_data_dir: str):
    import shutil
    import subprocess
    os.makedirs(user_data_dir, exist_ok=True)
    try:
        import psutil
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmd = " ".join(proc.info.get('cmdline') or []).lower()
                name = (proc.info.get('name') or "").lower()
                if "browser_session" in cmd and ("chrome" in name or "chromium" in name or "node" in name):
                    proc.kill()
            except Exception:
                pass
    except Exception:
        pass

    if sys.platform == "win32":
        try:
            cmd = "Get-CimInstance Win32_Process | Where-Object { ($_.Name -like '*chrome*' -or $_.Name -like '*chromium*') -and $_.CommandLine -like '*browser_session*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
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
                    os.remove(del_path)
    except Exception:
        pass

    for cache_sub in ["GPUPersistentCache", "ShaderCache", "GrShaderCache"]:
        cp = os.path.join(user_data_dir, cache_sub)
        if os.path.exists(cp):
            try:
                shutil.rmtree(cp, ignore_errors=True)
            except Exception:
                pass

def run_login_helper(target_url: str = "https://www.facebook.com/login.php", user_data_dir: str = "./browser_session"):
    session_path = os.path.abspath(user_data_dir)
    os.makedirs(session_path, exist_ok=True)

    print("""
================================================================
          🌐 فتح المتصفح لتسجيل الدخول وحفظ الجلسة
================================================================
  1. تم فتح المتصفح المرئي أمامك الآن.
  2. سجّل دخولك وتصفح بحريتك الكاملة.
  3. لن يقوم البرنامج بإغلاق المتصفح أو التدخل في أي شيء.
  4. عندما تنتهي من تسجيل الدخول:
     👉 ببساطة أغلق نافذة المتصفح بيدك (زر X)
        أو اضغط زر [Enter] في هذه الشاشة.
  5. سيتم حفظ جميع الكوكيز وبيانات الجلسة تلقائياً للاستخدام الدائم.
================================================================
""")

    clean_browser_session_locks(session_path)

    with sync_playwright() as p:
        print("[+] جاري تشغيل المتصفح...")
        context = None
        for attempt in range(2):
            try:
                context = p.chromium.launch_persistent_context(
                    user_data_dir=session_path,
                    headless=False,
                    viewport=None,  # يفتح بحجم النافذة الطبيعي
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                    locale="ar-SY",
                    timezone_id="Asia/Damascus",
                    args=[
                        "--start-maximized",
                        "--disable-blink-features=AutomationControlled",
                        "--disable-infobars",
                        "--no-sandbox"
                    ]
                )
                break
            except Exception as e:
                if attempt == 0:
                    print("⚠️ تم رصد حجز سابق للجلسة، جاري تنظيف الأقفال والمحاولة...")
                    clean_browser_session_locks(session_path)
                    time.sleep(1)
                else:
                    raise e

        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        page = context.pages[0] if context.pages else context.new_page()

        print(f"[+] فتح صفحة تسجيل الدخول المباشرة: {target_url}")
        try:
            page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            print(f"[!] تنبيه أثناء التحميل: {e}")

        print("\n🟢 المتصفح مفتوح الآن أمامك.")
        print("💡 سجّل دخولك متى ما أردت، وعند الانتهاء أغلق المتصفح بيدك (أو اضغط Enter هنا)...\n")

        # انتظار إما ضغط Enter من المستخدم أو إغلاق نافذة المتصفح يدوياً
        try:
            # نتحقق في خيط انتظار بسيط أو عبر input
            # باستخدام input نتيح للمستخدم الضغط على Enter فور انتهائه
            # ونراقب أيضاً إذا أغلق المتصفح
            import threading
            
            user_finished = threading.Event()
            
            def wait_for_user_input():
                try:
                    input("👉 اضغط Enter هنا بعد الانتهاء وحفظ الجلسة: ")
                except Exception:
                    pass
                user_finished.set()

            input_thread = threading.Thread(target=wait_for_user_input, daemon=True)
            input_thread.start()

            while not user_finished.is_set():
                time.sleep(1)
                # فحص إذا أغلق المستخدم جميع الصفحات أو المتصفح
                try:
                    if len(context.pages) == 0 or all(p.is_closed() for p in context.pages):
                        print("\n[+] تم اكتشاف إغلاق المتصفح يدوياً.")
                        break
                except Exception:
                    break

        except KeyboardInterrupt:
            print("\n[!] جاري حفظ الجلسة والإغلاق...")

        # حفظ ملف حالة التوثيق والكوكيز
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
        print("🚀 الحساب الآن جاهز ومحفوظ، ويمكنك تشغيل بوت سحب الإعلانات في أي وقت!")
        print("="*50)

if __name__ == "__main__":
    try:
        run_login_helper()
    except KeyboardInterrupt:
        print("\n[!] تم الإنهاء.")
    except Exception as e:
        print(f"\n[❌] خطأ: {e}")
