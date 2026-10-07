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

    with sync_playwright() as p:
        print("[+] جاري تشغيل المتصفح...")
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
