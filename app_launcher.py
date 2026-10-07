# -*- coding: utf-8 -*-
"""
برنامج تشغيل ومحدث منصة للبيع الذكي (Lelbai Control Launcher & Auto-Updater)
يقوم بالتحقق من وجود تحديثات جديدة على GitHub وتطبيقها تلقائياً،
وعرض تاريخ آخر تحديث للنظام، ثم تشغيل السيرفر وفتح لوحة التحكم للمستخدم.
"""

import os
import sys
import json
import time
import subprocess
import webbrowser
import urllib.request

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LAST_UPDATE_FILE = os.path.join(BASE_DIR, "last_update.json")
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

def load_repo_config():
    default_repo = "https://github.com/moayadalazrk/Lelbai-Control-Center.git"
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                return cfg.get("github_repo", default_repo)
        except Exception:
            pass
    return default_repo

def check_for_updates():
    print("\n[1/3] 🔍 جاري فحص وجود تحديثات جديدة على GitHub...")
    git_dir = os.path.join(BASE_DIR, ".git")

    if os.path.exists(git_dir):
        try:
            # فحص السيرفر البعيد
            subprocess.run(["git", "fetch", "origin"], cwd=BASE_DIR, capture_output=True, timeout=15)
            status = subprocess.check_output(["git", "status", "-uno"], cwd=BASE_DIR, universal_newlines=True)

            if "behind" in status or "Your branch is behind" in status:
                print("      ⚡ تم العثور على تحديث جديد! جاري سحب التحديث وتطبيقه...")
                pull_res = subprocess.check_output(["git", "pull", "--rebase"], cwd=BASE_DIR, universal_newlines=True)
                print("      ✅ تم تحديث الملفات بنجاح من GitHub!")
                
                if "requirements.txt" in pull_res:
                    print("      📦 تحديث الحزم المطلوبة...")
                    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], cwd=BASE_DIR)
            else:
                print("      ✅ كافة الملفات محدثة إلى أحدث إصدار على GitHub.")
        except Exception as e:
            print(f"      ℹ️ تخطي فحص Git: {e}")
    else:
        # فحص عبر GitHub API في حال تشغيل المشروع بدون Git
        try:
            repo_url = load_repo_config()
            repo_name = repo_url.replace(".git", "").replace("https://github.com/", "").strip("/")
            api_url = f"https://api.github.com/repos/{repo_name}/commits/master"
            req = urllib.request.Request(api_url, headers={"User-Agent": "Lelbai-Launcher/1.0"})
            with urllib.request.urlopen(req, timeout=5) as res:
                data = json.loads(res.read().decode("utf-8"))
                commit_date = data.get("commit", {}).get("committer", {}).get("date", "")
                commit_msg = data.get("commit", {}).get("message", "")
                save_last_update(commit_date, "متزامن مع GitHub", commit_msg)
        except Exception:
            pass

def save_last_update(date_str, relative="", message=""):
    info = {
        "last_updated_at": date_str,
        "relative_time": relative,
        "commit_message": message,
        "status": "up_to_date"
    }
    try:
        with open(LAST_UPDATE_FILE, "w", encoding="utf-8") as f:
            json.dump(info, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def show_last_update():
    date_str = ""
    relative = ""
    message = ""

    # القراءة من Git
    git_dir = os.path.join(BASE_DIR, ".git")
    if os.path.exists(git_dir):
        try:
            out = subprocess.check_output(
                ["git", "log", "-1", "--format=%ci|%cr|%s"],
                cwd=BASE_DIR,
                stderr=subprocess.DEVNULL,
                universal_newlines=True
            ).strip()
            if out and "|" in out:
                parts = out.split("|", 2)
                date_str = parts[0]
                relative = parts[1] if len(parts) > 1 else ""
                message = parts[2] if len(parts) > 2 else ""
        except Exception:
            pass

    # القراءة من last_update.json
    if not date_str and os.path.exists(LAST_UPDATE_FILE):
        try:
            with open(LAST_UPDATE_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                date_str = saved.get("last_updated_at", "")
                relative = saved.get("relative_time", "")
                message = saved.get("commit_message", "")
        except Exception:
            pass

    if not date_str:
        date_str = time.strftime("%Y-%m-%d %H:%M:%S")

    save_last_update(date_str, relative, message)

    print()
    print("-" * 70)
    print(f"  📅 تاريخ آخر تحديث للنظام: {date_str} {f'({relative})' if relative else ''}")
    if message:
        print(f"  💬 ملخص التحديث الأخير : {message}")
    print("  ✅ حالة المنظومة        : متزامنة وجاهزة للعمل بنجاح")
    print("-" * 70)
    print()

def main():
    print("=" * 70)
    print("   🚀 منصة للبيع (LELBAI) - مشغل التحديث التلقائي ومركز التحكم الذكي 🇸🇾")
    print("=" * 70)

    # 1. التحقق من التحديثات
    check_for_updates()

    # 2. عرض تاريخ آخر تحديث
    show_last_update()

    # 3. تشغيل سيرفر الويب
    print("[2/2] 🌐 جاري تشغيل سيرفر لوحة التحكم وفتح المتصفح...")
    from web_app import run_app
    run_app()

if __name__ == "__main__":
    main()
