# -*- coding: utf-8 -*-
"""
الواجهة الرئيسية لتشغيل بوت سحب إعلانات المجموعات السورية
تتضمن:
1. الفحص والتثبيت التلقائي للمكتبات والمتطلبات في حال نقله لجهاز جديد.
2. عداد مباشر لوقت التشغيل (00:00:00).
3. عداد تفاعلي مباشر لتقدم المجموعات (5/25) وتقدم الإعلانات (550/2500).
"""

import os
import sys
import json
import time
import subprocess
from typing import Dict, Any

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

def ensure_dependencies():
    """التحقق التلقائي من وجود المكتبات وتثبيتها إذا كان البوت منقولاً لجهاز جديد"""
    required_packages = {
        "playwright": "playwright",
        "PIL": "Pillow",
        "requests": "requests"
    }
    missing = []
    for mod, pkg in required_packages.items():
        try:
            __import__(mod)
        except ImportError:
            missing.append(pkg)

    if missing:
        print(f"[*] جاري تثبيت المتطلبات المفقودة على الجهاز ({', '.join(missing)})...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=False)
        print("[*] جاري تثبيت متصفح Chromium...")
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=False)
        print("[✔] تم اكتمال التثبيت بنجاح!\n")

ensure_dependencies()

from scraper import SyrianAdScraper
from login import run_login_helper

def print_banner():
    print("""
================================================================
   🤖 بوت سحب إعلانات المجموعات (سوريا) بالمتصفح المرئي 🇸🇾
================================================================
  الشروط الإجبارية للسحب:
   1. أن يكون الإعلان في سوريا (تحديد المدينة الرئيسية id-citie).
   2. أن يحتوي على رقم هاتف سوري (09xxxxxxxx أو +9639...).
  
  المخرجات في ملف JSON ومجلد الصور:
   - رابط الإعلان (ad_url)
   - رقم الهاتف (phone_number)
   - الوصف المنظف (description)
   - روابط التحميل (images dowlod - ماكس 5)
   - أسماء الصور المحفوظة بصيغة WebP واسم UUID (nimages)
   - تصنيف المدينة والمنطقة (id-citie / id-sub_districts)
================================================================
""")

def format_elapsed_time(start_timestamp: float) -> str:
    """تنسيق الوقت المنقضي بصيغة HH:MM:SS"""
    elapsed = int(time.time() - start_timestamp)
    hours = elapsed // 3600
    minutes = (elapsed % 3600) // 60
    seconds = elapsed % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def get_group_urls() -> list:
    """الحصول على روابط المجموعات إما من ملف groups.txt أو إدخال يدوي"""
    groups_file = "groups.txt"
    urls = []
    
    if os.path.exists(groups_file):
        with open(groups_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    urls.append(line)

    if urls:
        print(f"[+] تم العثور على {len(urls)} مجموعات في ملف groups.txt:")
        use_file = input("هل تريد بدء السحب من هذه المجموعات مباشرة؟ (اضغط Enter للمتابعة، أو اكتب n للإدخال يدوياً): ").strip().lower()
        if use_file not in ['n', 'no', 'لا']:
            return urls

    print("\nأدخل روابط المجموعات (رابط واحد في كل سطر).")
    print("عند الانتهاء، اضغط Enter على سطر فارغ:")
    urls = []
    while True:
        url = input("🔗 رابط المجموعة: ").strip()
        if not url:
            if urls:
                break
            else:
                print("[!] يرجى إدخال رابط واحد على الأقل.")
                continue
        urls.append(url)
        
    return urls

def remove_group_from_file(groups_file_path: str, url_to_remove: str):
    """حذف رابط المجموعة المكتملة من ملف groups.txt لمنع تكرارها عند إعادة التشغيل"""
    if not os.path.exists(groups_file_path):
        return
    try:
        norm_target = url_to_remove.strip().rstrip('/').lower()
        with open(groups_file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        new_lines = []
        for line in lines:
            stripped = line.strip()
            norm_line = stripped.rstrip('/').lower()
            
            # فحص ما إذا كان هذا السطر هو رابط المجموعة المكتملة
            if not stripped.startswith("#") and norm_line and (norm_line == norm_target or norm_line in norm_target or norm_target in norm_line):
                # إذا كان السطر السابق عبارة عن تعليق يحمل اسم المجموعة
                if new_lines and new_lines[-1].strip().startswith("#") and not new_lines[-1].strip().startswith("# ==="):
                    new_lines.pop()
                continue
            new_lines.append(line)

        with open(groups_file_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
            f.flush()
            os.fsync(f.fileno())

        print(f"[✔] تم شطب المجموعة المكتملة من قائمة groups.txt بنجاح.")
    except Exception as e:
        pass

def start_scraping_flow():
    """تدفق عملية السحب مع العدادات الحية المباشرة"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    groups_file_path = os.path.join(base_dir, "groups.txt")
    urls = get_group_urls()
    
    limit_input = input("\n🔢 كم عدد الإعلانات الصالحة المطلوب سحبها من كل مجموعة؟ (الافتراضي 100): ").strip()
    max_ads_per_group = int(limit_input) if limit_input.isdigit() and int(limit_input) > 0 else 100
    
    output_name = input("💾 اسم ملف النتائج JSON (الافتراضي: ads_syria.json): ").strip()
    if not output_name:
        output_name = "ads_syria.json"
    if not output_name.endswith(".json"):
        output_name += ".json"

    if not os.path.isabs(output_name):
        output_path = os.path.join(base_dir, output_name)
    else:
        output_path = output_name

    total_groups = len(urls)
    total_target_ads = total_groups * max_ads_per_group
    start_time = time.time()

    print("\n" + "="*65)
    print(f"🚀 بدء تشغيل البوت بالمتصفح المرئي...")
    print(f"   📁 إجمالي المجموعات: {total_groups}")
    print(f"   🎯 المطلوب من كل مجموعة: {max_ads_per_group} إعلان (أو الخروج بعد دقيقة إن لم تتوفر إعلانات)")
    print(f"   📊 إجمالي الهدف: {total_target_ads} إعلان")
    print(f"   💾 ملف النتائج المباشر: {output_path}")
    print(f"   🖼️  مجلد حفظ الصور: {os.path.join(base_dir, 'asstes', 'imgs')}")
    print("="*65)

    scraper = SyrianAdScraper(user_data_dir=os.path.join(base_dir, "browser_session"), headless=False)
    
    # تحميل الإعلانات السابقة إن وُجدت
    scraper.load_existing_ads(output_path)
    
    for group_idx, url in enumerate(urls, 1):
        print(f"\n=================================================================")
        print(f"⏱️  {format_elapsed_time(start_time)} | 📁 المجموعات: {group_idx}/{total_groups} | 📢 إجمالي الإعلانات في الملف: {len(scraper.extracted_ads)}")
        print(f"🔗 جاري معالجة المجموعة [{group_idx}/{total_groups}]: {url}")
        print(f"=================================================================")

        def live_progress_callback(ad: Dict[str, Any], current_total: int, group_count: int = 0):
            time_str = format_elapsed_time(start_time)
            phone_disp = ad.get("phone_number") or ""
            imgs_cnt = len(ad.get("nimages", []))
            loc_disp = ad.get("location_detected", "")
            title_disp = ad.get("clean_title") or ad.get("description", "")[:50]
            cat_disp = ad.get("category") or "عام"
            
            print(f"\n⏱️  {time_str} | 📁 المجموعات: {group_idx}/{total_groups} | 📢 الإعلانات الكلية: {current_total} (المجموعة الحالية: {group_count}/{max_ads_per_group})")
            print(f"⚡ إعلان سوري معتمد! 🟢 | [{cat_disp}] {title_disp}")
            print(f"   📞 الرقم: {phone_disp} | 📍 الموقع: {loc_disp}")
            print(f"   🖼️  الصور (WebP): {imgs_cnt} صور | 🔗 {ad['ad_url']}")
            print("-" * 65)

        scraper.scrape_group(
            group_url=url,
            max_ads=max_ads_per_group,
            max_scroll_attempts=250,
            output_file=output_path,
            progress_callback=live_progress_callback
        )

        # حذف رابط المجموعة المكتملة من ملف groups.txt
        remove_group_from_file(groups_file_path, url)

    total_time = format_elapsed_time(start_time)
    print("\n" + "="*65)
    print(f"🎉 تم الانتهاء من جميع المجموعات بنجاح!")
    print(f"⏱️  الوقت الإجمالي المستغرق: {total_time}")
    print(f"📁 المجموعات المكتملة: {total_groups}/{total_groups}")
    print(f"📊 إجمالي الإعلانات السورية المسحوبة: {len(scraper.extracted_ads)}/{total_target_ads}")
    print(f"📁 ملف النتائج النهائي: {output_path}")
    print(f"🖼️  مجلد الصور: {os.path.join(base_dir, 'asstes', 'imgs')}")
    print("="*65)

def main():
    print_banner()
    
    print("الخيارات المتاحة:")
    print(" [1] 🚀 بدء سحب الإعلانات من المجموعات مباشرة (سحب + ذكاء اصطناعي)")
    print(" [2] 🖥️  فتح لوحة المراجعة البشرية والنشر الفوري (Web Dashboard)")
    print(" [3] 🔐 تسجيل الدخول إلى فيسبوك وحفظ الجلسة")
    print(" [0] ❌ خروج")
    
    choice = input("\n👉 اختر رقم العملية (الافتراضي: 1): ").strip()
    
    if choice == "2":
        from review_server import start_review_server
        cfg = load_config()
        port = int(cfg.get("dashboard_port", 5000))
        start_review_server(port)
    elif choice == "3":
        run_login_helper()
        next_step = input("\nهل ترغب في بدء سحب الإعلانات الآن؟ (y/n): ").strip().lower()
        if next_step in ['y', 'yes', 'نعم', '']:
            start_scraping_flow()
    elif choice == "0":
        print("\nمع السلامة! 👋")
    else:
        start_scraping_flow()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[!] تم إيقاف البرنامج بواسطة المستخدم.")
    except Exception as e:
        print(f"\n[❌] حدث خطأ: {e}")
