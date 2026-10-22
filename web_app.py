# -*- coding: utf-8 -*-
"""
المنظومة المركزية المتكاملة وإدارة الروابط والمراجعة الشرعية (Lelbai Master Control Center)
سيرفر متكامل لإدارة الروابط وحفظها مع تاريخ آخر سحب، وعرض حالة الإعلانات بالمعايير الثلاثة (المواصفات، الشريعة، الجاهزية للنشر).
"""

import os
import sys
import json
import time
import queue
import random
import re
import shutil
import base64
import threading
import subprocess
import webbrowser
import urllib.parse
import socket
from http.server import HTTPServer, ThreadingHTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, List, Optional

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
    except Exception:
        pass
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
    except Exception:
        pass

import asyncio
from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright
from syria_filter import validate_ad, normalize_text
from image_processor import process_ad_images
from gemini_processor import GeminiProcessor, get_gemini_usage_info
from config import load_config, save_config
from publisher import publish_ad_to_website, export_ad_to_import_folder, detect_category_id, PUBLISHED_FILE
from category_classifier import (
    classify_leaf_category,
    extract_detailed_specifications,
    extract_or_generate_account_name,
    check_if_ad_already_exists,
    generate_ai_review_report
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CATEGORIES_DB_FILE = os.path.join(BASE_DIR, "categories_db.json")
PENDING_FILE = os.path.join(BASE_DIR, "pending_review.json")
FLAGGED_FILE = os.path.join(BASE_DIR, "flagged_ads.json")
ALL_ADS_FILE = os.path.join(BASE_DIR, "ads_syria.json")
GROUPS_DATA_FILE = os.path.join(BASE_DIR, "groups_data.json")
GROUPS_FILE = os.path.join(BASE_DIR, "groups.txt")
IMGS_DIR = os.path.join(BASE_DIR, "asstes", "imgs")

os.makedirs(IMGS_DIR, exist_ok=True)

FILE_IO_LOCK = threading.RLock()

def read_json_file(file_path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(file_path):
        return []
    with FILE_IO_LOCK:
        for attempt in range(4):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        data = json.loads(content)
                        if isinstance(data, list):
                            return data
                return []
            except (json.JSONDecodeError, PermissionError):
                if attempt < 3:
                    time.sleep(0.08)
                    continue
            except Exception:
                break
    return []

def write_json_file(file_path: str, data: List[Dict[str, Any]]):
    with FILE_IO_LOCK:
        for attempt in range(4):
            try:
                temp_path = f"{file_path}.tmp_{os.getpid()}_{threading.get_ident()}"
                with open(temp_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                    f.flush()
                    os.fsync(f.fileno())
                if os.path.exists(file_path):
                    os.replace(temp_path, file_path)
                else:
                    os.rename(temp_path, file_path)
                return
            except (PermissionError, OSError):
                if attempt < 3:
                    time.sleep(0.1)
                    continue
            except Exception as e:
                print(f"[!] خطأ أثناء كتابة {file_path}: {e}")
                break

def ensure_storage_files():
    """توليد ملفات البيانات النظيفة تلقائياً إذا لم تكن موجودة عند تشغيل التطبيق"""
    for fp in [PENDING_FILE, PUBLISHED_FILE, FLAGGED_FILE, GROUPS_DATA_FILE, ALL_ADS_FILE]:
        if not os.path.exists(fp):
            write_json_file(fp, [])

ensure_storage_files()

DEFAULT_STARTER_GROUPS = [
    {"id": 1, "name": "سوق سيارات سوريا", "url": "https://www.facebook.com/groups/5259742280745703/", "category": "السيارات", "status": "جاهز", "last_scraped_at": "لم يُسحب بعد", "last_ads_count": 0, "total_ads_count": 0, "created_at": time.strftime("%Y-%m-%d %H:%M:%S")},
    {"id": 2, "name": "سوق السيارات الكبير في إدلب", "url": "https://www.facebook.com/groups/616337179824577/", "category": "السيارات", "status": "جاهز", "last_scraped_at": "لم يُسحب بعد", "last_ads_count": 0, "total_ads_count": 0, "created_at": time.strftime("%Y-%m-%d %H:%M:%S")},
    {"id": 3, "name": "عقارات دمشق وريفها – بيع وإيجار", "url": "https://www.facebook.com/groups/syria.damascuse/", "category": "العقارات", "status": "جاهز", "last_scraped_at": "لم يُسحب بعد", "last_ads_count": 0, "total_ads_count": 0, "created_at": time.strftime("%Y-%m-%d %H:%M:%S")},
    {"id": 4, "name": "سوق الموبايلات في دمشق", "url": "https://www.facebook.com/groups/363826584999651/", "category": "الموبايلات والإلكترونيات", "status": "جاهز", "last_scraped_at": "لم يُسحب بعد", "last_ads_count": 0, "total_ads_count": 0, "created_at": time.strftime("%Y-%m-%d %H:%M:%S")},
    {"id": 5, "name": "الطاقة الشمسية في سورية", "url": "https://www.facebook.com/groups/148516947271390/", "category": "الطاقة البديلة", "status": "جاهز", "last_scraped_at": "لم يُسحب بعد", "last_ads_count": 0, "total_ads_count": 0, "created_at": time.strftime("%Y-%m-%d %H:%M:%S")},
    {"id": 6, "name": "بيع واشتري أثاث مستعمل بريف دمشق", "url": "https://www.facebook.com/groups/611791440232636/", "category": "الأثاث والمنزل", "status": "جاهز", "last_scraped_at": "لم يُسحب بعد", "last_ads_count": 0, "total_ads_count": 0, "created_at": time.strftime("%Y-%m-%d %H:%M:%S")}
]

def normalize_group_url(url: str) -> str:
    """توحيد وتنظيف رابط المجموعة أو الصفحة لمنع التكرار بدقة."""
    if not url:
        return ""
    u = str(url).strip()
    if "?" in u:
        u = u.split("?")[0]
    if "#" in u:
        u = u.split("#")[0]
    u = u.rstrip("/").lower()
    u = re.sub(r"^https?://", "", u)
    u = re.sub(r"^(www\.|m\.|web\.|mbasic\.|touch\.)", "", u)
    return u.rstrip("/")

def get_lan_ip() -> str:
    """الحصول على الآي بي المحلي للجهاز في الشبكة المحلية."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"

def enrich_groups_metadata(groups: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """تمييز آخر صفحة مضافة وآخر صفحة تم سحبها ونقطة الانطلاق التلقائية."""
    if not groups:
        return []

    result = [dict(g) for g in groups]

    # البحث عن آخر صفحة تم سحبها بتوقيت صحيح
    scraped_candidates = [
        g for g in result
        if g.get("last_scraped_at") and g.get("last_scraped_at") != "لم يُسحب بعد"
    ]
    last_scraped_group = max(scraped_candidates, key=lambda g: g.get("last_scraped_at", "")) if scraped_candidates else None

    # البحث عن آخر صفحة انضافت (أعلى ID أو أحدث created_at)
    last_added_group = max(result, key=lambda g: (g.get("created_at") or "", g.get("id", 0))) if result else None

    # تحديد نقطة الانطلاق الذكية:
    # إذا كانت آخر صفحة انضافت لم تُسحب بعد، أو تاريخ إضافتها أحدث من تاريخ آخر سحب -> نبدأ منها فوراً
    smart_start_group = None
    if last_added_group and (
        not last_scraped_group or 
        last_added_group.get("last_scraped_at") == "لم يُسحب بعد" or 
        (last_added_group.get("created_at", "") >= last_scraped_group.get("last_scraped_at", ""))
    ):
        smart_start_group = last_added_group
    elif last_scraped_group:
        smart_start_group = last_scraped_group
    else:
        smart_start_group = result[0] if result else None

    for g in result:
        g["is_last_scraped"] = bool(last_scraped_group and g.get("id") == last_scraped_group.get("id"))
        g["is_last_added"] = bool(last_added_group and g.get("id") == last_added_group.get("id"))
        g["is_smart_start"] = bool(smart_start_group and g.get("id") == smart_start_group.get("id"))

    return result

def get_ordered_groups(start_mode: str = "smart", groups: List[Dict[str, Any]] = None, custom_start_url: str = None) -> List[Dict[str, Any]]:
    """ترتيب المجموعات بشكل دائري بحيث يبدأ السحب من الصفحة المحددة أو الذكية."""
    if groups is None:
        groups = read_json_file(GROUPS_DATA_FILE)
    if not groups:
        return []

    enriched = enrich_groups_metadata(groups)
    target_idx = 0

    if custom_start_url:
        norm_custom = normalize_group_url(custom_start_url)
        for idx, g in enumerate(enriched):
            if normalize_group_url(g.get("url", "")) == norm_custom:
                target_idx = idx
                break
    elif start_mode == "last_added":
        for idx, g in enumerate(enriched):
            if g.get("is_last_added"):
                target_idx = idx
                break
    elif start_mode == "last_scraped":
        for idx, g in enumerate(enriched):
            if g.get("is_last_scraped"):
                target_idx = idx
                break
    elif start_mode == "first":
        target_idx = 0
    else:  # "smart" (افتراضي: آخر صفحة انضافت أو آخر صفحة تم سحبها)
        for idx, g in enumerate(enriched):
            if g.get("is_smart_start"):
                target_idx = idx
                break

    return groups[target_idx:] + groups[:target_idx]

# تقييم الإعلان بالمراحل الشاملة (الذكاء الاصطناعي الفائق، التصنيف في أصغر ابن، المواصفات، الشريعة، حساب وهمي، عدم التكرار)
def enrich_ad_status(ad: Dict[str, Any], force_recalc: bool = False) -> Dict[str, Any]:
    if not isinstance(ad, dict):
        return {}
    try:
        # تسريع الاستجابة إذا كان الإعلان مفحوصاً ومكتمل التقييم مسبقاً
        if not force_recalc and ad.get("evaluation") and ad.get("clean_title") and ad.get("publisher_name"):
            ev = ad.get("evaluation", {})
            if isinstance(ev, dict) and "specs_details" in ev and "sharia_details" in ev:
                return ad

        from ai_ad_enhancer import enhance_ad_with_super_ai, get_category_name_by_id, build_category_hierarchy
        # 1. تعزيز الإعلان بالذكاء الاصطناعي (عنوان نخبوي، وصف مهيكل، وأدق تصنيف أصغر فئة)
        ad_copy = enhance_ad_with_super_ai(ad)
        
        # دمج نص الإعلان الكامل للتحليل الدقيق
        full_text = f"{ad_copy.get('clean_title', '')} {ad_copy.get('clean_description') or ad_copy.get('description', '')}"

        cid = ad_copy.get("leaf_category_id", 3207)
        if not cid or not str(cid).isdigit():
            cid = 3207
        cid = int(cid)

        hier = ad_copy.get("category_hierarchy") or build_category_hierarchy(cid)
        p_name = hier.split(">")[-2].strip() if ">" in hier else (hier.split(">")[0].strip() if hier else "عام")

        leaf_info = {
            "category_id": cid,
            "category_name": ad_copy.get("leaf_category_name") or get_category_name_by_id(cid),
            "parent_name": p_name,
            "category_hierarchy": hier
        }

        # 2. استخراج أكبر قدر ممكن من المواصفات المهيكلة
        extracted_specs = extract_detailed_specifications(full_text, leaf_info)
        current_specs = ad_copy.get("specifications") or {}
        if force_recalc or leaf_info.get("parent_name") != "السيارات":
            ad_copy["specifications"] = extracted_specs
        else:
            ad_copy["specifications"] = {**current_specs, **extracted_specs}

        # 3. وضع اسم حساب معلن وهمي سوري واقعي
        if not ad_copy.get("publisher_name"):
            ad_copy["publisher_name"] = extract_or_generate_account_name(full_text)

        # 4. التحقق الصارم من عدم وجود الإعلان على الموقع من قبل
        published_db = read_json_file(PUBLISHED_FILE)
        is_duplicate, dup_reason = check_if_ad_already_exists(ad_copy, published_db, [])
        ad_copy["is_duplicate"] = is_duplicate
        ad_copy["duplicate_reason"] = dup_reason

        # 5. اكتمال المواصفات وتدقيق المدينة والسعر
        if not ad_copy.get("id-citie") or not ad_copy.get("city_name"):
            from syria_filter import classify_location
            loc_res = classify_location(full_text)
            if loc_res.get("id-citie"):
                ad_copy["id-citie"] = loc_res.get("id-citie")
                ad_copy["id-sub_districts"] = loc_res.get("id-sub_districts")
                ad_copy["city_name"] = loc_res.get("city_name")
                ad_copy["sub_district_name"] = loc_res.get("sub_district_name")
                ad_copy["location_detected"] = loc_res.get("location_detected")

        has_images = len(ad_copy.get("nimages", [])) > 0
        has_desc = bool(ad_copy.get("clean_description") or ad_copy.get("description"))
        has_title = bool(ad_copy.get("clean_title") or ad_copy.get("title"))
        has_phone = bool(ad_copy.get("phone_number"))
        has_city = bool(ad_copy.get("id-citie") or ad_copy.get("city_name") or ad_copy.get("location_detected"))
        has_price = ad_copy.get("price_info", {}).get("amount") is not None
        
        is_specs_complete = has_images and has_desc and has_title and has_phone and has_city
        
        # 6. الفحص الشرعي والرقابي
        raw_flags = ad_copy.get("flags", [])
        flags = [f for f in raw_flags if f not in ("no_api_key_provided", "offline_vision_filter", "local_filtered_images", "network_fallback")]
        is_safe = ad_copy.get("is_safe", True) and not any(f in raw_flags for f in ("prohibited_images_detected", "no_valid_images_left"))
        
        # 7. الجاهزية للنشر (مكتمل + سليم شرعياً + غير مكرر على الموقع)
        is_ready_to_publish = is_specs_complete and is_safe and not is_duplicate
        
        is_ai_done = bool(ad_copy.get("ai_evaluated"))
        summary_text = ad_copy.get("moderation_summary")
        if not summary_text:
            if is_ai_done:
                summary_text = "🤖 تم الفحص والاعتماد بالرؤية الذكية السحابية (Gemini Vision API)" if is_safe else "🚫 تم رصد مخالفات رقابية عبر الذكاء الاصطناعي"
            else:
                summary_text = "⏳ بانتظار استكمال فحص الذكاء الاصطناعي (Gemini)"

        # 8. توليد رد وتقرير الذكاء الاصطناعي الشامل
        ai_report = generate_ai_review_report(
            ad_copy,
            leaf_info,
            ad_copy["specifications"],
            ad_copy["publisher_name"],
            is_duplicate,
            dup_reason,
            summary_text
        )
        ad_copy["ai_review"] = ai_report

        resolved_city = ad_copy.get("city_name") or (ad_copy.get("location_detected", "").split("(")[0].strip() if ad_copy.get("location_detected") else "دمشق")
        ad_copy["evaluation"] = {
            "is_specs_complete": is_specs_complete,
            "specs_details": {
                "has_images": has_images,
                "images_count": len(ad_copy.get("nimages", [])),
                "has_desc": has_desc,
                "has_title": has_title,
                "has_phone": has_phone,
                "has_city": has_city,
                "has_price": has_price,
                "city_name": resolved_city,
                "sub_district_name": ad_copy.get("sub_district_name") or "عام"
            },
            "is_ai_evaluated": is_ai_done,
            "ai_model": ad_copy.get("ai_model", "Gemini Vision"),
            "is_sharia_compliant": is_safe,
            "sharia_details": {
                "is_safe": is_safe,
                "flags": flags,
                "summary": summary_text,
                "ai_evaluated": is_ai_done
            },
            "is_duplicate": is_duplicate,
            "duplicate_reason": dup_reason,
            "is_ready_to_publish": is_ready_to_publish,
            "ready_status_label": "جاهز للنشر الفوري 🚀" if is_ready_to_publish else ("مكرر على الموقع ⚠️" if is_duplicate else ("بحاجة لمراجعة أو تنقية" if is_specs_complete else "بيانات غير مكتملة"))
        }
        return ad_copy
    except Exception as e:
        print(f"[!] تحذير أثناء إثراء الإعلان: {e}")
        return ad

# ==============================================================================
# محرك إدارة السحب المتوازي وتحديث تواريخ الروابط
# ==============================================================================
def clean_browser_session_locks(user_data_dir: str):
    """
    تحرير أقفال مجلد الجلسة وإنهاء أي عمليات كروم أو بايثون يتيمة تحتجز browser_session
    وتنظيف ملفات Snapshots و CHROME_DELETE التي تسبب انهيار المتصفح فور إطلاقه (Exit code 33)
    """
    import shutil
    os.makedirs(user_data_dir, exist_ok=True)
    try:
        import psutil
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmd = " ".join(proc.info.get('cmdline') or []).lower()
                name = (proc.info.get('name') or "").lower()
                if "browser_session" in cmd and ("chrome" in name or "chromium" in name or "node" in name):
                    proc.kill()
                elif "login.py" in cmd and proc.pid != os.getpid():
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

    # تنظيف مجلد Snapshots و CHROME_DELETE وأي ملفات كاش مسببة لانهيار Chromium
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

    try:
        if os.path.exists(user_data_dir):
            for item in os.listdir(user_data_dir):
                if "CHROME_DELETE" in item or item == "Snapshots":
                    del_path = os.path.join(user_data_dir, item)
                    if os.path.isdir(del_path):
                        shutil.rmtree(del_path, ignore_errors=True)
                    elif os.path.isfile(del_path):
                        os.remove(del_path)
    except Exception:
        pass

    for cache_sub in ["GPUPersistentCache", "ShaderCache", "GrShaderCache", "Snapshots"]:
        cp = os.path.join(user_data_dir, cache_sub)
        if os.path.exists(cp):
            try:
                shutil.rmtree(cp, ignore_errors=True)
            except Exception:
                pass

    pref_file = os.path.join(user_data_dir, "Default", "Preferences")
    if os.path.exists(pref_file):
        try:
            with open(pref_file, "r", encoding="utf-8") as f:
                pref_data = json.load(f)
            if isinstance(pref_data, dict) and "profile" in pref_data and isinstance(pref_data["profile"], dict):
                pref_data["profile"]["exit_type"] = "Normal"
                pref_data["profile"]["exited_cleanly"] = True
            with open(pref_file, "w", encoding="utf-8") as f:
                json.dump(pref_data, f)
        except Exception:
            pass

def get_browser_channel():
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe")
    ]
    for c in candidates:
        if os.path.exists(c):
            return "chrome"
    return None

def parse_int_safe(val: Any, default: int = 0) -> int:
    if val is None:
        return default
    try:
        s = str(val).strip()
        arabic_digits = "٠١٢٣٤٥٦٧٨٩"
        for idx, d in enumerate(arabic_digits):
            s = s.replace(d, str(idx))
        s = re.sub(r'[^0-9\-]', '', s)
        return int(s) if s and s != '-' else default
    except Exception:
        return default

class ScrapingTaskManager:
    def __init__(self):
        self.is_running = False
        self.stop_requested = False
        self.start_time = 0.0
        self.total_target_ads = 0
        self.total_groups_count = 0
        self.completed_groups_count = 0
        self.total_ads_collected = 0
        self.active_tabs: Dict[int, Dict[str, Any]] = {}
        self.logs: List[str] = []
        self.lock = threading.RLock()
        self.gemini_processor = GeminiProcessor()

    def log(self, message: str):
        with self.lock:
            ts = time.strftime("%H:%M:%S")
            log_line = f"[{ts}] {message}"
            self.logs.append(log_line)
            if len(self.logs) > 200:
                self.logs.pop(0)
        try:
            print(log_line, flush=True)
        except Exception:
            try:
                enc = sys.stdout.encoding or 'cp1256'
                safe_msg = log_line.encode(enc, errors='replace').decode(enc, errors='replace')
                print(safe_msg, flush=True)
            except Exception:
                pass

    def start_scraping_job(self, params: Dict[str, Any]):
        with self.lock:
            if self.is_running:
                return False, "السحب قيد التشغيل بالفعل!"

            self.is_running = True
            self.stop_requested = False
            self.start_time = time.time()
            self.active_tabs.clear()
            self.logs = [f"[{time.strftime('%H:%M:%S')}] 🚀 تم إطلاق مهمة السحب، جاري تشغيل المتصفح والاتصال بالمجموعات..."]

        t = threading.Thread(target=self._run_parallel_scraper, args=(params,), daemon=True)
        t.start()
        return True, "تم بدء السحب بنجاح!"

    def stop_scraping_job(self):
        with self.lock:
            if not self.is_running:
                return False, "لا توجد عملية سحب نشطة."
            self.stop_requested = True
        self.log("⏹️ تم إرسال طلب إيقاف السحب...")
        return True, "جاري إيقاف السحب..."

    def _update_group_scrape_history(self, group_url: str, ads_found_count: int):
        """تحديث تاريخ وعدد الإعلانات المسحوبة للمجموعة في groups_data.json"""
        groups = read_json_file(GROUPS_DATA_FILE)
        norm_u = normalize_group_url(group_url)
        for g in groups:
            norm_g = normalize_group_url(g.get("url", ""))
            if norm_g == norm_u or norm_g in norm_u or norm_u in norm_g:
                g["last_scraped_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                g["last_ads_count"] = ads_found_count
                g["total_ads_count"] = g.get("total_ads_count", 0) + ads_found_count
                g["status"] = "مكتمل"
                break
        write_json_file(GROUPS_DATA_FILE, groups)

    def _run_parallel_scraper(self, params: Dict[str, Any]):
        try:
            if sys.platform == "win32":
                loop = asyncio.ProactorEventLoop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self._async_parallel_scraper(params))
            else:
                asyncio.run(self._async_parallel_scraper(params))
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            self.log(f"❌ خطأ عام أثناء السحب: {e}")
            self.log(f"🔍 تفاصيل: {tb.strip()[-300:]}")
        finally:
            with self.lock:
                self.is_running = False
                self.active_tabs.clear()

    async def _async_parallel_scraper(self, params: Dict[str, Any]):
        urls = params.get("groups", [])
        start_mode = params.get("start_mode", "smart")
        start_url = params.get("start_url")
        all_groups = read_json_file(GROUPS_DATA_FILE)

        # إذا لم يتم تمرير الروابط مسبقاً، نستخدم الترتيب الذكي
        if not urls:
            ordered_objs = get_ordered_groups(start_mode, all_groups, start_url)
            urls = [g.get("url") for g in ordered_objs if g.get("url")]

        if not urls:
            self.log("❌ لم يتم تحديد أي روابط مجموعات للسحب!")
            return

        first_group_name = "المجموعة الأولى"
        norm_first = normalize_group_url(urls[0])
        for g in all_groups:
            if normalize_group_url(g.get("url", "")) == norm_first:
                first_group_name = g.get("name", urls[0])
                break

        concurrent_tabs = parse_int_safe(params.get("concurrent_tabs"), 4)
        concurrent_tabs = max(1, min(concurrent_tabs, 6))
        raw_max_ads = parse_int_safe(params.get("max_ads_per_group"), 100)
        max_ads_per_group = max(1, raw_max_ads)
        raw_timeout = parse_int_safe(params.get("timeout_seconds"), 60)
        if raw_timeout < 20:
            raw_timeout = raw_timeout * 10
        timeout_seconds = max(45, raw_timeout)

        self.total_groups_count = len(urls)
        self.completed_groups_count = 0
        self.total_target_ads = self.total_groups_count * max_ads_per_group

        existing_ads = read_json_file(ALL_ADS_FILE)
        self.total_ads_collected = len(existing_ads)
        seen_signatures = {f"{a.get('phone_number')}_{a.get('description', '')[:50]}" for a in existing_ads}

        self.log(f"🎯 نقطة الانطلاق: البدء من [{first_group_name}] (إجمالي {len(urls)} مجموعات)")
        self.log(f"🚀 بدء محرك السحب المتوازي: {len(urls)} مجموعات | {concurrent_tabs} صفحات متزامنة حقيقية ⚡")

        user_data_dir = os.path.join(BASE_DIR, "browser_session")
        self.log("🔧 فحص وتحرير ملفات جلسة المتصفح...")
        clean_browser_session_locks(user_data_dir)

        browser_launch_args = [
            "--start-maximized",
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--no-sandbox",
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding",
            "--disable-features=CalculateNativeWinOcclusion,IntensiveWakeUpThrottling"
        ]

        self.log("🌐 جاري تشغيل المتصفح...")
        async with async_playwright() as p:
            context = None
            browser_channel = get_browser_channel()
            channel_name = "Google Chrome" if browser_channel else "Chromium"
            self.log(f"⚡ إطلاق جلسة التصفح عبر [{channel_name}]...")
            for attempt in range(2):
                try:
                    kwargs = {
                        "user_data_dir": user_data_dir,
                        "headless": False,
                        "viewport": None,
                        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                        "locale": "ar-SY",
                        "timezone_id": "Asia/Damascus",
                        "args": browser_launch_args,
                        "timeout": 25000
                    }
                    if browser_channel:
                        kwargs["channel"] = browser_channel

                    context = await asyncio.wait_for(
                        p.chromium.launch_persistent_context(**kwargs),
                        timeout=30.0
                    )
                    break
                except Exception as ex:
                    if attempt == 0:
                        self.log(f"⚠️ تنبيه أثناء إطلاق المتصفح ({ex}). جاري تحرير الجلسة وإعادة المحاولة...")
                        clean_browser_session_locks(user_data_dir)
                        browser_channel = None
                        await asyncio.sleep(1.0)
                    else:
                        raise ex

            self.log("✅ تم تشغيل المتصفح بنجاح! جاري تجهيز التبويبات المتزامنة...")
            await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")

            q = asyncio.Queue()
            for idx, u in enumerate(urls, 1):
                q.put_nowait((idx, u))

            async def tab_worker(tab_id: int):
                try:
                    if tab_id == 0 and context.pages:
                        page = context.pages[0]
                    else:
                        page = await context.new_page()
                except Exception as pe:
                    self.log(f"[تبويب {tab_id+1}] ❌ تعذر فتح التبويب: {pe}")
                    return

                while not q.empty() and not self.stop_requested:
                    try:
                        group_idx, group_url = q.get_nowait()
                    except asyncio.QueueEmpty:
                        break

                    with self.lock:
                        self.active_tabs[tab_id] = {
                            "group_idx": group_idx,
                            "url": group_url,
                            "ads_collected": 0,
                            "status": "جاري التحميل..."
                        }

                    self.log(f"[تبويب {tab_id+1}] 🔗 فتح المجموعة [{group_idx}/{self.total_groups_count}]: {group_url}")

                    try:
                        await page.goto(group_url, wait_until="domcontentloaded", timeout=45000)
                    except Exception:
                        pass

                    await asyncio.sleep(2.5)

                    cur_url = page.url
                    group_match = re.search(r'(https?://(?:www\.)?facebook\.com/groups/[0-9a-zA-Z._-]+)', cur_url)
                    if group_match and ("/permalink/" in cur_url or "/posts/" in cur_url):
                        try:
                            await page.goto(group_match.group(1) + "/", wait_until="domcontentloaded", timeout=25000)
                            await asyncio.sleep(2)
                        except Exception:
                            pass

                    scroll_attempts = 0
                    group_ads_count = 0
                    last_ad_time = time.time()

                    # استخراج عنوان واسم المجموعة لتمريره كسياق جغرافي للمنشورات
                    group_page_title = ""
                    try:
                        group_page_title = await page.title()
                    except Exception:
                        pass
                    group_saved_name = ""
                    try:
                        all_groups = read_json_file(GROUPS_DATA_FILE)
                        for g_item in all_groups:
                            if g_item.get("url") and normalize_group_url(g_item.get("url")) == normalize_group_url(group_url):
                                group_saved_name = g_item.get("name", "")
                                break
                    except Exception:
                        pass
                    full_group_context = f"{group_saved_name} {group_page_title}".strip()

                    while scroll_attempts < 250 and group_ads_count < max_ads_per_group and not self.stop_requested:
                        scroll_attempts += 1

                        # تحديث حالة التبويب الحية ليراها المستخدم بالثواني
                        with self.lock:
                            if group_ads_count > 0:
                                self.active_tabs[tab_id]["status"] = f"سحب ({group_ads_count}/{max_ads_per_group})"
                            else:
                                self.active_tabs[tab_id]["status"] = f"فحص المنشورات... ({scroll_attempts})"

                        # فحص إذا تم فتح صفحة منشور منفصلة (Permalink) والعودة فوراً لخلاصة المجموعة
                        try:
                            cur_tab_url = page.url
                            if "/permalink/" in cur_tab_url or "/posts/" in cur_tab_url:
                                m = re.search(r'(https?://(?:www\.)?facebook\.com/groups/[0-9a-zA-Z._-]+)', cur_tab_url)
                                clean_target = (m.group(1) + "/") if m else group_url
                                await page.goto(clean_target, wait_until="domcontentloaded", timeout=20000)
                                await asyncio.sleep(2)
                        except Exception:
                            pass

                        # 1. إغلاق النوافذ المنبثقة ومربعات تسجيل الدخول ومنشورات الـ Dialog المعيقة للتمرير
                        try:
                            await page.keyboard.press("Escape")
                            await page.evaluate("""() => {
                                const closeSelectors = [
                                    "div[aria-label='إغلاق']", "div[aria-label='Close']",
                                    "div[aria-label='Close post']", "div[aria-label='إغلاق المنشور']",
                                    "div[role='dialog'] div[aria-label='إغلاق']", "div[role='dialog'] div[aria-label='Close']",
                                    "div[role='dialog'] div[role='button']", "div[aria-label='X']",
                                    "div[role='dialog'] button"
                                ];
                                for (const sel of closeSelectors) {
                                    document.querySelectorAll(sel).forEach(b => {
                                        try { b.click(); } catch(e){}
                                    });
                                }
                            }""")
                        except Exception:
                            pass

                        # 2. توسيع أزرار 'عرض المزيد' في نص المنشور فقط وتخطي الروابط التي تفتح النوافذ
                        try:
                            await page.evaluate("""() => {
                                const elements = document.querySelectorAll("div[role='button'], span, strong");
                                for (const el of elements) {
                                    if (el.closest("a")) continue; // تخطي الروابط تماماً لتجنب فتح المنشور بنافذة منبثقة
                                    const txt = (el.textContent || '').trim();
                                    if (txt === 'عرض المزيد' || txt === 'See more' || txt === 'See More' || txt === '...عرض المزيد') {
                                        if (el.children.length <= 1) {
                                            try { el.click(); } catch(e){}
                                        }
                                    }
                                }
                            }""")
                        except Exception:
                            pass

                        # 3. استخراج المنشورات من الصفحة
                        try:
                            raw_posts = await page.evaluate("""() => {
                                let containers = document.querySelectorAll("div[role='feed'] > div, div[data-pagelet*='FeedUnit'], div[role='article']");
                                if (!containers || containers.length === 0) {
                                    containers = document.querySelectorAll("div[dir='auto']");
                                }
                                const extracted = [];
                                for (const c of containers) {
                                    let text = '';
                                    const msgEl = c.querySelector("div[data-ad-preview='message'], div[data-ad-comet-preview='message']");
                                    if (msgEl) {
                                        text = (msgEl.innerText || msgEl.textContent || '').trim();
                                    } else {
                                        const candidates = Array.from(c.querySelectorAll("div[dir='auto']")).filter(el => {
                                            if (el.closest("h2, h3, h4, [role='button'], a[role='link']")) return false;
                                            return (el.innerText || '').length > 20;
                                        });
                                        if (candidates.length > 0) {
                                            candidates.sort((a, b) => (b.innerText || '').length - (a.innerText || '').length);
                                            text = (candidates[0].innerText || candidates[0].textContent || '').trim();
                                        } else {
                                            text = (c.innerText || c.textContent || '').trim();
                                        }
                                    }

                                    if (!text || text.length < 15) continue;

                                    const images = [];
                                    const imgEls = c.querySelectorAll("img");
                                    for (const img of imgEls) {
                                        // استبعاد صور البروفايل وصور أصحاب الحسابات والتعليقات
                                        if (img.closest("h2, h3, h4, header, [role='button'], [role='toolbar'], div[aria-label*='تعليق'], div[aria-label*='Comment'], a[href*='/user/'], a[href*='profile.php']")) {
                                            continue;
                                        }

                                        // استبعاد الأيقونات والصور المصغرة جداً
                                        const w = img.naturalWidth || img.width || 0;
                                        const h = img.naturalHeight || img.height || 0;
                                        if ((w > 0 && w < 180) || (h > 0 && h < 180)) {
                                            continue;
                                        }

                                        const src = img.src || img.getAttribute('src');
                                        if (src && src.startsWith('http')) {
                                            const sLow = src.toLowerCase();
                                            if (!sLow.includes('emoji') && !sLow.includes('rsrc.php') && !sLow.includes('icon') && !sLow.includes('static') && !sLow.includes('avatar') && !sLow.includes('profile_pic') && !sLow.includes('spacer.gif') && !sLow.includes('badge')) {
                                                if (!images.includes(src)) images.push(src);
                                            }
                                        }
                                    }

                                    let link = '';
                                    const aTags = c.querySelectorAll("a[href]");
                                    for (const a of aTags) {
                                        const href = a.href || a.getAttribute('href') || '';
                                        if (href.includes('/posts/') || href.includes('/permalink/') || href.includes('story_fbid')) {
                                            link = href.split('?')[0];
                                            break;
                                        }
                                    }

                                    extracted.push({ text, images, link });
                                }
                                return extracted;
                            }""")
                        except Exception:
                            raw_posts = []

                        # فحص وتدقيق كل إعلان مسحوب
                        for p_data in raw_posts:
                            if self.stop_requested:
                                break

                            text_content = p_data.get("text", "")
                            if not text_content or len(text_content) < 15:
                                continue

                            raw_images = p_data.get("images", [])
                            if not raw_images or len(raw_images) == 0:
                                continue

                            validation = validate_ad(text_content, group_context=full_group_context)
                            if not validation["is_valid"]:
                                continue

                            clean_desc = validation.get("cleaned_description", text_content)
                            primary_phone = validation["phones"][0] if validation["phones"] else ""
                            sig = f"{primary_phone}_{clean_desc[:50]}"

                            with self.lock:
                                if sig in seen_signatures:
                                    continue
                                seen_signatures.add(sig)

                            # التحقق الحاسم من عدم وجود الإعلان مسبقاً على الموقع
                            published_db = read_json_file(PUBLISHED_FILE)
                            is_dup, dup_msg = check_if_ad_already_exists({"phone_number": primary_phone, "ad_url": p_data.get("link"), "description": clean_desc}, published_db, [])
                            if is_dup:
                                self.log(f"[🔄 استبعاد إعلان مكرر]: موجود مسبقاً على الموقع ({primary_phone})")
                                continue

                            # تنزيل الصور ومعالجتها إلى WebP بشكل غير حاجب للمهام الأخرى
                            images_download, nimages = await asyncio.to_thread(process_ad_images, raw_images, 5, IMGS_DIR)
                            if not nimages or len(nimages) == 0:
                                continue

                            ad_dict = {
                                "ad_url": p_data.get("link") or group_url,
                                "phone_number": primary_phone,
                                "description": clean_desc,
                                "images dowlod": images_download,
                                "nimages": nimages,
                                "id-citie": validation.get("id-citie"),
                                "id-sub_districts": validation.get("id-sub_districts"),
                                "city_name": validation.get("city_name"),
                                "sub_district_name": validation.get("sub_district_name"),
                                "location_detected": validation.get("location_detected"),
                                "extracted_at": time.strftime("%Y-%m-%d %H:%M:%S")
                            }

                            # فحص وهيكلة الذكاء الاصطناعي بشكل إلزامي لضمان مرور كل إعلان على الذكاء الاصطناعي بنسبة 100%
                            processed_ad = await asyncio.to_thread(self.gemini_processor.process_and_clean_ad, ad_dict, IMGS_DIR)

                            # إعادة محاولة فورية بفاصل زمني لضمان مرور الإعلان على الذكاء الاصطناعي وعدم تخطيه نهائياً
                            if not processed_ad.get("ai_evaluated"):
                                await asyncio.sleep(1.5)
                                processed_ad = await asyncio.to_thread(self.gemini_processor.process_and_clean_ad, ad_dict, IMGS_DIR)

                            if not processed_ad.get("ai_evaluated"):
                                await asyncio.sleep(2.5)
                                processed_ad = await asyncio.to_thread(self.gemini_processor.process_and_clean_ad, ad_dict, IMGS_DIR)

                            # منع قاطع: عدم السماح لأي إعلان بالدخول لقائمة المراجعة إذا لم يمر على الذكاء الاصطناعي
                            if not processed_ad.get("ai_evaluated"):
                                self.log(f"[⚠️ استبعاد مؤقت]: تعذر تقييم الإعلان عبر الذكاء الاصطناعي (Gemini Vision) - لن يتم إدراجه حفاظاً على دقة المنظومة.")
                                continue

                            if not processed_ad.get("is_safe", True):
                                rej_msg = processed_ad.get('rejection_reason') or processed_ad.get('moderation_summary') or 'مخالفة للضوابط'
                                self.log(f"[🚫 استبعاد إعلان مخالف عبر الذكاء الاصطناعي]: {rej_msg}")
                                with FILE_IO_LOCK:
                                    flagged = read_json_file(FLAGGED_FILE)
                                    ad_u = processed_ad.get("ad_url")
                                    ad_t = processed_ad.get("clean_title")
                                    if not any((ad_u and f.get("ad_url") == ad_u) or (ad_t and f.get("clean_title") == ad_t) for f in flagged):
                                        flagged.insert(0, processed_ad)
                                        write_json_file(FLAGGED_FILE, flagged)
                                continue

                            # إثراء الإعلان بالتصنيف في أصغر فئة، المواصفات، حساب وهمي، وفحص التكرار، وتقرير الذكاء الاصطناعي
                            processed_ad = enrich_ad_status(processed_ad)

                            # حفظ الإعلان المعتمد
                            with FILE_IO_LOCK:
                                pending = read_json_file(PENDING_FILE)
                                pending.append(processed_ad)
                                write_json_file(PENDING_FILE, pending)

                                all_ads = read_json_file(ALL_ADS_FILE)
                                all_ads.append(processed_ad)
                                write_json_file(ALL_ADS_FILE, all_ads)

                            group_ads_count += 1
                            with self.lock:
                                self.total_ads_collected += 1
                                self.active_tabs[tab_id]["ads_collected"] = group_ads_count
                                self.active_tabs[tab_id]["status"] = f"سحب ({group_ads_count}/{max_ads_per_group})"
                            last_ad_time = time.time()

                            cat_label = processed_ad.get('category_hierarchy') or processed_ad.get('category')
                            pub_name = processed_ad.get('publisher_name', 'معلن سوري')
                            self.log(f"[تبويب {tab_id+1}] 🟢 إعلان معتمد [{cat_label}]: {processed_ad.get('clean_title')} (المعلن: {pub_name} | هاتف: {primary_phone})")

                            if group_ads_count >= max_ads_per_group:
                                break

                        # فحص مهلة عدم النشاط للتخطي التلقائي
                        if (time.time() - last_ad_time) >= timeout_seconds:
                            self.log(f"[تبويب {tab_id+1}] ⏱️ مهلة عدم النشاط ({timeout_seconds} ثانية) انتهت للمجموعة [{group_idx}]. الانتقال للتالية...")
                            break

                        # التمرير الفعال المضمون (يعمل في كافة التبويبات المتزامنة والخلفية والنشطة)
                        try:
                            await page.evaluate("""() => {
                                window.scrollBy(0, 1600);
                                if (document.scrollingElement) {
                                    document.scrollingElement.scrollTop += 1600;
                                }
                                window.dispatchEvent(new Event('scroll'));
                            }""")
                            await page.mouse.wheel(0, 1600)
                        except Exception:
                            pass
                        await asyncio.sleep(random.uniform(0.8, 1.4))

                    with self.lock:
                        self.completed_groups_count += 1

                    self._update_group_scrape_history(group_url, group_ads_count)
                    self.log(f"[تبويب {tab_id+1}] ✔️ اكتملت المجموعة [{group_idx}]. الإعلانات المستخرجة: {group_ads_count}")
                    q.task_done()

                try:
                    await page.close()
                except Exception:
                    pass

            actual_tabs = min(concurrent_tabs, len(urls))
            self.log(f"⚡ جاري إطلاق {actual_tabs} تبويبات متزامنة في المتصفح...")
            await asyncio.gather(*[tab_worker(i) for i in range(actual_tabs)], return_exceptions=True)

            try:
                await context.close()
            except Exception:
                pass

        self.log(f"🎉 تم الانتهاء من كافة المهام! إجمالي الإعلانات الصالحة: {self.total_ads_collected}")

task_manager = ScrapingTaskManager()

# ==============================================================================
# واجهة الويب الشاملة (Unified 3-Pillar HTML Control Center)
# ==============================================================================
HTML_PAGE = r"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>لوحة التحكم المركزية وسحب الإعلانات 🇸🇾 | للبيع - Lelbai</title>
  <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800;900&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
  <style>
    :root {
      --primary: #2563eb;
      --primary-hover: #1d4ed8;
      --success: #10b981;
      --success-dark: #059669;
      --danger: #ef4444;
      --warning: #f59e0b;
      --purple: #8b5cf6;
      --bg: #0b1120;
      --card-bg: #1e293b;
      --card-inner: #0f172a;
      --border: #334155;
      --text: #f8fafc;
      --text-muted: #94a3b8;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Tajawal', sans-serif; }
    body { background: var(--bg); color: var(--text); padding: 20px; line-height: 1.6; }
    
    .navbar {
      display: flex; justify-content: space-between; align-items: center;
      background: var(--card-bg); padding: 16px 28px; border-radius: 16px;
      border: 1px solid var(--border); margin-bottom: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    .brand { font-size: 22px; font-weight: 900; color: #60a5fa; display: flex; align-items: center; gap: 10px; }
    
    .nav-tabs { display: flex; gap: 8px; flex-wrap: wrap; }
    .nav-btn {
      padding: 10px 18px; border-radius: 10px; border: 1px solid transparent;
      background: transparent; color: var(--text-muted); font-weight: 700; font-size: 14px;
      cursor: pointer; transition: all 0.2s; display: flex; align-items: center; gap: 8px;
    }
    .nav-btn.active { background: var(--primary); color: #fff; border-color: var(--primary); box-shadow: 0 4px 12px rgba(37,99,235,0.4); }
    .nav-btn:hover:not(.active) { background: #334155; color: #fff; }

    .tab-content { display: none; }
    .tab-content.active { display: block; }

    .card {
      background: var(--card-bg); border-radius: 16px; border: 1px solid var(--border);
      padding: 22px; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .card-title { font-size: 18px; font-weight: 800; color: #93c5fd; margin-bottom: 16px; display: flex; align-items: center; justify-content: space-between; }

    .form-group { margin-bottom: 14px; }
    .form-group label { display: block; font-size: 13px; font-weight: 700; color: var(--text-muted); margin-bottom: 6px; }
    .form-control {
      width: 100%; padding: 10px 14px; border-radius: 10px; background: var(--card-inner);
      border: 1px solid var(--border); color: #fff; font-size: 14px; outline: none; transition: 0.2s;
    }
    .form-control:focus { border-color: var(--primary); }
    textarea.form-control { resize: vertical; min-height: 90px; }

    .btn {
      padding: 10px 20px; border-radius: 10px; font-weight: 800; font-size: 14px;
      cursor: pointer; border: none; transition: all 0.2s; display: inline-flex; align-items: center; gap: 8px;
    }
    .btn-sm { padding: 6px 12px; font-size: 12px; border-radius: 8px; }
    .btn-primary { background: var(--primary); color: #fff; }
    .btn-primary:hover { background: var(--primary-hover); transform: translateY(-1px); }
    .btn-success { background: var(--success); color: #fff; }
    .btn-success:hover { background: var(--success-dark); transform: translateY(-1px); }
    .btn-danger { background: var(--danger); color: #fff; }
    .btn-danger:hover { background: #dc2626; }
    .btn-purple { background: var(--purple); color: #fff; }
    .btn-purple:hover { background: #7c3aed; }
    .btn-outline { background: transparent; border: 1px solid var(--border); color: #fff; }
    .btn-outline:hover { background: #334155; }

    /* Stats Grid */
    .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px; margin-bottom: 20px; }
    .stat-card {
      background: var(--card-inner); padding: 16px; border-radius: 14px; border: 1px solid var(--border);
      display: flex; align-items: center; gap: 15px;
    }
    .stat-icon {
      width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center;
      font-size: 22px; background: rgba(59, 130, 246, 0.15); color: #60a5fa;
    }
    .stat-info .val { font-size: 24px; font-weight: 900; color: #f8fafc; }
    .stat-info .lbl { font-size: 12px; font-weight: 700; color: var(--text-muted); }

    /* Groups Table */
    .table-container { overflow-x: auto; background: var(--card-inner); border-radius: 12px; border: 1px solid var(--border); }
    table { width: 100%; border-collapse: collapse; text-align: right; font-size: 13px; }
    th { background: #1e293b; color: #94a3b8; padding: 12px 16px; font-weight: 800; border-bottom: 1px solid var(--border); }
    td { padding: 12px 16px; border-bottom: 1px solid var(--border); vertical-align: middle; }
    tr:hover td { background: rgba(255,255,255,0.02); }
    .badge { padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 800; display: inline-flex; align-items: center; gap: 4px; }
    .badge-success { background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
    .badge-warning { background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
    .badge-info { background: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); }

    /* 3-Pillars Ad Card */
    .ads-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(420px, 1fr)); gap: 20px; }
    .ad-card {
      background: var(--card-bg); border-radius: 16px; border: 1px solid var(--border);
      overflow: hidden; display: flex; flex-direction: column; transition: all 0.2s;
    }
    .ad-card:hover { border-color: #60a5fa; box-shadow: 0 8px 25px rgba(0,0,0,0.4); }
    
    .ad-gallery { height: 230px; background: #000; position: relative; display: flex; align-items: center; justify-content: center; }
    .ad-gallery img { max-width: 100%; max-height: 100%; object-fit: contain; }
    .ad-thumbs {
      position: absolute; bottom: 0; left: 0; right: 0; display: flex; gap: 5px;
      padding: 6px; background: rgba(0,0,0,0.7); overflow-x: auto;
    }
    .ad-thumb-wrapper { position: relative; display: inline-block; flex-shrink: 0; }
    .ad-thumb { width: 42px; height: 42px; border-radius: 6px; object-fit: cover; cursor: pointer; border: 2px solid transparent; opacity: 0.7; }
    .ad-thumb.active { border-color: #38bdf8; opacity: 1; }
    .del-thumb-btn {
      position: absolute; top: -5px; right: -5px; width: 17px; height: 17px;
      border-radius: 50%; background: #ef4444; color: white; border: 1.5px solid #fff;
      font-size: 11px; font-weight: 900; line-height: 1; cursor: pointer;
      display: flex; align-items: center; justify-content: center; padding: 0;
      z-index: 10; box-shadow: 0 1px 4px rgba(0,0,0,0.6); transition: transform 0.15s, background 0.15s;
    }
    .del-thumb-btn:hover { background: #dc2626; transform: scale(1.2); }

    .ad-body { padding: 18px; display: flex; flex-direction: column; gap: 12px; flex: 1; }

    /* 3 Pillars Box */
    .verification-box {
      background: var(--card-inner); border-radius: 12px; border: 1px solid var(--border);
      padding: 12px; display: flex; flex-direction: column; gap: 8px;
    }
    .pillar-row {
      display: flex; justify-content: space-between; align-items: center; font-size: 12px; font-weight: 700;
      padding-bottom: 6px; border-bottom: 1px solid rgba(255,255,255,0.05);
    }
    .pillar-row:last-child { border-bottom: none; padding-bottom: 0; }
    .pillar-label { display: flex; align-items: center; gap: 6px; color: var(--text-muted); }

    .ad-title-input {
      background: var(--card-inner); border: 1px solid var(--border); color: #fff;
      padding: 8px 12px; border-radius: 8px; font-size: 15px; font-weight: 800; width: 100%;
    }
    .ad-desc-box {
      background: var(--card-inner); border: 1px solid var(--border); border-radius: 8px;
      padding: 10px; font-size: 12px; color: #cbd5e1; max-height: 100px; overflow-y: auto; white-space: pre-line;
    }

    .modal {
      display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.75);
      align-items: center; justify-content: center; z-index: 1000; padding: 20px;
    }
    .modal-content {
      background: var(--card-bg); border-radius: 16px; border: 1px solid var(--border);
      padding: 24px; width: 100%; max-width: 550px; display: flex; flex-direction: column; gap: 14px;
    }

    /* --- Ad Card Editable Inputs & Controls --- */
    .ad-edit-fields {
      display: flex;
      flex-direction: column;
      gap: 9px;
      background: rgba(15, 23, 42, 0.55);
      border: 1px solid rgba(255, 255, 255, 0.08);
      padding: 12px;
      border-radius: 12px;
      margin-top: 4px;
    }
    .ad-title-input {
      background: var(--card-inner); border: 1px solid var(--border); color: #fff;
      padding: 8px 12px; border-radius: 8px; font-size: 14px; font-weight: 800; width: 100%;
      transition: border-color 0.2s;
    }
    .ad-title-input:focus, .ad-desc-textarea:focus {
      border-color: #3b82f6; outline: none; box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
    }
    .ad-desc-textarea {
      background: var(--card-inner); border: 1px solid var(--border); border-radius: 8px;
      padding: 8px 12px; font-size: 12px; color: #cbd5e1; resize: vertical; line-height: 1.55; width: 100%;
      min-height: 80px; transition: border-color 0.2s; font-family: inherit;
    }
    .btn-category-select {
      background: rgba(37, 99, 235, 0.12);
      border: 1px solid rgba(59, 130, 246, 0.35);
      border-radius: 10px;
      padding: 8px 12px;
      color: #93c5fd;
      cursor: pointer;
      width: 100%;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 10px;
      transition: all 0.2s;
      text-align: right;
    }
    .btn-category-select:hover {
      background: rgba(37, 99, 235, 0.25);
      border-color: #60a5fa;
      color: #fff;
      transform: translateY(-1px);
    }
    .cat-pill-icon {
      width: 28px;
      height: 28px;
      border-radius: 6px;
      background: rgba(37, 99, 235, 0.3);
      color: #60a5fa;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 13px;
      flex-shrink: 0;
    }
    .cat-pill-text {
      font-weight: 800;
      font-size: 12px;
      text-align: right;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .cat-pill-badge {
      background: #2563eb;
      color: #fff;
      font-size: 10px;
      font-weight: 800;
      padding: 3px 8px;
      border-radius: 6px;
      flex-shrink: 0;
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }

    /* --- Category Picker Modal (2-Column Desktop Layout) --- */
    .modal-content-xl {
      max-width: 1250px;
      width: 95vw;
      max-height: 90vh;
      display: flex;
      flex-direction: column;
      padding: 0;
      border: 1px solid #3b82f6;
      box-shadow: 0 12px 50px rgba(0, 0, 0, 0.8);
      background: var(--card-bg);
      overflow: hidden;
    }
    .modal-header-custom {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 14px 22px;
      background: #0f172a;
      border-bottom: 1px solid var(--border);
    }
    .modal-icon-circle {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background: rgba(245, 158, 11, 0.2);
      color: #fbbf24;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 18px;
    }
    .modal-close-btn {
      background: transparent;
      border: none;
      color: var(--text-muted);
      font-size: 20px;
      cursor: pointer;
      padding: 4px 10px;
      border-radius: 8px;
      transition: all 0.15s;
    }
    .modal-close-btn:hover {
      background: rgba(239, 68, 68, 0.2);
      color: #ef4444;
    }
    .modal-body-split {
      display: grid;
      grid-template-columns: 1fr 380px;
      gap: 16px;
      padding: 16px;
      overflow-y: auto;
      flex: 1;
      background: rgba(15, 23, 42, 0.4);
    }
    @media (max-width: 992px) {
      .modal-body-split {
        grid-template-columns: 1fr;
      }
    }
    .picker-column-categories {
      background: var(--card-inner);
      border-radius: 12px;
      border: 1px solid var(--border);
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
      min-height: 480px;
    }
    .picker-column-reference {
      position: sticky;
      top: 0;
      height: 100%;
    }
    .picker-ref-card {
      background: var(--card-inner);
      border-radius: 12px;
      border: 1px solid var(--border);
      overflow: hidden;
      display: flex;
      flex-direction: column;
      height: 100%;
      box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    }
    .picker-ref-header {
      background: #0f172a;
      padding: 10px 14px;
      font-weight: 800;
      font-size: 12px;
      color: #f59e0b;
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .picker-ref-body {
      padding: 14px;
      display: flex;
      flex-direction: column;
      gap: 10px;
      overflow-y: auto;
      max-height: calc(85vh - 120px);
    }
    .picker-ref-img-wrapper {
      position: relative;
      height: 150px;
      background: #000;
      border-radius: 10px;
      overflow: hidden;
      cursor: pointer;
      border: 1px solid var(--border);
    }
    .picker-ref-img-wrapper img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
    .picker-ref-img-overlay {
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      background: rgba(0, 0, 0, 0.7);
      color: #38bdf8;
      font-size: 11px;
      font-weight: 700;
      padding: 4px 8px;
      text-align: center;
    }
    .picker-ref-item {
      background: rgba(30, 41, 59, 0.7);
      padding: 8px 10px;
      border-radius: 8px;
      border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .picker-ref-label {
      font-size: 10px;
      color: var(--text-muted);
      font-weight: 700;
      display: block;
      margin-bottom: 2px;
    }
    .picker-ref-val {
      font-size: 12px;
      word-break: break-word;
    }
    .picker-ref-desc {
      background: rgba(15, 23, 42, 0.9);
      padding: 8px 10px;
      border-radius: 6px;
      border: 1px solid rgba(255, 255, 255, 0.05);
      font-size: 11px;
      color: #cbd5e1;
      max-height: 130px;
      overflow-y: auto;
      white-space: pre-line;
      line-height: 1.5;
    }
    .picker-breadcrumbs-bar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }
    .picker-breadcrumbs {
      display: flex;
      align-items: center;
      gap: 6px;
      background: #0f172a;
      padding: 6px 14px;
      border-radius: 20px;
      border: 1px solid var(--border);
      font-size: 12px;
      flex-wrap: wrap;
    }
    .crumb-link {
      color: #60a5fa;
      text-decoration: none;
      font-weight: 700;
      cursor: pointer;
    }
    .crumb-link:hover {
      text-decoration: underline;
    }
    .crumb-sep {
      color: var(--text-muted);
      font-size: 10px;
    }
    .crumb-active {
      color: #f8fafc;
      font-weight: 800;
    }
    .picker-search-bar {
      display: flex;
      align-items: center;
      gap: 10px;
      background: #0f172a;
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 4px 12px;
    }
    .picker-search-bar input {
      background: transparent;
      border: none;
      color: #fff;
      font-size: 13px;
      padding: 6px 0;
      outline: none;
      flex: 1;
    }
    .category-tiles-container {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
      gap: 10px;
      overflow-y: auto;
      max-height: 480px;
      padding-right: 4px;
    }
    .category-tile {
      background: #0f172a;
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 12px 8px;
      text-align: center;
      cursor: pointer;
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 8px;
      position: relative;
    }
    .category-tile:hover {
      border-color: #3b82f6;
      background: rgba(37, 99, 235, 0.12);
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);
    }
    .category-tile.leaf-tile {
      border-color: rgba(16, 185, 129, 0.4);
    }
    .category-tile.leaf-tile:hover {
      border-color: #10b981;
      background: rgba(16, 185, 129, 0.15);
      box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25);
    }
    .cat-tile-icon {
      width: 44px;
      height: 44px;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border);
      padding: 4px;
      display: flex;
      align-items: center;
      justify-content: center;
      overflow: hidden;
    }
    .cat-tile-icon img {
      width: 100%;
      height: 100%;
      object-fit: contain;
    }
    .cat-tile-title {
      font-size: 12px;
      font-weight: 800;
      color: #f8fafc;
      line-height: 1.3;
      word-break: break-word;
    }
    .cat-tile-badge {
      font-size: 10px;
      padding: 2px 6px;
      border-radius: 4px;
      font-weight: 700;
    }
    .cat-tile-badge.badge-sub {
      background: rgba(59, 130, 246, 0.2);
      color: #60a5fa;
    }
    .cat-tile-badge.badge-leaf {
      background: rgba(16, 185, 129, 0.2);
      color: #34d399;
    }
    .modal-footer-custom {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 20px;
      background: #0f172a;
      border-top: 1px solid var(--border);
    }

  </style>
</head>
<body>

  <div class="navbar">
    <div class="brand">🚀 منصة إعلانات سوريا 🇸🇾 <span style="font-size:13px; color:var(--text-muted); font-weight:400;">(لوحة التحكم وسحب المجموعات والنشر)</span></div>
    <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap;">
      <!-- زر تشغيل لوحة الإدارة (المنجر) وكافة السيرفرات -->
      <button class="btn btn-primary btn-sm" id="btnLaunchManager" onclick="launchManager()" style="display:inline-flex; align-items:center; gap:8px; font-weight:800; padding:8px 16px; border-radius:10px; background:linear-gradient(135deg, #1d4ed8, #2563eb); border:1px solid #3b82f6; box-shadow:0 3px 12px rgba(37,99,235,0.35); cursor:pointer;" title="تشغيل وفتح لوحة تحكم الإدارة (المنجر) والسيرفرات">
        <span>🖥️ صفحة الإدارة (المنجر)</span>
        <span id="managerStatusDot" data-online="false" style="width:10px; height:10px; border-radius:50%; background:#ef4444; display:inline-block; box-shadow:0 0 6px #ef4444;" title="سيرفر الإدارة متوقف"></span>
      </button>

      <!-- شارة تاريخ آخر تحديث للنظام -->
      <div id="updateBadgeContainer" style="display:inline-flex; align-items:center; gap:6px; font-size:12px; background:rgba(255,255,255,0.06); padding:6px 12px; border-radius:10px; border:1px solid var(--border); color:var(--text-muted); cursor:pointer;" onclick="checkSystemUpdates()" title="انقر للتحقق من التحديثات من GitHub">
        <span>🔄 آخر تحديث:</span>
        <b id="lblLastUpdate" style="color:#60a5fa;">جاري الفحص...</b>
      </div>

      <!-- شارة حالة ورصيد الذكاء الاصطناعي (Gemini Vision) -->
      <div id="aiQuotaBadge" style="display:inline-flex; align-items:center; gap:8px; font-size:12px; font-weight:800; background:rgba(16,185,129,0.12); padding:6px 14px; border-radius:10px; border:1px solid #10b981; color:#34d399; cursor:pointer;" onclick="switchTab('tab-settings', document.getElementById('navBtnSettings'))" title="انقر لعرض تفاصيل الاستهلاك وإعدادات الذكاء الاصطناعي">
        <span id="aiStatusDot" style="width:8px; height:8px; border-radius:50%; background:#10b981; display:inline-block; box-shadow:0 0 6px #10b981;"></span>
        <span>🤖 فحص الصور:</span>
        <span id="aiCallsCounter" style="color:#67e8f9; font-weight:900;">المتبقي: 1,500 / 1,500</span>
      </div>

      <div id="serverStatusBadge" class="badge badge-warning" style="font-size:12px; padding:6px 14px; font-weight:700;">⏳ فحص الاتصال...</div>
      
      <div class="nav-tabs">
        <button class="nav-btn active" id="navBtnLinks" onclick="switchTab('tab-links', this)">🔗 إدارة الروابط وتاريخ السحب</button>
        <button class="nav-btn" id="navBtnScraper" onclick="switchTab('tab-scraper', this)">⚡ تشغيل السحب المتوازي</button>
        <button class="nav-btn" id="navBtnReview" onclick="switchTab('tab-review', this)">📦 مراجعة ونشر الإعلانات (<span id="badgePending">0</span>)</button>
        <button class="nav-btn" id="navBtnPublished" onclick="switchTab('tab-published', this)">✅ الإعلانات المنشورة (<span id="badgePublished">0</span>)</button>
        <button class="nav-btn" id="navBtnFlagged" onclick="switchTab('tab-flagged', this)" style="color:#f87171;">🚫 الإعلانات المحظورة (<span id="badgeFlagged">0</span>)</button>
        <button class="nav-btn" id="navBtnSettings" onclick="switchTab('tab-settings', this)">⚙️ الإعدادات والـ API</button>
      </div>
    </div>
  </div>

  <!-- تنبيه حالة السيرفر في حال فتح الملف كـ file:// أو السيرفر غير متصل -->
  <div id="serverAlertBanner" style="display:none; background:#450a0a; color:#fecaca; border:1px solid #dc2626; border-radius:14px; padding:16px 20px; margin-bottom:20px; box-shadow:0 4px 20px rgba(220,38,38,0.25); align-items:center; justify-content:space-between; flex-wrap:wrap; gap:14px;">
    <div style="display:flex; align-items:center; gap:14px;">
      <span style="font-size:28px;">⚠️</span>
      <div>
        <div style="font-weight:900; font-size:16px; color:#fee2e2;">سيرفر لوحة التحكم المحلي غير متصل (http://localhost:5000)</div>
        <div style="font-size:13px; color:#fca5a5; margin-top:2px;">
          لقد قمت بفتح صفحة الويب مباشرة دون تشغيل السيرفر. لتفعيل سحب الإعلانات وحفظ الروابط والتواصل مع الذكاء الاصطناعي، يرجى تشغيل <b>start_app.bat</b> أو <b>Lelbai_Control_Center.exe</b> أولاً.
        </div>
      </div>
    </div>
    <div style="display:flex; gap:10px; align-items:center; flex-wrap:wrap;">
      <a href="start_app.bat" download class="btn btn-success btn-sm" style="white-space:nowrap; padding:10px 18px; font-weight:800; text-decoration:none; display:inline-flex; align-items:center; gap:6px;">🚀 تشغيل السيرفر الآن (start_app.bat)</a>
      <button class="btn btn-warning btn-sm" onclick="checkServerConnection(true)" style="white-space:nowrap; padding:10px 18px; font-weight:800;">🔄 إعادة فحص الاتصال</button>
    </div>
  </div>

  <!-- الإحصائيات العلوية العامة -->
  <div class="stats-grid">
    <div class="stat-card" onclick="switchTab('tab-links', document.getElementById('navBtnLinks'))" style="cursor:pointer;" title="إدارة الروابط">
      <div class="stat-icon">🔗</div>
      <div class="stat-info"><div class="val" id="stTotalLinks">0</div><div class="lbl">إجمالي الروابط المحفوظة</div></div>
    </div>
    <div class="stat-card" onclick="switchTab('tab-review', document.getElementById('navBtnReview'))" style="cursor:pointer;" title="مراجعة الإعلانات الجاهزة">
      <div class="stat-icon" style="background:rgba(16,185,129,0.15); color:#34d399;">🚀</div>
      <div class="stat-info"><div class="val" id="stReadyAds" style="color:#34d399;">0</div><div class="lbl">إعلانات جاهزة للنشر الفوري</div></div>
    </div>
    <div class="stat-card" onclick="switchTab('tab-settings', document.getElementById('navBtnSettings'))" style="cursor:pointer;" title="رصيد فحص الذكاء الاصطناعي اليومي">
      <div class="stat-icon" style="background:rgba(56,189,248,0.15); color:#38bdf8;">🤖</div>
      <div class="stat-info"><div class="val" id="stAiRemaining" style="color:#38bdf8;">1,500</div><div class="lbl">متبقي فحص ذكاء اصطناعي اليوم</div></div>
    </div>
    <div class="stat-card" onclick="switchTab('tab-published', document.getElementById('navBtnPublished'))" style="cursor:pointer;" title="عرض قائمة الإعلانات المنشورة">
      <div class="stat-icon" style="background:rgba(139,92,246,0.15); color:#a78bfa;">✔️</div>
      <div class="stat-info"><div class="val" id="stPublishedAds" style="color:#a78bfa;">0</div><div class="lbl">إعلانات تم نشرها للموقع</div></div>
    </div>
    <div class="stat-card" onclick="switchTab('tab-flagged', document.getElementById('navBtnFlagged'))" style="cursor:pointer; border-color:rgba(239,68,68,0.3);" title="انقر لعرض قائمة الإعلانات المحظورة وأسباب الحظر">
      <div class="stat-icon" style="background:rgba(239,68,68,0.15); color:#f87171;">🚫</div>
      <div class="stat-info"><div class="val" id="stFlaggedAds" style="color:#f87171;">0</div><div class="lbl">إعلانات مخالفة تم استبعادها</div></div>
    </div>
  </div>

  <!-- تبويب 1: إدارة الروابط وتاريخ السحب -->
  <div class="tab-content active" id="tab-links">
    <div class="card">
      <div class="card-title" style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
        <span>📋 قائمة الروابط المحفوظة ومتابعة آخر عمليات السحب</span>
        <div style="display:flex; gap:8px; flex-wrap:wrap;">
          <button class="btn btn-danger btn-sm" onclick="clearAllGroups()" style="background:#ef4444;" title="مسح كافة الروابط المحفوظة">🗑️ تفريغ كافة الروابط</button>
          <button class="btn btn-info btn-sm" onclick="loadStarterGroups()" style="background:#0ea5e9;" title="استيراد قائمة روابط مقترحة لمجموعات سورية نشطة">📥 استيراد روابط مقترحة</button>
          <button class="btn btn-primary btn-sm" onclick="openAddGroupModal()">➕ إضافة رابط جديد</button>
        </div>
      </div>

      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>اسم المجموعة / الرابط</th>
              <th>القسم</th>
              <th>🕒 آخر مرة سحبت منه</th>
              <th>📊 آخر سحب</th>
              <th>إجمالي الإعلانات</th>
              <th>الحالة</th>
              <th>إجراءات</th>
            </tr>
          </thead>
          <tbody id="groupsTableBody">
            <!-- يتم الملء عبر JavaScript -->
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- تبويب 2: تشغيل السحب المتوازي والمتابعة -->
  <div class="tab-content" id="tab-scraper">
    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:20px;">
      
      <div class="card">
        <div class="card-title">⚡ بدء السحب المتوازي السريع</div>
        
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:12px;">
          <div class="form-group">
            <label>⚡ عدد التبويبات المتزامنة (1 إلى 5):</label>
            <input type="number" class="form-control" id="inpConcurrent" value="4" min="1" max="5">
          </div>
          <div class="form-group">
            <label>🎯 المطلوب من كل مجموعة:</label>
            <input type="number" class="form-control" id="inpMaxAds" value="100" min="5" max="500">
          </div>
        </div>

        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:12px;">
          <div class="form-group">
            <label>⏱️ مهلة الانتظار قبل التخطي (ثانية):</label>
            <input type="number" class="form-control" id="inpTimeout" value="60" min="40" max="300">
          </div>
          <div class="form-group">
            <label>📁 مجلد استيراد الموقع:</label>
            <input type="text" class="form-control" id="inpImportDir" value="" placeholder="تلقائي: سطح المكتب \ إعلانات_للاستيراد (أو اختر مساراً مخصصاً)">
          </div>
        </div>

        <div class="form-group" style="margin-top:14px; background:rgba(255,255,255,0.03); border:1px solid var(--border); border-radius:12px; padding:12px 14px;">
          <label style="font-weight:700; color:#60a5fa; display:flex; align-items:center; gap:6px; margin-bottom:6px;">
            <span>🎯 نقطة انطلاق السحب:</span>
          </label>
          <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px;">
            <select class="form-control" id="scrapeStartMode" onchange="updateScrapeStartPreview()">
              <option value="smart">🌟 تلقائي ذكي: من آخر صفحة انضافت أو سُحبت (موصى به)</option>
              <option value="last_added">🆕 من آخر صفحة انضافت أولاً</option>
              <option value="last_scraped">🕒 من آخر صفحة تم السحب منها</option>
              <option value="first">🔢 من أول صفحة بالقائمة</option>
              <option value="custom">📌 اختيار صفحة محددة للبدء منها...</option>
            </select>
            <select class="form-control" id="scrapeCustomGroupSelect" onchange="updateScrapeStartPreview()" style="display:none;">
              <!-- يتم الملء ديناميكياً عبر JavaScript -->
            </select>
          </div>
          <div id="scrapeStartInfoBox" style="font-size:12px; margin-top:8px; color:#38bdf8; font-weight:700; display:flex; align-items:center; gap:6px; flex-wrap:wrap;">
            <span>🚀 سيبدأ السحب من:</span>
            <span id="scrapeStartGroupName" style="color:#4ade80;">جاري التحميل...</span>
          </div>
        </div>

        <div style="display:flex; gap:10px; margin-top:15px;">
          <button class="btn btn-success" id="btnStartScraping" onclick="startAllScraping()">🚀 تشغيل السحب لكافة المجموعات</button>
          <button class="btn btn-danger" id="btnStopScraping" onclick="stopAllScraping()" style="display:none;">⏹️ إيقاف السحب</button>
          <button class="btn btn-outline" onclick="openLoginBrowser()">🔐 تسجيل دخول فيسبوك</button>
        </div>
      </div>

      <div class="card">
        <div class="card-title">📊 حالة التبويبات والسجلات الحية</div>
        <div id="activeTabsLiveList" style="display:flex; flex-direction:column; gap:8px; margin-bottom:12px;">
          <div style="font-size:12px; color:var(--text-muted); text-align:center; padding:10px;">لا توجد تبويبات نشطة حالياً</div>
        </div>
        <div id="liveLogsContainer" style="background:#000; color:#4ade80; font-family:monospace; padding:10px; border-radius:8px; height:150px; overflow-y:auto; font-size:11px;">جاهز لبدء السحب...</div>
      </div>

    </div>
  </div>

  <!-- تبويب 3: مراجعة ونشر الإعلانات (المراحل الثلاث) -->
  <div class="tab-content" id="tab-review">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; flex-wrap:wrap; gap:12px;">
      <div style="display:flex; gap:10px; align-items:center;">
        <span style="font-weight:800; color:#60a5fa;">تصفية الإعلانات:</span>
        <button class="btn btn-sm btn-outline active" onclick="filterAds('all', this)">الكل</button>
        <button class="btn btn-sm btn-outline" onclick="filterAds('ready', this)">🚀 الجاهز للنشر فقط</button>
        <button class="btn btn-sm btn-outline" onclick="filterAds('review', this)">⚠️ بحاجة لمراجعة</button>
      </div>
      <div style="display:flex; gap:10px; flex-wrap:wrap;">
        <button class="btn btn-outline" style="border-color:#38bdf8; color:#38bdf8; font-weight:800;" onclick="reclassifyAllAdsWithAi()" title="إعادة الفحص والتصنيف الكامل لكافة الإعلانات عبر Gemini AI">🤖 فحص الكل بالذكاء الاصطناعي</button>
        <button class="btn btn-danger" onclick="clearAllPendingAds()" style="background:#ef4444;" title="مسح وتفريغ كافة الإعلانات غير المنشورة وصورها دفعة واحدة">🗑️ تفريغ كافة الإعلانات</button>
        <button class="btn btn-success" onclick="bulkPublishReady()">⚡ نشر كافة الإعلانات الجاهزة لمجلد الاستيراد</button>
        <button class="btn btn-outline" onclick="loadAllAds()">🔄 تحديث</button>
      </div>
    </div>

    <div class="ads-grid" id="adsCardsGrid">
      <!-- يتم عرض بطاقات الإعلانات بالمراحل الثلاث عبر JavaScript -->
    </div>
  </div>

  <!-- تبويب 4: قائمة الإعلانات المنشورة في قائمة لوحدها -->
  <div class="tab-content" id="tab-published">
    <div class="card" style="margin-bottom:20px;">
      <div class="card-title" style="flex-wrap:wrap; gap:12px;">
        <div style="display:flex; align-items:center; gap:10px;">
          <span>✅ سجل الإعلانات التي تم نشرها وتصديرها (<span id="publishedListCount" style="color:#a78bfa; font-weight:900;">0</span> إعلان)</span>
        </div>
        <div style="display:flex; gap:10px; flex-wrap:wrap;">
          <button class="btn btn-danger btn-sm" onclick="clearPublishedAds()" style="background:#ef4444;" title="مسح وتفريغ سجل الإعلانات المنشورة">🗑️ تفريغ سجل المنشورات</button>
          <button class="btn btn-primary btn-sm" onclick="openImportFolder()">📂 فتح مجلد إعلانات_للاستيراد</button>
          <button class="btn btn-outline btn-sm" onclick="loadPublishedAds()">🔄 تحديث القائمة</button>
        </div>
      </div>

      <!-- شريط البحث والتصفية -->
      <div style="display:flex; gap:12px; margin-top:14px; flex-wrap:wrap; align-items:center;">
        <div style="flex:1; min-width:260px;">
          <input type="text" class="form-control" id="searchPublishedInput" placeholder="🔍 ابحث في الإعلانات المنشورة (العنوان، الهاتف، اسم المعلن، المدينة، القسم...)" oninput="filterPublishedAds()" />
        </div>
        <div style="width:220px;">
          <select class="form-control" id="filterPublishedCat" onchange="filterPublishedAds()">
            <option value="">جميع الأقسام</option>
            <option value="سيارات">السيارات والدراجات</option>
            <option value="عقارات">العقارات</option>
            <option value="قطع غيار">قطع الغيار والإكسسوارات</option>
            <option value="إلكترونيات">الموبايلات والإلكترونيات</option>
            <option value="طاقة">الطاقة والكهرباء</option>
            <option value="أثاث">الأثاث والمنزل</option>
            <option value="عام">أخرى / عام</option>
          </select>
        </div>
      </div>
    </div>

    <div class="ads-grid" id="publishedCardsGrid">
      <!-- يتم عرض بطاقات الإعلانات المنشورة عبر JavaScript -->
    </div>
  </div>

  <!-- تبويب: قائمة الإعلانات المحظورة والمستبعدة وأسباب الحظر -->
  <div class="tab-content" id="tab-flagged">
    <div class="card" style="margin-bottom:20px;">
      <div class="card-title" style="flex-wrap:wrap; gap:12px;">
        <div style="display:flex; align-items:center; gap:10px;">
          <span>🚫 سجل الإعلانات المحظورة والمستبعدة بالذكاء الاصطناعي (<span id="flaggedListCount" style="color:#f87171; font-weight:900;">0</span> إعلان)</span>
        </div>
        <div style="display:flex; gap:10px; flex-wrap:wrap;">
          <button class="btn btn-danger btn-sm" onclick="clearFlaggedAds()" style="background:#ef4444;" title="مسح وتفريغ سجل الإعلانات المحظورة بالكامل">🗑️ تفريغ كافة الإعلانات المحظورة</button>
          <button class="btn btn-outline btn-sm" onclick="loadFlaggedAds()">🔄 تحديث القائمة</button>
        </div>
      </div>

      <div style="background:rgba(239,68,68,0.1); border:1px solid rgba(239,68,68,0.3); border-radius:10px; padding:12px; margin-top:12px; color:#fca5a5; font-size:13px; display:flex; align-items:center; gap:10px;">
        <span style="font-size:24px;">🛡️</span>
        <div>
          <b>نظام الرقابة الآلي والشرعي (Gemini Vision Cloud API):</b>
          يتم استبعاد أي إعلان يحتوي على صور نساء، أسلحة، وثائق شخصية، سلع محظورة، أو حسابات ألعاب. يظهر لك أدناه كل إعلان تم استبعاده مع <b>سبب الحظر الدقيق</b> الصادر من الذكاء الاصطناعي، ويمكنك إلغاء الحظر ونقله للمراجعة إذا كان مستبعداً بالخطأ.
        </div>
      </div>
    </div>

    <div class="ads-grid" id="flaggedCardsGrid">
      <!-- يتم عرض بطاقات الإعلانات المحظورة عبر JavaScript -->
    </div>
  </div>

  <!-- تبويب: الإعدادات والتحكم بالبيانات -->
  <div class="tab-content" id="tab-settings">
    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:20px; max-width:1200px; margin:0 auto;">
      
      <!-- كارت 1: رصيد ونماذج الذكاء الاصطناعي وفحص الصور -->
      <div class="card" style="margin:0;">
        <div class="card-title" style="display:flex; justify-content:space-between; align-items:center;">
          <span>🤖 رصيد الذكاء الاصطناعي وقدرات النماذج</span>
          <button class="btn btn-outline btn-sm" onclick="fetchAiQuotaInfo(true)" title="تحديث قراءة العداد">🔄 تحديث الرصيد</button>
        </div>

        <div style="background:rgba(56,189,248,0.1); border:1px solid rgba(56,189,248,0.3); border-radius:12px; padding:14px; margin-bottom:14px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <span style="font-weight:800; color:#38bdf8; font-size:14px;">📊 الرصيد اليومي الفعلي (Gemini Flash Vision):</span>
            <span id="aiModelBadgeStatus" class="badge badge-success" style="font-size:11px;">متصل ونشط 🟢</span>
          </div>
          <div style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap:8px; text-align:center;">
            <div style="background:rgba(15,23,42,0.6); padding:8px; border-radius:8px; border:1px solid rgba(255,255,255,0.05);">
              <div style="font-size:18px; font-weight:900; color:#34d399;" id="aiRemainingBox">1,500</div>
              <div style="font-size:11px; color:var(--text-muted);">المتبقي اليوم</div>
            </div>
            <div style="background:rgba(15,23,42,0.6); padding:8px; border-radius:8px; border:1px solid rgba(255,255,255,0.05);">
              <div style="font-size:18px; font-weight:900; color:#60a5fa;" id="aiUsedBox">0</div>
              <div style="font-size:11px; color:var(--text-muted);">المستهلك اليوم</div>
            </div>
            <div style="background:rgba(15,23,42,0.6); padding:8px; border-radius:8px; border:1px solid rgba(255,255,255,0.05);">
              <div style="font-size:18px; font-weight:900; color:#cbd5e1;">1,500 / يوم</div>
              <div style="font-size:11px; color:var(--text-muted);">الحد الأقصى اليومي</div>
            </div>
          </div>
          <div style="font-size:11px; color:#94a3b8; margin-top:8px; text-align:center;">
            سرعة الاستدعاء المسموحة: <b>15 طلب / دقيقة (RPM)</b> | يتجدد الرصيد مجاناً كل 24 ساعة
          </div>
        </div>

        <div style="font-weight:800; font-size:13px; color:#f8fafc; margin-bottom:8px;">
          ❓ هل جميع النماذج تفحص الصور؟
        </div>
        <div style="font-size:12px; color:#cbd5e1; background:rgba(16,185,129,0.08); border:1px solid rgba(16,185,129,0.25); border-radius:10px; padding:10px; margin-bottom:14px; line-height:1.5;">
          <b>نعم بالتأكيد!</b> جميع النماذج المعتمدة أدناه مزودة بقدرات الرؤية البصرية (Vision) لفحص صور الإعلانات بدقة متناهية واستبعاد الصور المحظورة (النساء، الوثائق، الأسلحة) وهيكلة بيانات الإعلان:
        </div>

        <div style="display:flex; flex-direction:column; gap:8px;" id="aiModelsTableContainer">
          <div style="background:rgba(15,23,42,0.8); border:1px solid #10b981; border-radius:10px; padding:10px; display:flex; justify-content:space-between; align-items:center;">
            <div>
              <div style="font-weight:800; color:#34d399; font-size:13px;">⚡ gemini-flash-latest (النموذج الافتراضي المعتمد)</div>
              <div style="font-size:11px; color:var(--text-muted);">فحص صور + نصوص فائق السرعة والدقة | 1,500 طلب/يوم | 15 RPM</div>
            </div>
            <span class="badge badge-success">نشط ومعتمد تلقائياً 🟢</span>
          </div>

          <div style="background:rgba(15,23,42,0.5); border:1px solid rgba(255,255,255,0.08); border-radius:10px; padding:10px; display:flex; justify-content:space-between; align-items:center;">
            <div>
              <div style="font-weight:800; color:#60a5fa; font-size:13px;">⚡ gemini-3.8-flash</div>
              <div style="font-size:11px; color:var(--text-muted);">فحص صور + نصوص تجريبي | 1,500 طلب/يوم | 15 RPM</div>
            </div>
            <span class="badge badge-info">مدعوم واحتياطي ✅</span>
          </div>

          <div style="background:rgba(15,23,42,0.5); border:1px solid rgba(255,255,255,0.08); border-radius:10px; padding:10px; display:flex; justify-content:space-between; align-items:center;">
            <div>
              <div style="font-weight:800; color:#a78bfa; font-size:13px;">🧠 gemini-pro-latest</div>
              <div style="font-size:11px; color:var(--text-muted);">أعلى دقة تفكير واستنتاج للمحتوى والسلع الحساسة | 50 طلب/يوم</div>
            </div>
            <span class="badge badge-warning">مدعوم (حد 50 يومياً) ⚠️</span>
          </div>

          <div style="background:rgba(15,23,42,0.5); border:1px solid rgba(255,255,255,0.08); border-radius:10px; padding:10px; display:flex; justify-content:space-between; align-items:center;">
            <div>
              <div style="font-weight:800; color:#38bdf8; font-size:13px;">🤖 Gemini Vision API (فحص الصور السحابي)</div>
              <div style="font-size:11px; color:var(--text-muted);">فحص صور الإعلانات وكشف المحظورات والتعري والنساء والوثائق عبر السحاب | 1500 طلب/يوم</div>
            </div>
            <span class="badge badge-success">نشط ومعتمد 🟢</span>
          </div>
        </div>
      </div>

      <!-- العمود الثاني: الإعدادات والربط + إدارة وحذف البيانات -->
      <div style="display:flex; flex-direction:column; gap:20px;">
        
        <!-- كارت 2: الإعدادات والربط الآلي -->
        <div class="card" style="margin:0;">
          <div class="card-title">⚙️ الإعدادات ومفاتيح الربط</div>

          <div class="form-group">
            <label>رابط API الموقع (مدمج وجاهز):</label>
            <input type="text" class="form-control" id="setWebUrl" placeholder="https://api.lelbai.com/public/api/listings" readonly style="background:rgba(255,255,255,0.03); color:var(--text-muted);">
          </div>

          <div class="form-group">
            <label>مفتاح توثيق الموقع (مدمج وموثق مسبقاً):</label>
            <input type="password" class="form-control" id="setWebKey" value="●●●●●●●●●●●●●●●●" readonly style="background:rgba(255,255,255,0.03); color:var(--text-muted);">
          </div>

          <div class="form-group">
            <label>مفتاح Google Gemini API (مدمج تلقائياً ويعمل على أي جهاز):</label>
            <input type="password" class="form-control" id="setGeminiKey" placeholder="مفتاح الذكاء الاصطناعي مدمج ويعمل تلقائياً">
            <div style="font-size:11px; color:var(--text-muted); margin-top:4px;">
              المفتاح مدمج ومفعل افتراضياً. يمكنك تغييره بمفتاحك الخاص من <a href="https://aistudio.google.com/app/apikey" target="_blank" style="color:#60a5fa; text-decoration:underline;">Google AI Studio</a>.
            </div>
          </div>

          <div class="form-group">
            <label>🖥️ رابط صفحة المنجر (لوحة الإدارة):</label>
            <input type="text" class="form-control" id="setManagerUrl" placeholder="http://localhost:8002">
            <div style="font-size:11px; color:#93c5fd; margin-top:4px; line-height:1.4;">
              💡 <b>إذا كنت على الكمبيوتر الثاني:</b> ضع هنا عنوان IP الكمبيوتر الأول (مثال: <code>http://192.168.1.229:8002</code>) ليفتح المنجر مباشرة عبر الشبكة دون الحاجة لتثبيت أي ملفات على هذا الجهاز.
            </div>
          </div>

          <button class="btn btn-primary" onclick="saveSettings()">💾 حفظ الإعدادات</button>
        </div>

        <!-- كارت 3: إدارة ومسح البيانات وتصفير المنظومة -->
        <div class="card" style="margin:0; border:1px solid rgba(239,68,68,0.3);">
          <div class="card-title" style="color:#f87171;">
            <span>🗑️ إدارة وتفريغ البيانات (مسح مخصص وتصفير)</span>
          </div>
          <div style="font-size:12px; color:var(--text-muted); margin-bottom:12px;">
            يمكنك مسح وتفريغ أي قسم تريده بشكل منفصل أو إعادة ضبط المنظومة بالكامل:
          </div>

          <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px;">
            <button class="btn btn-danger btn-sm" onclick="clearAllPendingAds()" style="background:#dc2626;" title="مسح كافة الإعلانات غير المنشورة وصورها">
              🗑️ مسح مسودات الإعلانات
            </button>
            <button class="btn btn-danger btn-sm" onclick="clearPublishedAds()" style="background:#dc2626;" title="مسح سجل الإعلانات المنشورة">
              🗑️ مسح سجل المنشورات
            </button>
            <button class="btn btn-warning btn-sm" onclick="clearFlaggedAds()" title="مسح سجل الإعلانات المستبعدة">
              🚫 مسح الإعلانات المخالفة
            </button>
            <button class="btn btn-warning btn-sm" onclick="clearAllImages()" title="تنظيف كافة الصور المحملة من القرص">
              🖼️ تنظيف كافة الصور من القرص
            </button>
            <button class="btn btn-danger btn-sm" onclick="clearAllGroups()" style="background:#b91c1c;" title="مسح كافة روابط المجموعات المحفوظة">
              🔗 تفريغ كافة الروابط
            </button>
            <button class="btn btn-info btn-sm" onclick="loadStarterGroups()" style="background:#0284c7;" title="استيراد روابط لمجموعات سورية نشطة">
              📥 استيراد روابط مقترحة
            </button>
          </div>

          <div style="margin-top:14px; padding-top:12px; border-top:1px solid rgba(255,255,255,0.08); text-align:center;">
            <button class="btn btn-danger" onclick="resetAllSystemData()" style="width:100%; background:#991b1b; padding:10px; font-weight:800;" title="مسح كافة البيانات والصور وإعادة المنظومة كأنها نزلت الآن">
              ⚠️ تصفير المنظومة بالكامل (إعادة ضبط المصنع)
            </button>
          </div>
        </div>

      </div>

    </div>
  </div>

  <!-- Modal إضافة مجموعة -->
  <div class="modal" id="addGroupModal">
    <div class="modal-content">
      <div style="font-size:18px; font-weight:800; color:#60a5fa;">➕ إضافة رابط سحب جديد</div>
      
      <div class="form-group">
        <label>اسم المجموعة / الصفحة:</label>
        <input type="text" class="form-control" id="mGrpName" placeholder="مثال: سوق سيارات دمشق">
      </div>

      <div class="form-group">
        <label>رابط المجموعة (فيسبوك):</label>
        <input type="text" class="form-control" id="mGrpUrl" placeholder="https://www.facebook.com/groups/...">
      </div>

      <div class="form-group">
        <label>القسم / التصنيف:</label>
        <select class="form-control" id="mGrpCat">
          <option value="السيارات">السيارات والدراجات</option>
          <option value="العقارات">العقارات</option>
          <option value="الموبايلات والإلكترونيات">الموبايلات والإلكترونيات</option>
          <option value="الطاقة البديلة">الطاقة البديلة والكهرباء</option>
          <option value="الأثاث والمنزل">الأثاث والمنزل</option>
          <option value="المواشي والحيوانات">المواشي والحيوانات</option>
          <option value="الوظائف والخدمات">الوظائف والخدمات</option>
          <option value="عام">أخرى / عام</option>
        </select>
      </div>

      <div style="display:flex; justify-content:flex-end; gap:10px; margin-top:10px;">
        <button class="btn btn-outline" onclick="closeAddGroupModal()">إلغاء</button>
        <button class="btn btn-primary" onclick="saveNewGroup()">حفظ الرابط</button>
      </div>
    </div>
  </div>


  <!-- Modal اختيار وتصفح القسم الهرمي التفاعلي مع كرت معلومات الإعلان (Category Picker with Reference Card) -->
  <div class="modal" id="categoryPickerModal" style="display:none; z-index:1070;">
    <div class="modal-content modal-content-xl">
      <!-- رأس البوب اب -->
      <div class="modal-header-custom">
        <div style="display:flex; align-items:center; gap:12px;">
          <div class="modal-icon-circle"><i class="fa-solid fa-layer-group"></i></div>
          <div>
            <div style="display:flex; align-items:center; gap:8px;">
              <h3 style="font-size:17px; font-weight:900; color:#fff; margin:0;">اختيار وتحديد تصنيف الإعلان</h3>
              <span class="badge" style="background:#f59e0b; color:#000; font-weight:900;" id="pickerAdIdBadge">#</span>
            </div>
            <div style="font-size:12px; color:var(--text-muted); margin-top:2px;" id="pickerAdTitleBadge">اختر وتصفح القسم المناسب لمواصفات وتفاصيل هذا الإعلان</div>
          </div>
        </div>
        <button type="button" class="modal-close-btn" onclick="closeCategoryPickerModal()" title="إغلاق">✕</button>
      </div>

      <!-- جسم البوب اب: عمودين (النصف: متصفح الأصناف، اليسار: مواصفات الإعلان للمطابقة) -->
      <div class="modal-body-split">
        
        <!-- العمود الأيمن / النصف: متصفح وشبكة الأقسام الهرمية (Category Explorer) -->
        <div class="picker-column-categories">
          
          <!-- شريط المسار والرجوع Breadcrumbs -->
          <div class="picker-breadcrumbs-bar">
            <div class="picker-breadcrumbs" id="categoryPickerBreadcrumbs">
              <span class="crumb-link" onclick="goToPickerBreadcrumb(-1)"><i class="fa-solid fa-house"></i> الرئيسية</span>
            </div>
            <button type="button" class="btn btn-sm btn-outline" id="btnPickerBack" style="display:none;" onclick="navigatePickerBack()">
              <i class="fa-solid fa-arrow-right"></i> رجوع للخلف
            </button>
          </div>

          <!-- شريط البحث السريع في الأقسام -->
          <div class="picker-search-bar">
            <span style="color:var(--text-muted);"><i class="fa-solid fa-magnifying-glass"></i></span>
            <input type="text" id="categoryPickerSearch" placeholder="ابحث عن أي قسم بسرعة (مثال: سيراتو، كيا، شقق، كنبايات، طاقة...)" oninput="filterCategoryPicker(this.value)" />
            <button type="button" class="btn btn-sm btn-outline" onclick="clearPickerSearch()" title="مسح البحث">✕</button>
          </div>

          <!-- زر اعتماد القسم الأب الحالي إذا أراد المستخدم التوقف عنده -->
          <div id="pickerCurrentParentAction" style="display:none;"></div>

          <!-- شبكة كروت الأقسام المعروضة -->
          <div class="category-tiles-container" id="categoryPickerGrid">
            <!-- تُولد بطاقات الأقسام هنا ديناميكياً -->
          </div>

          <div id="categoryPickerEmpty" style="display:none; text-align:center; padding:40px; color:var(--text-muted);">
            <div style="font-size:32px; margin-bottom:8px;">📂</div>
            <div style="font-weight:800; font-size:14px; color:#f8fafc;">لم يتم العثور على أي قسم مطابق لكلمة البحث</div>
          </div>

        </div>

        <!-- العمود الأيسر: كرت معلومات ومواصفات الإعلان للمطابقة والتذكر (Ad Reference Card) -->
        <div class="picker-column-reference">
          <div class="picker-ref-card">
            <div class="picker-ref-header">
              <span>📋 بطاقة تفاصيل الإعلان (للمطابقة والتذكر)</span>
            </div>
            <div class="picker-ref-body">
              
              <!-- صورة الإعلان المرجعية (قابلة للنقر للتكبير) -->
              <div class="picker-ref-img-wrapper" onclick="openLightboxFromPickerRef()" title="انقر لتكبير ومعاينة الصورة">
                <img id="pickerRefImage" src="" alt="صورة الإعلان" onerror="this.src='https://placehold.co/400x250/1e293b/f8fafc?text=No+Image'" />
                <div class="picker-ref-img-overlay">
                  <span>🔍 انقر لتكبير ومعاينة الصورة</span>
                </div>
              </div>

              <!-- العنوان -->
              <div class="picker-ref-item">
                <span class="picker-ref-label">العنوان المسجل:</span>
                <div class="picker-ref-val" id="pickerRefTitle" style="color:#60a5fa; font-weight:800;"></div>
              </div>

              <!-- القسم المسجل حالياً -->
              <div class="picker-ref-item">
                <span class="picker-ref-label">القسم المسجل حالياً:</span>
                <div class="picker-ref-val" id="pickerRefCategory" style="color:#a78bfa; font-weight:800;"></div>
              </div>

              <!-- السعر والمدينة -->
              <div style="display:grid; grid-template-columns: 1fr 1fr; gap:6px;">
                <div class="picker-ref-item">
                  <span class="picker-ref-label">السعر:</span>
                  <div class="picker-ref-val" id="pickerRefPrice" style="color:#34d399; font-weight:800;"></div>
                </div>
                <div class="picker-ref-item">
                  <span class="picker-ref-label">المدينة:</span>
                  <div class="picker-ref-val" id="pickerRefCity" style="color:#fde047; font-weight:800;"></div>
                </div>
              </div>

              <!-- المعلن والهاتف -->
              <div style="display:grid; grid-template-columns: 1fr 1fr; gap:6px;">
                <div class="picker-ref-item">
                  <span class="picker-ref-label">المعلن:</span>
                  <div class="picker-ref-val" id="pickerRefUser" style="color:#cbd5e1;"></div>
                </div>
                <div class="picker-ref-item">
                  <span class="picker-ref-label">الهاتف:</span>
                  <div class="picker-ref-val" id="pickerRefPhone" style="color:#38bdf8; font-weight:800;" dir="ltr"></div>
                </div>
              </div>

              <!-- بادجات المواصفات المستخرجة إن وجدت -->
              <div id="pickerRefSpecsBadges" style="display:flex; flex-wrap:wrap; gap:4px;"></div>

              <!-- الوصف الأصلي الكامل (أهم جزء لتحديد القسم وتذكر الإعلان!) -->
              <div class="picker-ref-item" style="flex:1; display:flex; flex-direction:column;">
                <span class="picker-ref-label">وصف ومواصفات الإعلان (اقرأه لاختيار وتذكر القسم):</span>
                <div class="picker-ref-desc" id="pickerRefDescription"></div>
              </div>

              <!-- رابط المعاينة في فيسبوك -->
              <div style="margin-top:auto; padding-top:6px;">
                <a id="pickerRefLiveUrl" href="#" target="_blank" class="btn btn-outline btn-sm" style="width:100%; justify-content:center; font-size:11px; text-decoration:none;">
                  🔗 فتح رابط الإعلان الأصلي في فيسبوك
                </a>
              </div>

            </div>
          </div>
        </div>

      </div>

      <!-- تذييل البوب اب -->
      <div class="modal-footer-custom">
        <div style="font-size:12px; color:var(--text-muted); display:flex; align-items:center; gap:6px;">
          <span style="color:#38bdf8;">💡</span>
          <span>النقر على أصغر قسم فرعي (أصغر ابن) يقوم باختياره وتثبيته فورياً في الإعلان.</span>
        </div>
        <button type="button" class="btn btn-outline btn-sm" onclick="closeCategoryPickerModal()">إغلاق بدون تغيير</button>
      </div>

    </div>
  </div>

  <!-- Lightbox Modal تكبير الصور -->
  <div class="modal" id="imageLightboxModal" style="display:none; z-index:2000;" onclick="closeImageLightbox()">
    <div style="max-width:90vw; max-height:90vh; display:flex; flex-direction:column; align-items:center; position:relative;" onclick="event.stopPropagation()">
      <button type="button" onclick="closeImageLightbox()" style="position:absolute; top:-40px; right:0; background:#ef4444; color:#fff; border:none; border-radius:50%; width:32px; height:32px; font-weight:900; font-size:16px; cursor:pointer;" title="إغلاق">✕</button>
      <img id="lightboxImg" src="" style="max-width:90vw; max-height:80vh; object-fit:contain; border-radius:12px; box-shadow:0 10px 40px rgba(0,0,0,0.8); border:1px solid var(--border);" />
      <div id="lightboxTitle" style="color:#fff; font-weight:800; margin-top:10px; font-size:14px; text-align:center;"></div>
    </div>
  </div>

  <script>
    // تحديد مسار الـ API تلقائياً للعمل المباشر سواء فُتح من السيرفر أو كملف HTML محلي
    const API_BASE = (window.location.protocol === 'file:' || !window.location.port || window.location.port !== '5000') 
      ? 'http://localhost:5000' 
      : '';

    let groupsData = [];
    let adsData = [];
    let publishedAdsData = [];
    let filteredPublished = [];
    let currentFilter = 'all';
    let isServerConnected = false;

    // -------------------------------------------------------------------------
    // مدن الجمهورية العربية السورية وخريطة المعرفات المعتمدة
    // -------------------------------------------------------------------------
    const SYRIAN_CITIES = [
      { id: 1, name: 'دمشق' },
      { id: 2, name: 'ريف دمشق' },
      { id: 3, name: 'حلب' },
      { id: 4, name: 'ريف حلب' },
      { id: 5, name: 'إدلب' },
      { id: 6, name: 'حمص' },
      { id: 7, name: 'حماة' },
      { id: 8, name: 'اللاذقية' },
      { id: 9, name: 'دير الزور' },
      { id: 10, name: 'الحسكة' },
      { id: 11, name: 'درعا' },
      { id: 12, name: 'طرطوس' },
      { id: 13, name: 'الرقة' },
      { id: 14, name: 'السويداء' },
      { id: 15, name: 'القنيطرة' }
    ];

    // إشعار عائم فوري للحفظ والمزامنة
    const SyncStatusManager = {
      toastTimer: null,
      success: function(msg) { this.show(msg, '#10b981'); },
      error: function(msg) { this.show(msg, '#ef4444'); },
      show: function(msg, color) {
        let el = document.getElementById('dashFloatingToast');
        if (!el) {
          el = document.createElement('div');
          el.id = 'dashFloatingToast';
          el.style.cssText = 'position:fixed; bottom:25px; left:25px; z-index:9999; padding:12px 22px; border-radius:12px; color:#fff; font-weight:800; font-size:13px; box-shadow:0 8px 30px rgba(0,0,0,0.6); display:flex; align-items:center; gap:8px; transition:all 0.3s ease; pointer-events:none;';
          document.body.appendChild(el);
        }
        el.style.background = color || '#2563eb';
        el.style.border = '1px solid ' + (color || '#3b82f6');
        el.innerHTML = msg;
        el.style.display = 'flex';
        el.style.opacity = '1';
        el.style.transform = 'translateY(0)';
        if (this.toastTimer) clearTimeout(this.toastTimer);
        this.toastTimer = setTimeout(() => {
          el.style.opacity = '0';
          el.style.transform = 'translateY(10px)';
          setTimeout(() => { el.style.display = 'none'; }, 300);
        }, 2500);
      }
    };
    window.SyncStatusManager = SyncStatusManager;

    // قاعدة بيانات الأقسام والتصنيفات الهرمية (326 فئة مع الأيقونات)
    const EMBEDDED_CATEGORIES = [{"id": 1, "name_ar": "السيارات", "slug": "cars", "icon": "/icons/cars.svg", "parent_id": null}, {"id": 16, "name_ar": "الدراجات النارية", "slug": "motorcycles", "icon": "/icons/motorcycles.svg", "parent_id": null}, {"id": 29, "name_ar": "العقارات", "slug": "real-estate", "icon": "/icons/realestate.svg", "parent_id": null}, {"id": 44, "name_ar": "الطاقة البديلة والكهرباء", "slug": "solar-energy", "icon": "/icons/solar-energy.svg", "parent_id": null}, {"id": 69, "name_ar": "الإلكترونيات والشبكات", "slug": "devices", "icon": "/icons/devices.svg", "parent_id": null}, {"id": 88, "name_ar": "المنزل والأثاث", "slug": "furniture", "icon": "/icons/furniture.svg", "parent_id": null}, {"id": 101, "name_ar": "الأزياء والعناية الشخصية", "slug": "fashion", "icon": "/icons/fashion.svg", "parent_id": null}, {"id": 114, "name_ar": "بقالة ومواد غذائية", "slug": "food", "icon": "/icons/food.svg", "parent_id": null}, {"id": 127, "name_ar": "صحة ورياضة", "slug": "health-sports", "icon": "/icons/health-sports.svg", "parent_id": null}, {"id": 140, "name_ar": "الحيوان ومواشي", "slug": "animals", "icon": "/icons/animals.svg", "parent_id": null}, {"id": 155, "name_ar": "مناسبات وحفلات", "slug": "occasions", "icon": "/icons/occasions.svg", "parent_id": null}, {"id": 167, "name_ar": "وجهات سياحية ورحلات", "slug": "tourism", "icon": "/icons/tourism.svg", "parent_id": null}, {"id": 176, "name_ar": "مكتبة وقرطاسية", "slug": "library", "icon": "/icons/library.svg", "parent_id": null}, {"id": 189, "name_ar": "الوظائف والأعمال", "slug": "jobs", "icon": "/icons/jobs.svg", "parent_id": null}, {"id": 202, "name_ar": "الخدمات", "slug": "services", "icon": "/icons/services.svg", "parent_id": null}, {"id": 217, "name_ar": "مواد البناء والمعدات", "slug": "construction", "icon": "/icons/construction.svg", "parent_id": null}, {"id": 232, "name_ar": "الزراعة ومستلزمات الإنتاج", "slug": "agriculture", "icon": "/icons/agriculture.svg", "parent_id": null}, {"id": 245, "name_ar": "السكراب والستوكات والتصفيات", "slug": "scrap-stock", "icon": "/icons/scrap-stock.svg", "parent_id": null}, {"id": 259, "name_ar": "أخرى", "slug": "other", "icon": "/icons/more-horizontal.svg", "parent_id": null}, {"id": 1143, "name_ar": "سيارات للبيع", "slug": "cars-for-sale", "icon": null, "parent_id": 1}, {"id": 1144, "name_ar": "هيونداي", "slug": "hyundai-sale", "icon": "/icons/cars/hyundai.svg", "parent_id": 1143}, {"id": 1145, "name_ar": "أكسنت / فيرنا", "slug": "hyundai-aksnt-fyrna-sale", "icon": null, "parent_id": 1144}, {"id": 1146, "name_ar": "إلنترا / أفانتي", "slug": "hyundai-alntra-afanty-sale", "icon": null, "parent_id": 1144}, {"id": 1147, "name_ar": "توسان", "slug": "hyundai-tosan-sale", "icon": null, "parent_id": 1144}, {"id": 1148, "name_ar": "سنتافي", "slug": "hyundai-sntafy-sale", "icon": null, "parent_id": 1144}, {"id": 1149, "name_ar": "سوناتا", "slug": "hyundai-sonata-sale", "icon": null, "parent_id": 1144}, {"id": 1150, "name_ar": "جيتز / i10 / ماتريكس", "slug": "hyundai-gytz-i10-matryks-sale", "icon": null, "parent_id": 1144}, {"id": 1151, "name_ar": "أزيرا", "slug": "hyundai-azyra-sale", "icon": null, "parent_id": 1144}, {"id": 1152, "name_ar": "كريتا / فينيو", "slug": "hyundai-kryta-fynyo-sale", "icon": null, "parent_id": 1144}, {"id": 1153, "name_ar": "H1 / ستاريا", "slug": "hyundai-h1-starya-sale", "icon": null, "parent_id": 1144}, {"id": 1155, "name_ar": "كيا", "slug": "kia-sale", "icon": "/icons/cars/kia.svg", "parent_id": 1143}, {"id": 1156, "name_ar": "ريو", "slug": "kia-ryo-sale", "icon": null, "parent_id": 1155}, {"id": 1157, "name_ar": "سيراتو / فورتي", "slug": "kia-syrato-forty-sale", "icon": null, "parent_id": 1155}, {"id": 1158, "name_ar": "بيكانتو", "slug": "kia-bykanto-sale", "icon": null, "parent_id": 1155}, {"id": 1159, "name_ar": "سبورتاج", "slug": "kia-sbortag-sale", "icon": null, "parent_id": 1155}, {"id": 1160, "name_ar": "أوبتيما / K5", "slug": "kia-aobtyma-k5-sale", "icon": null, "parent_id": 1155}, {"id": 1161, "name_ar": "سورينتو", "slug": "kia-sorynto-sale", "icon": null, "parent_id": 1155}, {"id": 1162, "name_ar": "كارينز", "slug": "kia-karynz-sale", "icon": null, "parent_id": 1155}, {"id": 1163, "name_ar": "كارنيفال", "slug": "kia-karnyfal-sale", "icon": null, "parent_id": 1155}, {"id": 1164, "name_ar": "كادينزا / K7", "slug": "kia-kadynza-k7-sale", "icon": null, "parent_id": 1155}, {"id": 1166, "name_ar": "تويوتا", "slug": "toyota-sale", "icon": "/icons/cars/toyota.svg", "parent_id": 1143}, {"id": 1167, "name_ar": "كورولا", "slug": "toyota-korola-sale", "icon": null, "parent_id": 1166}, {"id": 1168, "name_ar": "يارس / إيكو", "slug": "toyota-yars-ayko-sale", "icon": null, "parent_id": 1166}, {"id": 1169, "name_ar": "هايلوكس", "slug": "toyota-hayloks-sale", "icon": null, "parent_id": 1166}, {"id": 1170, "name_ar": "لاند كروزر", "slug": "toyota-land-krozr-sale", "icon": null, "parent_id": 1166}, {"id": 1171, "name_ar": "كامري", "slug": "toyota-kamry-sale", "icon": null, "parent_id": 1166}, {"id": 1172, "name_ar": "برادو", "slug": "toyota-brado-sale", "icon": null, "parent_id": 1166}, {"id": 1173, "name_ar": "راف 4", "slug": "toyota-raf-4-sale", "icon": null, "parent_id": 1166}, {"id": 1174, "name_ar": "بريوس / هايبرد", "slug": "toyota-bryos-haybrd-sale", "icon": null, "parent_id": 1166}, {"id": 1176, "name_ar": "مازدا", "slug": "mazda-sale", "icon": "/icons/cars/mazda.svg", "parent_id": 1143}, {"id": 1177, "name_ar": "مازدا 3", "slug": "mazda-mazda-3-sale", "icon": null, "parent_id": 1176}, {"id": 1178, "name_ar": "مازدا 323", "slug": "mazda-mazda-323-sale", "icon": null, "parent_id": 1176}, {"id": 1179, "name_ar": "مازدا 6", "slug": "mazda-mazda-6-sale", "icon": null, "parent_id": 1176}, {"id": 1180, "name_ar": "CX-5 / CX-9", "slug": "mazda-cx-5-cx-9-sale", "icon": null, "parent_id": 1176}, {"id": 1181, "name_ar": "929 / 626 الكلاسيكية", "slug": "mazda-929-626-alklasyky-sale", "icon": null, "parent_id": 1176}, {"id": 1182, "name_ar": "مازدا 2", "slug": "mazda-mazda-2-sale", "icon": null, "parent_id": 1176}, {"id": 1184, "name_ar": "نيسان", "slug": "nissan-sale", "icon": "/icons/cars/nissan.svg", "parent_id": 1143}, {"id": 1185, "name_ar": "صني", "slug": "nissan-sny-sale", "icon": null, "parent_id": 1184}, {"id": 1186, "name_ar": "تيدا", "slug": "nissan-tyda-sale", "icon": null, "parent_id": 1184}, {"id": 1187, "name_ar": "باترول", "slug": "nissan-batrol-sale", "icon": null, "parent_id": 1184}, {"id": 1188, "name_ar": "قشقاي", "slug": "nissan-kshkay-sale", "icon": null, "parent_id": 1184}, {"id": 1189, "name_ar": "ألتيما / ماكسيما", "slug": "nissan-altyma-maksyma-sale", "icon": null, "parent_id": 1184}, {"id": 1190, "name_ar": "داتسون / نافارا بيك آب", "slug": "nissan-datson-nafara-byk-ab-sale", "icon": null, "parent_id": 1184}, {"id": 1191, "name_ar": "إكس تريل", "slug": "nissan-aks-tryl-sale", "icon": null, "parent_id": 1184}, {"id": 1193, "name_ar": "سايبا", "slug": "saipa-sale", "icon": "/icons/cars/saipa.svg", "parent_id": 1143}, {"id": 1194, "name_ar": "صبا / برايد", "slug": "saipa-sba-brayd-sale", "icon": null, "parent_id": 1193}, {"id": 1195, "name_ar": "تيبا", "slug": "saipa-tyba-sale", "icon": null, "parent_id": 1193}, {"id": 1196, "name_ar": "كويك", "slug": "saipa-koyk-sale", "icon": null, "parent_id": 1193}, {"id": 1197, "name_ar": "ساينا", "slug": "saipa-sayna-sale", "icon": null, "parent_id": 1193}, {"id": 1199, "name_ar": "سيامكو / شام", "slug": "siamco-sale", "icon": "/icons/cars/siamco.webp", "parent_id": 1143}, {"id": 1200, "name_ar": "شام (Sham)", "slug": "siamco-sham-sham-sale", "icon": null, "parent_id": 1199}, {"id": 1201, "name_ar": "شمرا (Shamra)", "slug": "siamco-shmra-shamra-sale", "icon": null, "parent_id": 1199}, {"id": 1202, "name_ar": "شهباء (Shahba)", "slug": "siamco-shhbaaa-shahba-sale", "icon": null, "parent_id": 1199}, {"id": 1203, "name_ar": "سيريا بالميرا (Palmyra)", "slug": "siamco-syrya-balmyra-palmyra-sale", "icon": null, "parent_id": 1199}, {"id": 1205, "name_ar": "دايو", "slug": "daewoo-sale", "icon": "/icons/cars/daewoo.webp", "parent_id": 1143}, {"id": 1206, "name_ar": "لاسيتي", "slug": "daewoo-lasyty-sale", "icon": null, "parent_id": 1205}, {"id": 1207, "name_ar": "لانوس", "slug": "daewoo-lanos-sale", "icon": null, "parent_id": 1205}, {"id": 1208, "name_ar": "نوبيرا", "slug": "daewoo-nobyra-sale", "icon": null, "parent_id": 1205}, {"id": 1209, "name_ar": "ماتيز", "slug": "daewoo-matyz-sale", "icon": null, "parent_id": 1205}, {"id": 1210, "name_ar": "سيلو / ريسر", "slug": "daewoo-sylo-rysr-sale", "icon": null, "parent_id": 1205}, {"id": 1212, "name_ar": "سوزوكي", "slug": "suzuki-sale", "icon": "/icons/cars/suzuki.svg", "parent_id": 1143}, {"id": 1213, "name_ar": "ماروتي / ألتو", "slug": "suzuki-maroty-alto-sale", "icon": null, "parent_id": 1212}, {"id": 1214, "name_ar": "سويفت", "slug": "suzuki-soyft-sale", "icon": null, "parent_id": 1212}, {"id": 1215, "name_ar": "جراند فيتارا", "slug": "suzuki-grand-fytara-sale", "icon": null, "parent_id": 1212}, {"id": 1216, "name_ar": "جيمني", "slug": "suzuki-gymny-sale", "icon": null, "parent_id": 1212}, {"id": 1217, "name_ar": "كاري / دبابات", "slug": "suzuki-kary-dbabat-sale", "icon": null, "parent_id": 1212}, {"id": 1219, "name_ar": "ميتسوبيشي", "slug": "mitsubishi-sale", "icon": "/icons/cars/mitsubishi.svg", "parent_id": 1143}, {"id": 1220, "name_ar": "لانسر", "slug": "mitsubishi-lansr-sale", "icon": null, "parent_id": 1219}, {"id": 1221, "name_ar": "باجيرو", "slug": "mitsubishi-bagyro-sale", "icon": null, "parent_id": 1219}, {"id": 1222, "name_ar": "L200 (بيك آب)", "slug": "mitsubishi-l200-byk-ab-sale", "icon": null, "parent_id": 1219}, {"id": 1223, "name_ar": "أوتلاندر", "slug": "mitsubishi-aotlandr-sale", "icon": null, "parent_id": 1219}, {"id": 1224, "name_ar": "كانتر (شاحنات)", "slug": "mitsubishi-kantr-shahnat-sale", "icon": null, "parent_id": 1219}, {"id": 1226, "name_ar": "مرسيدس-بنز", "slug": "mercedes-sale", "icon": "/icons/cars/mercedes.svg", "parent_id": 1143}, {"id": 1227, "name_ar": "الفئة E (E-Class)", "slug": "mercedes-alfy-e-e-class-sale", "icon": null, "parent_id": 1226}, {"id": 1228, "name_ar": "الفئة C (C-Class)", "slug": "mercedes-alfy-c-c-class-sale", "icon": null, "parent_id": 1226}, {"id": 1229, "name_ar": "الفئة S (S-Class)", "slug": "mercedes-alfy-s-s-class-sale", "icon": null, "parent_id": 1226}, {"id": 1230, "name_ar": "الكلاسيكية (W123 / لف)", "slug": "mercedes-alklasyky-w123-lf-sale", "icon": null, "parent_id": 1226}, {"id": 1231, "name_ar": "ML / GLE / GL", "slug": "mercedes-ml-gle-gl-sale", "icon": null, "parent_id": 1226}, {"id": 1232, "name_ar": "الفئة G (G-Class)", "slug": "mercedes-alfy-g-g-class-sale", "icon": null, "parent_id": 1226}, {"id": 1233, "name_ar": "شاحنات وباصات", "slug": "mercedes-shahnat-obasat-sale", "icon": null, "parent_id": 1226}, {"id": 1235, "name_ar": "بي إم دبليو", "slug": "bmw-sale", "icon": "/icons/cars/bmw.svg", "parent_id": 1143}, {"id": 1236, "name_ar": "الفئة الثالثة (3 Series)", "slug": "bmw-alfy-althalth-3-series-sale", "icon": null, "parent_id": 1235}, {"id": 1237, "name_ar": "الفئة الخامسة (5 Series)", "slug": "bmw-alfy-alkhams-5-series-sale", "icon": null, "parent_id": 1235}, {"id": 1238, "name_ar": "جيبات X5", "slug": "bmw-gybat-x5-sale", "icon": null, "parent_id": 1235}, {"id": 1239, "name_ar": "الفئة السابعة (7 Series)", "slug": "bmw-alfy-alsabaa-7-series-sale", "icon": null, "parent_id": 1235}, {"id": 1240, "name_ar": "جيبات X6 / X3", "slug": "bmw-gybat-x6-x3-sale", "icon": null, "parent_id": 1235}, {"id": 1242, "name_ar": "بيجو", "slug": "peugeot-sale", "icon": "/icons/cars/peugeot.svg", "parent_id": 1143}, {"id": 1243, "name_ar": "206", "slug": "peugeot-206-sale", "icon": null, "parent_id": 1242}, {"id": 1244, "name_ar": "207 / 208", "slug": "peugeot-207-208-sale", "icon": null, "parent_id": 1242}, {"id": 1245, "name_ar": "307 / 308", "slug": "peugeot-307-308-sale", "icon": null, "parent_id": 1242}, {"id": 1246, "name_ar": "405 / 406 / 407", "slug": "peugeot-405-406-407-sale", "icon": null, "parent_id": 1242}, {"id": 1247, "name_ar": "301", "slug": "peugeot-301-sale", "icon": null, "parent_id": 1242}, {"id": 1248, "name_ar": "3008 / 5008", "slug": "peugeot-3008-5008-sale", "icon": null, "parent_id": 1242}, {"id": 1249, "name_ar": "بارتنر (Partner)", "slug": "peugeot-bartnr-partner-sale", "icon": null, "parent_id": 1242}, {"id": 1251, "name_ar": "فولكس فاجن", "slug": "volkswagen-sale", "icon": "/icons/cars/volkswagen.svg", "parent_id": 1143}, {"id": 1252, "name_ar": "جولف (Golf)", "slug": "volkswagen-golf-golf-sale", "icon": null, "parent_id": 1251}, {"id": 1253, "name_ar": "باسات (Passat)", "slug": "volkswagen-basat-passat-sale", "icon": null, "parent_id": 1251}, {"id": 1254, "name_ar": "بولو (Polo)", "slug": "volkswagen-bolo-polo-sale", "icon": null, "parent_id": 1251}, {"id": 1255, "name_ar": "تيجوان (Tiguan)", "slug": "volkswagen-tygoan-tiguan-sale", "icon": null, "parent_id": 1251}, {"id": 1256, "name_ar": "طوارق (Touareg)", "slug": "volkswagen-toark-touareg-sale", "icon": null, "parent_id": 1251}, {"id": 1257, "name_ar": "جيتا / بيتل", "slug": "volkswagen-gyta-bytl-sale", "icon": null, "parent_id": 1251}, {"id": 1259, "name_ar": "رينو", "slug": "renault-sale", "icon": "/icons/cars/renault.svg", "parent_id": 1143}, {"id": 1260, "name_ar": "ميجان (Megane)", "slug": "renault-mygan-megane-sale", "icon": null, "parent_id": 1259}, {"id": 1261, "name_ar": "داستر (Duster)", "slug": "renault-dastr-duster-sale", "icon": null, "parent_id": 1259}, {"id": 1262, "name_ar": "كليو (Clio)", "slug": "renault-klyo-clio-sale", "icon": null, "parent_id": 1259}, {"id": 1263, "name_ar": "لوجان / سيمبول", "slug": "renault-logan-symbol-sale", "icon": null, "parent_id": 1259}, {"id": 1264, "name_ar": "فلوانس (Fluence)", "slug": "renault-floans-fluence-sale", "icon": null, "parent_id": 1259}, {"id": 1266, "name_ar": "بي واي دي", "slug": "byd-sale", "icon": "/icons/cars/byd.svg", "parent_id": 1143}, {"id": 1267, "name_ar": "F3", "slug": "byd-f3-sale", "icon": null, "parent_id": 1266}, {"id": 1268, "name_ar": "سونج بلس (Song Plus)", "slug": "byd-song-bls-song-plus-sale", "icon": null, "parent_id": 1266}, {"id": 1269, "name_ar": "هان (Han EV)", "slug": "byd-han-han-ev-sale", "icon": null, "parent_id": 1266}, {"id": 1270, "name_ar": "يوان بلس (Yuan Plus)", "slug": "byd-yoan-bls-yuan-plus-sale", "icon": null, "parent_id": 1266}, {"id": 1271, "name_ar": "تانغ (Tang)", "slug": "byd-tangh-tang-sale", "icon": null, "parent_id": 1266}, {"id": 1272, "name_ar": "تشين (Qin Plus)", "slug": "byd-tshyn-qin-plus-sale", "icon": null, "parent_id": 1266}, {"id": 1274, "name_ar": "جيلي", "slug": "geely-sale", "icon": "/icons/cars/geely.svg", "parent_id": 1143}, {"id": 1275, "name_ar": "إمجراند (Emgrand 7/EC7)", "slug": "geely-amgrand-emgrand-7ec7-sale", "icon": null, "parent_id": 1274}, {"id": 1276, "name_ar": "كولراي (Coolray)", "slug": "geely-kolray-coolray-sale", "icon": null, "parent_id": 1274}, {"id": 1277, "name_ar": "GC6 / CK / MK", "slug": "geely-gc6-ck-mk-sale", "icon": null, "parent_id": 1274}, {"id": 1278, "name_ar": "توجيلا / أزكارا", "slug": "geely-togyla-azkara-sale", "icon": null, "parent_id": 1274}, {"id": 1279, "name_ar": "مونجارو", "slug": "geely-mongaro-sale", "icon": null, "parent_id": 1274}, {"id": 1280, "name_ar": "باندا", "slug": "geely-banda-sale", "icon": null, "parent_id": 1274}, {"id": 1282, "name_ar": "شيري", "slug": "chery-sale", "icon": "/icons/cars/chery.svg", "parent_id": 1143}, {"id": 1283, "name_ar": "كيو كيو (QQ)", "slug": "chery-kyo-kyo-qq-sale", "icon": null, "parent_id": 1282}, {"id": 1284, "name_ar": "تيجو (Tiggo 7 / 8 / 4)", "slug": "chery-tygo-tiggo-7-8-4-sale", "icon": null, "parent_id": 1282}, {"id": 1285, "name_ar": "أريزو (Arrizo)", "slug": "chery-aryzo-arrizo-sale", "icon": null, "parent_id": 1282}, {"id": 1286, "name_ar": "A11 / A15 / كوين", "slug": "chery-a11-a15-koyn-sale", "icon": null, "parent_id": 1282}, {"id": 1288, "name_ar": "شانجان", "slug": "changan-sale", "icon": "/icons/cars/changan.svg", "parent_id": 1143}, {"id": 1289, "name_ar": "CS35 Plus", "slug": "changan-cs35-plus-sale", "icon": null, "parent_id": 1288}, {"id": 1290, "name_ar": "CS75 / CS85 / CS95", "slug": "changan-cs75-cs85-cs95-sale", "icon": null, "parent_id": 1288}, {"id": 1291, "name_ar": "السفن (Alsvin)", "slug": "changan-alsfn-alsvin-sale", "icon": null, "parent_id": 1288}, {"id": 1292, "name_ar": "إيدو (Eado)", "slug": "changan-aydo-eado-sale", "icon": null, "parent_id": 1288}, {"id": 1293, "name_ar": "يوني (UNI-T / UNI-K)", "slug": "changan-yony-uni-t-uni-k-sale", "icon": null, "parent_id": 1288}, {"id": 1295, "name_ar": "شيفروليه", "slug": "chevrolet-sale", "icon": "/icons/cars/chevrolet.svg", "parent_id": 1143}, {"id": 1296, "name_ar": "أوبترا (Optra)", "slug": "chevrolet-aobtra-optra-sale", "icon": null, "parent_id": 1295}, {"id": 1297, "name_ar": "أفيو (Aveo)", "slug": "chevrolet-afyo-aveo-sale", "icon": null, "parent_id": 1295}, {"id": 1298, "name_ar": "كروز (Cruze)", "slug": "chevrolet-kroz-cruze-sale", "icon": null, "parent_id": 1295}, {"id": 1299, "name_ar": "تاهو / سوبربان", "slug": "chevrolet-taho-sobrban-sale", "icon": null, "parent_id": 1295}, {"id": 1300, "name_ar": "كابتيفا (Captiva)", "slug": "chevrolet-kabtyfa-captiva-sale", "icon": null, "parent_id": 1295}, {"id": 1301, "name_ar": "ماليبو / سبارك", "slug": "chevrolet-malybo-sbark-sale", "icon": null, "parent_id": 1295}, {"id": 1303, "name_ar": "أوبل", "slug": "opel-sale", "icon": "/icons/cars/opel.svg", "parent_id": 1143}, {"id": 1304, "name_ar": "أسترا (Astra)", "slug": "opel-astra-astra-sale", "icon": null, "parent_id": 1303}, {"id": 1305, "name_ar": "فيكترا (Vectra)", "slug": "opel-fyktra-vectra-sale", "icon": null, "parent_id": 1303}, {"id": 1306, "name_ar": "كورسا (Corsa)", "slug": "opel-korsa-corsa-sale", "icon": null, "parent_id": 1303}, {"id": 1307, "name_ar": "إنسيجنيا (Insignia)", "slug": "opel-ansygnya-insignia-sale", "icon": null, "parent_id": 1303}, {"id": 1308, "name_ar": "زافيرا / أوميغا", "slug": "opel-zafyra-aomygha-sale", "icon": null, "parent_id": 1303}, {"id": 1310, "name_ar": "فورد", "slug": "ford-sale", "icon": "/icons/cars/ford.svg", "parent_id": 1143}, {"id": 1311, "name_ar": "فيوجن (Fusion)", "slug": "ford-fyogn-fusion-sale", "icon": null, "parent_id": 1310}, {"id": 1312, "name_ar": "فوكس (Focus)", "slug": "ford-foks-focus-sale", "icon": null, "parent_id": 1310}, {"id": 1313, "name_ar": "إكسبلورر (Explorer)", "slug": "ford-aksblorr-explorer-sale", "icon": null, "parent_id": 1310}, {"id": 1314, "name_ar": "F-150 / رينجر", "slug": "ford-f-150-ryngr-sale", "icon": null, "parent_id": 1310}, {"id": 1315, "name_ar": "إسكيب / إيدج", "slug": "ford-askyb-aydg-sale", "icon": null, "parent_id": 1310}, {"id": 1316, "name_ar": "موستنج", "slug": "ford-mostng-sale", "icon": null, "parent_id": 1310}, {"id": 1318, "name_ar": "هوندا", "slug": "honda-sale", "icon": "/icons/cars/honda.svg", "parent_id": 1143}, {"id": 1319, "name_ar": "سيفيك (Civic)", "slug": "honda-syfyk-civic-sale", "icon": null, "parent_id": 1318}, {"id": 1320, "name_ar": "أكورد (Accord)", "slug": "honda-akord-accord-sale", "icon": null, "parent_id": 1318}, {"id": 1321, "name_ar": "CR-V", "slug": "honda-cr-v-sale", "icon": null, "parent_id": 1318}, {"id": 1322, "name_ar": "سيتي / بايلوت", "slug": "honda-syty-baylot-sale", "icon": null, "parent_id": 1318}, {"id": 1324, "name_ar": "إم جي", "slug": "mg-sale", "icon": "/icons/cars/mg.svg", "parent_id": 1143}, {"id": 1325, "name_ar": "MG 5", "slug": "mg-mg-5-sale", "icon": null, "parent_id": 1324}, {"id": 1326, "name_ar": "MG ZS", "slug": "mg-mg-zs-sale", "icon": null, "parent_id": 1324}, {"id": 1327, "name_ar": "MG 6 / GT", "slug": "mg-mg-6-gt-sale", "icon": null, "parent_id": 1324}, {"id": 1328, "name_ar": "MG RX5 / HS", "slug": "mg-mg-rx5-hs-sale", "icon": null, "parent_id": 1324}, {"id": 1330, "name_ar": "لادا", "slug": "lada-sale", "icon": "/icons/cars/lada.svg", "parent_id": 1143}, {"id": 1331, "name_ar": "2107 / 2105 (ريفا)", "slug": "lada-2107-2105-ryfa-sale", "icon": null, "parent_id": 1330}, {"id": 1332, "name_ar": "نيفا (Niva 4x4)", "slug": "lada-nyfa-niva-4x4-sale", "icon": null, "parent_id": 1330}, {"id": 1333, "name_ar": "سمارا (Samara)", "slug": "lada-smara-samara-sale", "icon": null, "parent_id": 1330}, {"id": 1334, "name_ar": "كالينا / غرانتا", "slug": "lada-kalyna-ghranta-sale", "icon": null, "parent_id": 1330}, {"id": 1336, "name_ar": "أودي", "slug": "audi-sale", "icon": "/icons/cars/audi.svg", "parent_id": 1143}, {"id": 1337, "name_ar": "A4", "slug": "audi-a4-sale", "icon": null, "parent_id": 1336}, {"id": 1338, "name_ar": "A6", "slug": "audi-a6-sale", "icon": null, "parent_id": 1336}, {"id": 1339, "name_ar": "Q7", "slug": "audi-q7-sale", "icon": null, "parent_id": 1336}, {"id": 1340, "name_ar": "Q5 / Q3", "slug": "audi-q5-q3-sale", "icon": null, "parent_id": 1336}, {"id": 1341, "name_ar": "A8 / A3", "slug": "audi-a8-a3-sale", "icon": null, "parent_id": 1336}, {"id": 1343, "name_ar": "سكودا", "slug": "skoda-sale", "icon": "/icons/cars/skoda.svg", "parent_id": 1143}, {"id": 1344, "name_ar": "أوكتافيا (Octavia)", "slug": "skoda-aoktafya-octavia-sale", "icon": null, "parent_id": 1343}, {"id": 1345, "name_ar": "فابيا (Fabia)", "slug": "skoda-fabya-fabia-sale", "icon": null, "parent_id": 1343}, {"id": 1346, "name_ar": "سوبيرب (Superb)", "slug": "skoda-sobyrb-superb-sale", "icon": null, "parent_id": 1343}, {"id": 1347, "name_ar": "كودياك / كاروك", "slug": "skoda-kodyak-karok-sale", "icon": null, "parent_id": 1343}, {"id": 1349, "name_ar": "فيات", "slug": "fiat-sale", "icon": "/icons/cars/fiat.svg", "parent_id": 1143}, {"id": 1350, "name_ar": "بونتو (Punto)", "slug": "fiat-bonto-punto-sale", "icon": null, "parent_id": 1349}, {"id": 1351, "name_ar": "تيبو (Tipo)", "slug": "fiat-tybo-tipo-sale", "icon": null, "parent_id": 1349}, {"id": 1352, "name_ar": "أونو (Uno)", "slug": "fiat-aono-uno-sale", "icon": null, "parent_id": 1349}, {"id": 1353, "name_ar": "سيينا / لينيا", "slug": "fiat-syyna-lynya-sale", "icon": null, "parent_id": 1349}, {"id": 1354, "name_ar": "فيات 500", "slug": "fiat-fyat-500-sale", "icon": null, "parent_id": 1349}, {"id": 1356, "name_ar": "لاند روفر", "slug": "land-rover-sale", "icon": "/icons/cars/land-rover.png", "parent_id": 1143}, {"id": 1357, "name_ar": "رنج روفر فوغ", "slug": "land-rover-rng-rofr-fogh-sale", "icon": null, "parent_id": 1356}, {"id": 1358, "name_ar": "رنج روفر سبورت", "slug": "land-rover-rng-rofr-sbort-sale", "icon": null, "parent_id": 1356}, {"id": 1359, "name_ar": "ديفندر", "slug": "land-rover-dyfndr-sale", "icon": null, "parent_id": 1356}, {"id": 1360, "name_ar": "إيفوك / فيلار", "slug": "land-rover-ayfok-fylar-sale", "icon": null, "parent_id": 1356}, {"id": 1361, "name_ar": "ديسكفري", "slug": "land-rover-dyskfry-sale", "icon": null, "parent_id": 1356}, {"id": 1363, "name_ar": "هونشي ودونغ فينغ وفاو", "slug": "hongqi-dfm-faw-sale", "icon": "/icons/cars/hongqi.webp", "parent_id": 1143}, {"id": 1364, "name_ar": "هونشي (H5/HS5/H9)", "slug": "hongqi-dfm-faw-honshy-h5hs5h9-sale", "icon": "/icons/cars/hongqi.webp", "parent_id": 1363}, {"id": 1365, "name_ar": "دونغ فينغ (A30/T5)", "slug": "hongqi-dfm-faw-dongh-fyngh-a30t5-sale", "icon": "/icons/cars/dongfeng.svg", "parent_id": 1363}, {"id": 1366, "name_ar": "بيستون (Bestune)", "slug": "hongqi-dfm-faw-byston-bestune-sale", "icon": "/icons/cars/faw.webp", "parent_id": 1363}, {"id": 1367, "name_ar": "فانات وشاحنات صينية", "slug": "hongqi-dfm-faw-fanat-oshahnat-syny-sale", "icon": null, "parent_id": 1363}, {"id": 1369, "name_ar": "قطع غيار وإكسسوارات السيارات", "slug": "auto-spare-parts", "icon": null, "parent_id": 1}, {"id": 1395, "name_ar": "سيارات للإيجار", "slug": "cars-for-rent", "icon": null, "parent_id": 1}, {"id": 1802, "name_ar": "موديلات أخرى", "slug": "hyundai-sale-other-models", "icon": null, "parent_id": 1144}, {"id": 1803, "name_ar": "موديلات أخرى", "slug": "kia-sale-other-models", "icon": null, "parent_id": 1155}, {"id": 1804, "name_ar": "موديلات أخرى", "slug": "toyota-sale-other-models", "icon": null, "parent_id": 1166}, {"id": 1805, "name_ar": "موديلات أخرى", "slug": "mazda-sale-other-models", "icon": null, "parent_id": 1176}, {"id": 1806, "name_ar": "موديلات أخرى", "slug": "nissan-sale-other-models", "icon": null, "parent_id": 1184}, {"id": 1807, "name_ar": "موديلات أخرى", "slug": "saipa-sale-other-models", "icon": null, "parent_id": 1193}, {"id": 1808, "name_ar": "موديلات أخرى", "slug": "siamco-sale-other-models", "icon": null, "parent_id": 1199}, {"id": 1809, "name_ar": "موديلات أخرى", "slug": "daewoo-sale-other-models", "icon": null, "parent_id": 1205}, {"id": 1810, "name_ar": "موديلات أخرى", "slug": "suzuki-sale-other-models", "icon": null, "parent_id": 1212}, {"id": 1811, "name_ar": "موديلات أخرى", "slug": "mitsubishi-sale-other-models", "icon": null, "parent_id": 1219}, {"id": 1812, "name_ar": "موديلات أخرى", "slug": "mercedes-sale-other-models", "icon": null, "parent_id": 1226}, {"id": 1813, "name_ar": "موديلات أخرى", "slug": "bmw-sale-other-models", "icon": null, "parent_id": 1235}, {"id": 1814, "name_ar": "موديلات أخرى", "slug": "peugeot-sale-other-models", "icon": null, "parent_id": 1242}, {"id": 1815, "name_ar": "موديلات أخرى", "slug": "volkswagen-sale-other-models", "icon": null, "parent_id": 1251}, {"id": 1816, "name_ar": "موديلات أخرى", "slug": "renault-sale-other-models", "icon": null, "parent_id": 1259}, {"id": 1817, "name_ar": "موديلات أخرى", "slug": "byd-sale-other-models", "icon": null, "parent_id": 1266}, {"id": 1818, "name_ar": "موديلات أخرى", "slug": "geely-sale-other-models", "icon": null, "parent_id": 1274}, {"id": 1819, "name_ar": "موديلات أخرى", "slug": "chery-sale-other-models", "icon": null, "parent_id": 1282}, {"id": 1820, "name_ar": "موديلات أخرى", "slug": "changan-sale-other-models", "icon": null, "parent_id": 1288}, {"id": 1821, "name_ar": "موديلات أخرى", "slug": "chevrolet-sale-other-models", "icon": null, "parent_id": 1295}, {"id": 1822, "name_ar": "موديلات أخرى", "slug": "opel-sale-other-models", "icon": null, "parent_id": 1303}, {"id": 1823, "name_ar": "موديلات أخرى", "slug": "ford-sale-other-models", "icon": null, "parent_id": 1310}, {"id": 1824, "name_ar": "موديلات أخرى", "slug": "honda-sale-other-models", "icon": null, "parent_id": 1318}, {"id": 1825, "name_ar": "موديلات أخرى", "slug": "mg-sale-other-models", "icon": null, "parent_id": 1324}, {"id": 1826, "name_ar": "موديلات أخرى", "slug": "lada-sale-other-models", "icon": null, "parent_id": 1330}, {"id": 1827, "name_ar": "موديلات أخرى", "slug": "audi-sale-other-models", "icon": null, "parent_id": 1336}, {"id": 1828, "name_ar": "موديلات أخرى", "slug": "skoda-sale-other-models", "icon": null, "parent_id": 1343}, {"id": 1829, "name_ar": "موديلات أخرى", "slug": "fiat-sale-other-models", "icon": null, "parent_id": 1349}, {"id": 1830, "name_ar": "موديلات أخرى", "slug": "land-rover-sale-other-models", "icon": null, "parent_id": 1356}, {"id": 1831, "name_ar": "موديلات أخرى", "slug": "hongqi-dfm-faw-sale-other-models", "icon": null, "parent_id": 1363}, {"id": 1832, "name_ar": "ماركات أخرى", "slug": "other-car-brands-sale", "icon": null, "parent_id": 1143}, {"id": 3091, "name_ar": "دراجات نارية (ميتورات)", "slug": "motorcycles-gas-1787857971-557", "icon": null, "parent_id": 16}, {"id": 3117, "name_ar": "دراجات هوائية (بسكليتات)", "slug": "bicycles-1787857971-138", "icon": null, "parent_id": 16}, {"id": 3124, "name_ar": "قطع غيار وإكسسوارات الدراجات", "slug": "motorcycle-parts-accessories-1787857971-251", "icon": null, "parent_id": 16}, {"id": 3131, "name_ar": "شقق", "slug": "apartments-1787869957-600", "icon": null, "parent_id": 29}, {"id": 3132, "name_ar": "فلل وبيوت", "slug": "villas-houses-1787869957-362", "icon": null, "parent_id": 29}, {"id": 3133, "name_ar": "أراضي ومزارع", "slug": "lands-farms-1787869957-802", "icon": null, "parent_id": 29}, {"id": 3134, "name_ar": "محلات وعقارات تجارية", "slug": "commercial-shops-1787869957-710", "icon": null, "parent_id": 29}, {"id": 3135, "name_ar": "شاليهات واستراحات", "slug": "chalets-resorts-1787869957-992", "icon": null, "parent_id": 29}, {"id": 3136, "name_ar": "ألواح ومنظومات طاقة شمسية", "slug": "solar-panels-systems-1787870392-477", "icon": null, "parent_id": 44}, {"id": 3137, "name_ar": "إنفيرترات وبطاريات", "slug": "inverters-batteries-1787870392-848", "icon": null, "parent_id": 44}, {"id": 3138, "name_ar": "مولدات ومستلزمات كهرباء", "slug": "generators-electrical-supplies-1787870392-844", "icon": null, "parent_id": 44}, {"id": 3139, "name_ar": "جوالات وهواتف ذكية", "slug": "smartphones-1787870649-134", "icon": null, "parent_id": 69}, {"id": 3140, "name_ar": "أجهزة لوحية وآيباد", "slug": "tablets-ipad-1787870649-806", "icon": null, "parent_id": 69}, {"id": 3141, "name_ar": "كمبيوتر ولابتوب", "slug": "computers-laptops-1787870649-515", "icon": null, "parent_id": 69}, {"id": 3143, "name_ar": "شاشات وتلفزيونات", "slug": "tv-screens-1787870649-375", "icon": null, "parent_id": 69}, {"id": 3144, "name_ar": "ساعات ذكية وسماعات وإكسسوارات", "slug": "smartwatches-accessories-1787870649-752", "icon": null, "parent_id": 69}, {"id": 3146, "name_ar": "أخرى", "slug": "electronics-other-1787871022", "icon": null, "parent_id": 69}, {"id": 3147, "name_ar": "أخرى", "slug": "solar-other-1787871067", "icon": null, "parent_id": 44}, {"id": 3148, "name_ar": "أثاث منزلي وغرف", "slug": "home-furniture-rooms-1787871873-618", "icon": null, "parent_id": 88}, {"id": 3149, "name_ar": "أجهزة كهربائية ومنزلية", "slug": "home-electrical-appliances-1787871873-474", "icon": null, "parent_id": 88}, {"id": 3150, "name_ar": "مطابخ وأواني", "slug": "kitchens-cookware-1787871873-757", "icon": null, "parent_id": 88}, {"id": 3151, "name_ar": "سجاد ومفروشات وستائر", "slug": "carpets-curtains-textiles-1787871873-389", "icon": null, "parent_id": 88}, {"id": 3152, "name_ar": "أثاث مكتبي وجلسات خارجية", "slug": "office-outdoor-furniture-1787871873-113", "icon": null, "parent_id": 88}, {"id": 3153, "name_ar": "أخرى", "slug": "home-other-1787871873-400", "icon": null, "parent_id": 88}, {"id": 3154, "name_ar": "وظائف شاغرة", "slug": "job-vacancies-1787872151-772", "icon": null, "parent_id": 189}, {"id": 3155, "name_ar": "باحثون عن عمل", "slug": "job-seekers-1787872151-444", "icon": null, "parent_id": 189}, {"id": 3156, "name_ar": "فرص استثمار وشراكات", "slug": "investment-partnerships-1787872151-757", "icon": null, "parent_id": 189}, {"id": 3157, "name_ar": "أخرى", "slug": "jobs-other-1787872151-403", "icon": null, "parent_id": 189}, {"id": 3158, "name_ar": "خدمات مقاولات", "slug": "contracting-services-1787872334-690", "icon": null, "parent_id": 202}, {"id": 3159, "name_ar": "خدمات التوصيل", "slug": "delivery-services-1787872334-277", "icon": null, "parent_id": 202}, {"id": 3160, "name_ar": "خدمات تعقيب", "slug": "clearance-services-1787872334-910", "icon": null, "parent_id": 202}, {"id": 3161, "name_ar": "خدمات نقل العفش", "slug": "furniture-moving-services-1787872334-319", "icon": null, "parent_id": 202}, {"id": 3162, "name_ar": "خدمات نظافة", "slug": "cleaning-services-1787872334-215", "icon": null, "parent_id": 202}, {"id": 3163, "name_ar": "خدمات قانونية", "slug": "legal-services-1787872334-237", "icon": null, "parent_id": 202}, {"id": 3164, "name_ar": "خدمات محاسبية ومالية", "slug": "accounting-financial-services-1787872334-249", "icon": null, "parent_id": 202}, {"id": 3165, "name_ar": "خدمات أخرى", "slug": "other-services-1787872334-777", "icon": null, "parent_id": 202}, {"id": 3166, "name_ar": "ملابس رجالية", "slug": "mens-clothing-1787872599-341", "icon": null, "parent_id": 101}, {"id": 3167, "name_ar": "ملابس نسائية وفساتين", "slug": "womens-clothing-dresses-1787872599-873", "icon": null, "parent_id": 101}, {"id": 3168, "name_ar": "ملابس أطفال ومواليد", "slug": "kids-baby-clothing-1787872599-790", "icon": null, "parent_id": 101}, {"id": 3169, "name_ar": "ساعات ومجوهرات وإكسسوارات", "slug": "watches-jewelry-accessories-1787872599-529", "icon": null, "parent_id": 101}, {"id": 3170, "name_ar": "عطور ومستحضرات تجميل", "slug": "perfumes-cosmetics-1787872599-856", "icon": null, "parent_id": 101}, {"id": 3171, "name_ar": "أخرى", "slug": "fashion-other-1787872599-888", "icon": null, "parent_id": 101}, {"id": 3172, "name_ar": "مواد وأطعمة غذائية", "slug": "food-groceries-1787925468-517", "icon": null, "parent_id": 114}, {"id": 3173, "name_ar": "منظفات ومستلزمات", "slug": "detergents-grocery-supplies-1787925468-663", "icon": null, "parent_id": 114}, {"id": 3174, "name_ar": "أخرى", "slug": "groceries-other-1787925468-640", "icon": null, "parent_id": 114}, {"id": 3175, "name_ar": "أجهزة ومعدات رياضية", "slug": "sports-fitness-equipment-1787925614-646", "icon": null, "parent_id": 127}, {"id": 3176, "name_ar": "مستلزمات وأجهزة طبية", "slug": "medical-equipment-supplies-1787925614-774", "icon": null, "parent_id": 127}, {"id": 3177, "name_ar": "مكملات غذائية وفيتامينات", "slug": "supplements-vitamins-1787925614-230", "icon": null, "parent_id": 127}, {"id": 3178, "name_ar": "أخرى", "slug": "health-sports-other-1787925614-977", "icon": null, "parent_id": 127}, {"id": 3179, "name_ar": "غنم وماعز وإبل", "slug": "sheep-goats-camels-1787925814-406", "icon": null, "parent_id": 140}, {"id": 3180, "name_ar": "أبقار وعجول وخيول", "slug": "cattle-horses-1787925814-818", "icon": null, "parent_id": 140}, {"id": 3181, "name_ar": "طيور ودواجن وحمام", "slug": "birds-poultry-pigeons-1787925814-324", "icon": null, "parent_id": 140}, {"id": 3182, "name_ar": "قطط وحيوانات أليفة ومستلزماتها", "slug": "pets-cats-supplies-1787925814-583", "icon": null, "parent_id": 140}, {"id": 3183, "name_ar": "أعلاف ومستلزمات مزارع", "slug": "fodder-farm-supplies-1787925814-865", "icon": null, "parent_id": 140}, {"id": 3184, "name_ar": "أخرى", "slug": "animals-other-1787925814-334", "icon": null, "parent_id": 140}, {"id": 3185, "name_ar": "مواد بناء وأسمنت وحديد", "slug": "building-materials-cement-steel-1787925814-912", "icon": null, "parent_id": 217}, {"id": 3186, "name_ar": "عدد وأدوات مهنية وكهربائية", "slug": "tools-hardware-1787925814-709", "icon": null, "parent_id": 217}, {"id": 3187, "name_ar": "آليات ومعدات ثقيلة", "slug": "heavy-machinery-equipment-1787925814-135", "icon": null, "parent_id": 217}, {"id": 3188, "name_ar": "سيراميك وأدوات صحية وأبواب", "slug": "sanitary-ceramics-doors-1787925814-104", "icon": null, "parent_id": 217}, {"id": 3189, "name_ar": "أخرى", "slug": "construction-other-1787925814-238", "icon": null, "parent_id": 217}, {"id": 3190, "name_ar": "أشجار وأشتال وبذور", "slug": "trees-seedlings-seeds-1787925814-271", "icon": null, "parent_id": 232}, {"id": 3191, "name_ar": "أسمدة ومبيدات زراعية", "slug": "fertilizers-pesticides-1787925814-762", "icon": null, "parent_id": 232}, {"id": 3192, "name_ar": "مضخات وشبكات ري وآليات زراعية", "slug": "pumps-irrigation-tractors-1787925814-538", "icon": null, "parent_id": 232}, {"id": 3193, "name_ar": "أخرى", "slug": "agriculture-other-1787925814-265", "icon": null, "parent_id": 232}, {"id": 3194, "name_ar": "سكراب ومعادن وخردة", "slug": "scrap-metals-junk-1787925814-876", "icon": null, "parent_id": 245}, {"id": 3195, "name_ar": "ستوكات وتصفيات بضائع ومستودعات", "slug": "stock-clearance-wholesale-1787925814-524", "icon": null, "parent_id": 245}, {"id": 3196, "name_ar": "أخرى", "slug": "scrap-other-1787925814-786", "icon": null, "parent_id": 245}, {"id": 3197, "name_ar": "صالات وقاعات مناسبات", "slug": "event-halls-venues-1787925814-597", "icon": null, "parent_id": 155}, {"id": 3198, "name_ar": "كوش وتجهيزات حفلات وضيافة", "slug": "party-setup-hospitality-1787925814-923", "icon": null, "parent_id": 155}, {"id": 3199, "name_ar": "أخرى", "slug": "events-other-1787925814-445", "icon": null, "parent_id": 155}, {"id": 3200, "name_ar": "شاليهات ومزارع واستراحات سياحية", "slug": "chalets-tourist-farms-1787925814-339", "icon": null, "parent_id": 167}, {"id": 3201, "name_ar": "فنادق ورحلات وبرامج سياحية", "slug": "hotels-trips-tourism-1787925814-143", "icon": null, "parent_id": 167}, {"id": 3202, "name_ar": "أخرى", "slug": "tourism-other-1787925814-192", "icon": null, "parent_id": 167}, {"id": 3203, "name_ar": "كتب ومراجع ومطبوعات", "slug": "books-publications-1787925814-615", "icon": null, "parent_id": 176}, {"id": 3204, "name_ar": "قرطاسية ومستلزمات مدرسية ومكتبية", "slug": "stationery-school-supplies-1787925814-309", "icon": null, "parent_id": 176}, {"id": 3205, "name_ar": "أخرى", "slug": "stationery-other-1787925814-650", "icon": null, "parent_id": 176}, {"id": 3206, "name_ar": "نوادر ومقتنيات وتحف قديمة", "slug": "antiques-collectibles-1787925814-388", "icon": null, "parent_id": 259}, {"id": 3207, "name_ar": "أصناف عامة ومتنوعة", "slug": "general-misc-1787925814-280", "icon": null, "parent_id": 259}];
    let allCategoriesData = [];
    const catMap = {};
    const childrenMap = {};
    let activePickerAdIndex = null;
    let pickerCurrentPid = 'root';
    let pickerTrail = [];

    function initCategories(data) {
      if (!Array.isArray(data) || data.length === 0) return;
      allCategoriesData = data;
      for (const k in catMap) delete catMap[k];
      for (const k in childrenMap) delete childrenMap[k];
      allCategoriesData.forEach(c => {
        catMap[c.id] = c;
        const pid = (c.parent_id !== null && c.parent_id !== undefined && c.parent_id !== '') ? String(c.parent_id) : 'root';
        if (!childrenMap[pid]) {
          childrenMap[pid] = [];
        }
        childrenMap[pid].push(c);
      });
    }

    function getCategoryPathText(catId) {
      if (!catId || !catMap[catId]) return '';
      const trail = [];
      let cur = catMap[catId];
      const visited = new Set();
      while (cur && !visited.has(cur.id)) {
        visited.add(cur.id);
        trail.unshift(cur.name_ar);
        if (cur.parent_id && catMap[cur.parent_id]) {
          cur = catMap[cur.parent_id];
        } else {
          break;
        }
      }
      return trail.join(' > ');
    }

    function getCategoryRootName(catId) {
      if (!catId || !catMap[catId]) return 'عام';
      let cur = catMap[catId];
      const visited = new Set();
      while (cur && !visited.has(cur.id)) {
        visited.add(cur.id);
        if (cur.parent_id && catMap[cur.parent_id]) {
          cur = catMap[cur.parent_id];
        } else {
          return cur.name_ar;
        }
      }
      return cur ? cur.name_ar : 'عام';
    }

    async function loadCategoriesData() {
      try {
        const res = await apiFetch('/api/categories');
        if (res.ok) {
          const data = await res.json();
          if (Array.isArray(data) && data.length > 0) {
            initCategories(data);
            return;
          }
        }
      } catch (e) {
        console.warn("Could not fetch categories from server, using preloaded categories:", e);
      }
    }

    // تهيئة الأقسام فورياً عند تحميل الصفحة
    initCategories(EMBEDDED_CATEGORIES);

    // -------------------------------------------------------------------------
    // دوال بوب اب اختيار وتصفح القسم مع بطاقة تفاصيل الإعلان
    // -------------------------------------------------------------------------
    function openCategoryPickerForAd(idx) {
      if (typeof idx !== 'number' || idx < 0 || idx >= adsData.length) {
        console.warn("Invalid ad index passed to openCategoryPickerForAd:", idx);
        return;
      }
      activePickerAdIndex = idx;
      const ad = adsData[idx];
      if (!ad) return;

      const searchInp = document.getElementById('categoryPickerSearch');
      if (searchInp) searchInp.value = '';

      // قراءة أحدث القيم من حقول الإدخال الحالية إن كانت معدلة
      const titleInp = document.getElementById(`titleInp-${idx}`);
      const curTitle = titleInp ? titleInp.value.trim() : (ad.clean_title || ad.title || 'إعلان');

      const priceInp = document.getElementById(`priceInp-${idx}`);
      const currencySel = document.getElementById(`currencySel-${idx}`);
      const curPriceNum = priceInp && priceInp.value !== '' ? Number(priceInp.value) : (ad.price_info?.amount);
      const curCurr = currencySel ? currencySel.value : (ad.price_info?.currency || 'SYP');
      const curCurrSym = curCurr === 'USD' ? '$' : 'ل.س';
      const curPriceStr = (curPriceNum !== undefined && curPriceNum !== null && !isNaN(curPriceNum)) ? `${Number(curPriceNum).toLocaleString()} ${curCurrSym}` : 'على السوم';

      const citySel = document.getElementById(`citySel-${idx}`);
      const areaInp = document.getElementById(`areaInp-${idx}`);
      const curCity = citySel ? (citySel.options[citySel.selectedIndex]?.dataset.name || citySel.options[citySel.selectedIndex]?.text) : (ad.city_name || 'دمشق');
      const curArea = areaInp ? areaInp.value.trim() : (ad.sub_district_name || '');
      const curCityStr = curArea ? `${curCity} (${curArea})` : curCity;

      const phoneInp = document.getElementById(`phoneInp-${idx}`);
      const curPhone = phoneInp ? phoneInp.value.trim() : (ad.phone_number || '-');

      const publisherInp = document.getElementById(`publisherInp-${idx}`);
      const curUser = publisherInp ? publisherInp.value.trim() : (ad.publisher_name || 'أبو محمد الشامي');

      const descInp = document.getElementById(`descInp-${idx}`);
      const curDesc = descInp ? descInp.value.trim() : (ad.clean_description || ad.description || '(لا يوجد نص وصف مسجل)');

      const catDisplay = document.getElementById(`catDisplay-${idx}`);
      const curCat = catDisplay ? catDisplay.textContent.trim() : (ad.category_hierarchy || `${ad.category || 'عام'}`);

      const images = Array.isArray(ad.nimages) ? ad.nimages : [];
      const firstImg = images.length > 0 ? `${API_BASE}/imgs/${encodeURIComponent(images[0])}` : '';

      // تعبئة بطاقة معلومات الإعلان المرجعية في العمود الأيسر (Reference Card)
      const pIdBadge = document.getElementById('pickerAdIdBadge');
      if (pIdBadge) pIdBadge.textContent = `#${idx + 1}`;

      const pTitleBadge = document.getElementById('pickerAdTitleBadge');
      if (pTitleBadge) pTitleBadge.textContent = `الإعلان: ${curTitle.length > 55 ? curTitle.substring(0, 55) + '...' : curTitle}`;

      const pImg = document.getElementById('pickerRefImage');
      if (pImg) {
        pImg.src = firstImg || 'https://placehold.co/400x250/1e293b/f8fafc?text=No+Image';
        pImg.dataset.title = curTitle;
        pImg.dataset.price = curPriceStr;
      }

      const pTitle = document.getElementById('pickerRefTitle');
      if (pTitle) pTitle.textContent = curTitle;

      const pCat = document.getElementById('pickerRefCategory');
      if (pCat) pCat.textContent = curCat;

      const pPrice = document.getElementById('pickerRefPrice');
      if (pPrice) pPrice.textContent = curPriceStr;

      const pCity = document.getElementById('pickerRefCity');
      if (pCity) pCity.textContent = curCityStr;

      const pUser = document.getElementById('pickerRefUser');
      if (pUser) pUser.textContent = curUser;

      const pPhone = document.getElementById('pickerRefPhone');
      if (pPhone) pPhone.textContent = curPhone;

      const pDesc = document.getElementById('pickerRefDescription');
      if (pDesc) pDesc.textContent = curDesc;

      const pLive = document.getElementById('pickerRefLiveUrl');
      if (pLive) {
        pLive.href = ad.ad_url || '#';
        pLive.style.display = ad.ad_url ? 'inline-flex' : 'none';
      }

      // بادجات المواصفات الفنية
      const pSpecsBadges = document.getElementById('pickerRefSpecsBadges');
      if (pSpecsBadges) {
        const spObj = (typeof ad.specifications === 'object' && ad.specifications !== null) ? ad.specifications : {};
        const items = [];
        if (spObj.make) items.push(`🏢 ${spObj.make}`);
        if (spObj.model) items.push(`🚗 ${spObj.model}`);
        if (spObj.year) items.push(`📅 ${spObj.year}`);
        if (spObj.transmission) items.push(`⚙️ ${spObj.transmission}`);
        if (spObj.fuel_type) items.push(`⛽ ${spObj.fuel_type}`);
        if (spObj.condition) items.push(`✨ ${spObj.condition}`);
        if (spObj.mileage) items.push(`📟 ${spObj.mileage}`);
        if (spObj.area) items.push(`📐 ${spObj.area}`);
        if (spObj.rooms) items.push(`🚪 ${spObj.rooms}`);
        pSpecsBadges.innerHTML = items.map(s => `<span style="background:rgba(56,189,248,0.15); color:#38bdf8; border:1px solid rgba(56,189,248,0.3); border-radius:6px; padding:2px 8px; font-size:10px; font-weight:700;">${escapeHtml(s)}</span>`).join('');
      }

      // فتح القسم المختار حالياً إن وجد أو المستوى الرئيسي
      const currentCatId = ad.leaf_category_id;
      if (currentCatId && catMap[currentCatId]) {
        pickerTrail = [];
        let cur = catMap[currentCatId];
        const visited = new Set();
        while (cur && !visited.has(cur.id)) {
          visited.add(cur.id);
          if (cur.parent_id && catMap[cur.parent_id]) {
            pickerTrail.unshift(catMap[cur.parent_id]);
            cur = catMap[cur.parent_id];
          } else {
            break;
          }
        }
        const lastParent = pickerTrail.length > 0 ? pickerTrail[pickerTrail.length - 1].id : 'root';
        renderPickerLevel(lastParent, pickerTrail);
      } else {
        renderPickerLevel('root', []);
      }

      const modal = document.getElementById('categoryPickerModal');
      if (modal) modal.style.display = 'flex';
    }

    function closeCategoryPickerModal() {
      const modal = document.getElementById('categoryPickerModal');
      if (modal) modal.style.display = 'none';
      activePickerAdIndex = null;
    }

    function renderPickerLevel(parentId, trail) {
      pickerCurrentPid = String(parentId);
      pickerTrail = trail || [];

      const breadcrumbsOl = document.getElementById('categoryPickerBreadcrumbs');
      if (breadcrumbsOl) {
        let bHtml = `<span class="crumb-link" onclick="goToPickerBreadcrumb(-1)"><i class="fa-solid fa-house"></i> الرئيسية</span>`;
        pickerTrail.forEach((item, idx) => {
          bHtml += ` <span class="crumb-sep">›</span> `;
          if (idx === pickerTrail.length - 1) {
            bHtml += `<span class="crumb-active">${escapeHtml(item.name_ar)}</span>`;
          } else {
            bHtml += `<span class="crumb-link" onclick="goToPickerBreadcrumb(${idx})">${escapeHtml(item.name_ar)}</span>`;
          }
        });
        breadcrumbsOl.innerHTML = bHtml;
      }

      const backBtn = document.getElementById('btnPickerBack');
      if (backBtn) {
        backBtn.style.display = pickerTrail.length > 0 ? 'inline-flex' : 'none';
      }

      const parentActionBox = document.getElementById('pickerCurrentParentAction');
      if (parentActionBox) {
        if (pickerCurrentPid !== 'root' && catMap[pickerCurrentPid]) {
          const currentCat = catMap[pickerCurrentPid];
          parentActionBox.innerHTML = `
            <div style="background:rgba(37,99,235,0.15); border:1px solid rgba(59,130,246,0.3); border-radius:10px; padding:10px 14px; display:flex; align-items:center; justify-content:space-between; gap:10px; margin-bottom:12px;">
              <div style="display:flex; align-items:center; gap:8px;">
                <span style="font-size:18px;">📂</span>
                <div>
                  <span style="font-size:11px; color:var(--text-muted); display:block;">أنت تتصفح الآن قسم:</span>
                  <strong style="color:#60a5fa; font-size:13px;">${escapeHtml(currentCat.name_ar)}</strong>
                </div>
              </div>
              <button type="button" class="btn btn-sm btn-success" style="font-weight:800; border-radius:8px;" onclick="selectCategoryFinal('${currentCat.id}')">
                <i class="fa-solid fa-check-double"></i> اعتماد هذا القسم واختياره
              </button>
            </div>
          `;
          parentActionBox.style.display = 'block';
        } else {
          parentActionBox.innerHTML = '';
          parentActionBox.style.display = 'none';
        }
      }

      const items = childrenMap[pickerCurrentPid] || [];
      renderCategoryGrid(items, false);
    }

    function goToPickerBreadcrumb(index) {
      if (index === -1) {
        renderPickerLevel('root', []);
      } else if (index < pickerTrail.length) {
        const target = pickerTrail[index];
        const newTrail = pickerTrail.slice(0, index + 1);
        renderPickerLevel(target.id, newTrail);
      }
    }

    function navigatePickerBack() {
      if (pickerTrail.length > 1) {
        pickerTrail.pop();
        const prev = pickerTrail[pickerTrail.length - 1];
        renderPickerLevel(prev.id, pickerTrail);
      } else {
        renderPickerLevel('root', []);
      }
    }

    function drillDownCategory(catId) {
      const cat = catMap[catId];
      if (!cat) return;
      pickerTrail.push(cat);
      renderPickerLevel(cat.id, pickerTrail);
    }

    function renderCategoryGrid(items, isSearchResult) {
      const grid = document.getElementById('categoryPickerGrid');
      const emptyBox = document.getElementById('categoryPickerEmpty');
      if (!grid) return;

      if (!items || items.length === 0) {
        grid.innerHTML = '';
        if (emptyBox) emptyBox.style.display = 'block';
        return;
      }

      if (emptyBox) emptyBox.style.display = 'none';

      let html = '';
      items.forEach(c => {
        const hasChildren = (childrenMap[String(c.id)] || []).length > 0;
        let iconUrl = 'https://lelbai.com/icons/cars.svg';
        if (c.icon) {
          iconUrl = c.icon.startsWith('http') ? c.icon : 'https://lelbai.com/' + c.icon.replace(/^\/+/, '');
        }

        const isDirect = !hasChildren;
        const actionFn = hasChildren ? `drillDownCategory('${c.id}')` : `selectCategoryFinal('${c.id}')`;
        const pathBreadcrumb = isSearchResult ? `<div style="font-size:10px; color:var(--text-muted); margin-top:3px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; max-width:130px;">${escapeHtml(getCategoryPathText(c.id))}</div>` : '';

        html += `
          <div class="category-tile ${isDirect ? 'leaf-tile' : ''}" onclick="${actionFn}" title="${escapeHtml(c.name_ar)}">
            <div class="cat-tile-icon">
              <img src="${iconUrl}" alt="" onerror="this.onerror=null; this.src='https://lelbai.com/icons/cars.svg';" />
            </div>
            <div class="cat-tile-title">${escapeHtml(c.name_ar)}</div>
            ${pathBreadcrumb}
            ${hasChildren ? `
              <span class="cat-tile-badge badge-sub"><i class="fa-solid fa-arrow-left"></i> تفريع</span>
            ` : `
              <span class="cat-tile-badge badge-leaf"><i class="fa-solid fa-check"></i> أصغر فئة</span>
            `}
          </div>
        `;
      });

      grid.innerHTML = html;
    }

    function filterCategoryPicker(query) {
      query = (query || '').trim().toLowerCase();
      const parentActionBox = document.getElementById('pickerCurrentParentAction');
      const backBtn = document.getElementById('btnPickerBack');

      if (!query) {
        if (backBtn) backBtn.style.display = pickerTrail.length > 0 ? 'inline-flex' : 'none';
        renderPickerLevel(pickerCurrentPid, pickerTrail);
        return;
      }

      if (parentActionBox) parentActionBox.style.display = 'none';
      if (backBtn) backBtn.style.display = 'none';

      const breadcrumbsOl = document.getElementById('categoryPickerBreadcrumbs');
      if (breadcrumbsOl) {
        breadcrumbsOl.innerHTML = `<span class="crumb-link" onclick="clearPickerSearch()"><i class="fa-solid fa-house"></i> الرئيسية</span> <span class="crumb-sep">›</span> <span class="crumb-active">نتائج البحث عن: "${escapeHtml(query)}"</span>`;
      }

      const matched = allCategoriesData.filter(c => {
        const nameAr = (c.name_ar || '').toLowerCase();
        const slug = (c.slug || '').toLowerCase();
        return nameAr.includes(query) || slug.includes(query);
      });

      renderCategoryGrid(matched, true);
    }

    function clearPickerSearch() {
      const searchInp = document.getElementById('categoryPickerSearch');
      if (searchInp) searchInp.value = '';
      renderPickerLevel(pickerCurrentPid, pickerTrail);
    }

    function selectCategoryFinal(catId) {
      if (activePickerAdIndex === null || !adsData[activePickerAdIndex]) {
        closeCategoryPickerModal();
        return;
      }
      const ad = adsData[activePickerAdIndex];
      const cat = catMap[catId];
      if (!cat) return;

      const hierarchy = getCategoryPathText(cat.id);
      const rootCatName = getCategoryRootName(cat.id);

      ad.leaf_category_id = Number(cat.id);
      ad.leaf_category_name = cat.name_ar;
      ad.category_hierarchy = hierarchy;
      ad.category = rootCatName;

      // تحديث الزر المعروض في كرت الإعلان فورياً
      const catDisplayEl = document.getElementById(`catDisplay-${activePickerAdIndex}`);
      if (catDisplayEl) {
        catDisplayEl.textContent = hierarchy;
        const parentBtn = catDisplayEl.closest('.btn-category-select');
        if (parentBtn) {
          parentBtn.style.borderColor = '#10b981';
          parentBtn.style.background = 'rgba(16, 185, 129, 0.2)';
          setTimeout(() => {
            if (parentBtn) {
              parentBtn.style.borderColor = 'rgba(59, 130, 246, 0.35)';
              parentBtn.style.background = 'rgba(37, 99, 235, 0.12)';
            }
          }, 2000);
        }
      }

      markAdDirty(activePickerAdIndex);
      closeCategoryPickerModal();
      SyncStatusManager.success(`تم اختيار القسم: ${cat.name_ar} ✅`);
    }

    // -------------------------------------------------------------------------
    // دوال حفظ وتعديل الإعلان Lightbox & Saving
    // -------------------------------------------------------------------------
    function markAdDirty(idx) {
      const saveBtn = document.getElementById(`saveBtn-${idx}`);
      if (saveBtn) {
        saveBtn.style.boxShadow = '0 0 10px rgba(59, 130, 246, 0.7)';
      }
    }

    function openImageLightbox(src, title, price, id) {
      const modal = document.getElementById('imageLightboxModal');
      const img = document.getElementById('lightboxImg');
      const caption = document.getElementById('lightboxTitle');
      if (!modal || !img) return;

      img.src = src;
      if (caption) {
        caption.textContent = `${title || 'معاينة الصورة'} ${price ? ' - ' + price : ''} ${id ? ' (' + id + ')' : ''}`;
      }
      modal.style.display = 'flex';
    }

    function closeImageLightbox() {
      const modal = document.getElementById('imageLightboxModal');
      if (modal) modal.style.display = 'none';
    }

    function openLightboxFromPickerRef() {
      const refImg = document.getElementById('pickerRefImage');
      if (refImg && refImg.src) {
        openImageLightbox(refImg.src, refImg.dataset.title || 'معاينة صورة الإعلان', refImg.dataset.price || '');
      }
    }

    async function saveAdChanges(idx) {
      const ad = adsData[idx];
      if (!ad) return;

      const saveBtn = document.getElementById(`saveBtn-${idx}`);
      const saveBtnText = document.getElementById(`saveBtnText-${idx}`);
      const origText = 'حفظ التعديلات';

      // 1. قراءة العنوان
      const titleInp = document.getElementById(`titleInp-${idx}`);
      if (titleInp && titleInp.value.trim()) {
        ad.clean_title = titleInp.value.trim();
        ad.title = ad.clean_title;
      }

      // 2. قراءة السعر والعملة
      const priceInp = document.getElementById(`priceInp-${idx}`);
      const currencySel = document.getElementById(`currencySel-${idx}`);
      const amt = (priceInp && priceInp.value !== '') ? Number(priceInp.value) : null;
      const curr = currencySel ? currencySel.value : 'SYP';
      ad.price_info = {
        amount: amt,
        currency: curr
      };

      // 3. قراءة المدينة والمنطقة
      const citySel = document.getElementById(`citySel-${idx}`);
      const areaInp = document.getElementById(`areaInp-${idx}`);
      if (citySel) {
        const cityId = Number(citySel.value);
        const cityName = citySel.options[citySel.selectedIndex]?.dataset.name || citySel.options[citySel.selectedIndex]?.text || 'دمشق';
        ad['id-citie'] = cityId;
        ad.city_name = cityName;
        ad.location_detected = cityName;
      }
      if (areaInp) {
        ad.sub_district_name = areaInp.value.trim();
      }

      // 4. قراءة الهاتف واسم المعلن
      const phoneInp = document.getElementById(`phoneInp-${idx}`);
      if (phoneInp) {
        ad.phone_number = phoneInp.value.trim();
      }
      const publisherInp = document.getElementById(`publisherInp-${idx}`);
      if (publisherInp) {
        ad.publisher_name = publisherInp.value.trim();
      }

      // 5. قراءة نص الوصف
      const descInp = document.getElementById(`descInp-${idx}`);
      if (descInp) {
        ad.clean_description = descInp.value.trim();
        ad.description = ad.clean_description;
      }

      if (saveBtn) {
        saveBtn.disabled = true;
        saveBtn.style.opacity = '0.7';
        if (saveBtnText) saveBtnText.textContent = 'جاري الحفظ... ⏳';
      }

      try {
        const res = await apiFetch('/api/save_ad', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ index: idx, ad: ad })
        });
        const data = await res.json();
        if (data.success) {
          if (saveBtn) {
            saveBtn.style.background = 'linear-gradient(135deg, #059669, #10b981)';
            saveBtn.style.borderColor = '#10b981';
            saveBtn.style.boxShadow = 'none';
            if (saveBtnText) saveBtnText.textContent = 'تم الحفظ بنجاح! ✅';
          }
          setTimeout(() => {
            if (saveBtn) {
              saveBtn.disabled = false;
              saveBtn.style.opacity = '1';
              saveBtn.style.background = 'linear-gradient(135deg, #1d4ed8, #2563eb)';
              saveBtn.style.borderColor = '#3b82f6';
              if (saveBtnText) saveBtnText.textContent = origText;
            }
          }, 2000);
          SyncStatusManager.success('تم حفظ وتثبيت تعديلات الإعلان بنجاح ✅');
        } else {
          alert(data.message || 'فشل حفظ التعديلات');
          if (saveBtn) {
            saveBtn.disabled = false;
            saveBtn.style.opacity = '1';
            if (saveBtnText) saveBtnText.textContent = origText;
          }
        }
      } catch (err) {
        console.error("Save ad error:", err);
        alert("تعذر الاتصال بالسيرفر لحفظ التعديلات: " + err);
        if (saveBtn) {
          saveBtn.disabled = false;
          saveBtn.style.opacity = '1';
          if (saveBtnText) saveBtnText.textContent = origText;
        }
      }
    }


    function escapeHtml(str) {
      if (str === null || str === undefined) return '';
      return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
    }

    function updateServerStatusBadge(online) {
      isServerConnected = online;
      const badge = document.getElementById('serverStatusBadge');
      const banner = document.getElementById('serverAlertBanner');
      if (online) {
        if (badge) {
          badge.className = 'badge badge-success';
          badge.innerHTML = '🟢 السيرفر متصل (5000)';
        }
        if (banner) banner.style.display = 'none';
      } else {
        if (badge) {
          badge.className = 'badge badge-danger';
          badge.innerHTML = '🔴 السيرفر غير متصل';
        }
        if (banner) banner.style.display = 'flex';
      }
    }

    async function apiFetch(endpoint, options = {}) {
      const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;
      try {
        const res = await fetch(url, options);
        updateServerStatusBadge(true);
        return res;
      } catch (err) {
        updateServerStatusBadge(false);
        console.warn(`[Connection Info] Unable to connect to ${url}`);
        throw err;
      }
    }

    function switchTab(tabId, el) {
      document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
      const targetTab = document.getElementById(tabId);
      if (targetTab) targetTab.classList.add('active');
      if (el) el.classList.add('active');
      if (tabId === 'tab-links') {
        if (!groupsData || groupsData.length === 0) loadGroups();
      }
      if (tabId === 'tab-review') {
        if (!adsData || adsData.length === 0) loadAllAds();
        else renderAdsGrid();
      }
      if (tabId === 'tab-published') {
        if (!publishedAdsData || publishedAdsData.length === 0) loadPublishedAds();
        else renderPublishedGrid();
      }
      if (tabId === 'tab-flagged') {
        if (!flaggedAdsData || flaggedAdsData.length === 0) loadFlaggedAds();
        else renderFlaggedGrid();
      }
    }

    async function init() {
      await checkServerConnection(false);

      // فحص دوري تلقائي لإعادة الاتصال ومتابعة السحب والمنجر
      setInterval(async () => {
        if (!isServerConnected) {
          try {
            const res = await apiFetch('/api/config');
            if (res.ok) {
              await checkServerConnection(false);
            }
          } catch (e) {}
        } else {
          pollScraperStatus();
          checkManagerStatus();
        }
      }, 4000);
    }

    async function checkServerConnection(isManual = false) {
      try {
        const testRes = await apiFetch('/api/config');
        if (!testRes.ok) throw new Error("Server offline");

        await loadConfig();
        await loadGroups();
        await loadAllAds();
        pollScraperStatus();
        checkManagerStatus();
        fetchUpdateInfo();
        fetchAiQuotaInfo(false);
        updateServerStatusBadge(true);
        if (isManual) alert("تم الاتصال بالسيرفر بنجاح! 🟢");
      } catch (e) {
        updateServerStatusBadge(false);
        if (isManual) alert("تعذر الاتصال بالسيرفر! يرجى تشغيل start_app.bat أو Lelbai_Launcher.exe أولاً.");
      }
    }

    // تشغيل وفتح لوحة الإدارة (المنجر) وكافة سيرفراتها
    async function launchManager() {
      const btn = document.getElementById('btnLaunchManager');
      const dot = document.getElementById('managerStatusDot');
      const origText = btn ? btn.innerHTML : '';

      const currentHost = (window.location.hostname && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1')
        ? window.location.hostname
        : 'localhost';
      let targetUrl = dot ? (dot.getAttribute('data-url') || `http://${currentHost}:8002`) : `http://${currentHost}:8002`;

      // إذا كانت سيرفرات الإدارة تعمل مسبقاً، افتح الصفحة فوراً في تبويب جديد دون أي تأخير
      if (dot && dot.getAttribute('data-online') === 'true') {
        window.open(targetUrl, '_blank');
        return;
      }

      if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<span>⏳ جاري تشغيل سيرفرات الإدارة...</span>`;
      }
      
      try {
        const res = await fetch(`${API_BASE}/api/launch_manager`, { method: 'POST' });
        const data = await res.json();
        if (data.success) {
          if (data.url) {
            targetUrl = data.url;
            if (currentHost !== 'localhost' && !targetUrl.includes('://')) {
              targetUrl = targetUrl.replace('localhost', currentHost).replace('127.0.0.1', currentHost);
            }
          }
          if (dot) {
            dot.style.background = '#10b981';
            dot.style.boxShadow = '0 0 8px #10b981';
            dot.setAttribute('data-online', 'true');
            dot.setAttribute('data-url', targetUrl);
            dot.title = `صفحة الإدارة متصلة وجاهزة (${targetUrl})`;
          }
          const win = window.open(targetUrl, '_blank');
          if (!win) {
            alert(`✅ تم تشغيل سيرفر الإدارة بنجاح!\nيرجى السماح بالنوافذ المنبثقة أو فتح الرابط التالي مباشرة:\n${targetUrl}`);
          }
        } else if (data.php_missing) {
          alert(data.message || "⚠️ يلزم توفر بيئة PHP على الجهاز لتشغيل لوحة تحكم المنجر.");
        } else if (data.not_installed) {
          alert(data.message || "🔒 ملفات المنجر غير متوفرة داخل هذا المجلد.");
        } else {
          alert("⚠️ " + (data.message || "فشل تشغيل سيرفرات الإدارة."));
        }
      } catch (err) {
        alert("تعذر الاتصال بسيرفر لوحة التحكم المحلي (تأكد من تشغيل السيرفر أولاً)");
      } finally {
        if (btn) {
          btn.disabled = false;
          btn.innerHTML = origText;
        }
        checkManagerStatus();
      }
    }

    // فحص حالة سيرفر الإدارة دورياً وتحديث الروابط حسب الجهاز المتصل
    async function checkManagerStatus() {
      const dot = document.getElementById('managerStatusDot');
      const btn = document.getElementById('btnLaunchManager');
      if (!dot) return;

      const currentHost = (window.location.hostname && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1')
        ? window.location.hostname
        : 'localhost';
      let defaultUrl = `http://${currentHost}:8002`;

      try {
        const res = await fetch(`${API_BASE}/api/manager_status`);
        const data = await res.json();
        const activeUrl = data.manager_url || defaultUrl;
        dot.setAttribute('data-url', activeUrl);

        if (data.manager_running) {
          dot.style.background = '#10b981';
          dot.style.boxShadow = '0 0 8px #10b981';
          dot.setAttribute('data-online', 'true');
          dot.title = `صفحة الإدارة متصلة وجاهزة (${activeUrl}) - انقر للفتح المباشر`;
          if (btn) {
            btn.title = `صفحة الإدارة تعمل بنشاط. انقر للفتح المباشر في المتصفح (${activeUrl})`;
          }
        } else {
          dot.style.background = '#ef4444';
          dot.style.boxShadow = '0 0 8px #ef4444';
          dot.setAttribute('data-online', 'false');
          if (data.is_installed === false) {
            dot.title = 'ملفات المنجر غير مثبتة على هذا الجهاز. انقر للمساعدة في الربط بالكمبيوتر الأول';
            if (btn) {
              btn.title = 'ملفات المنجر غير مثبتة محلياً. انقر للمساعدة في الربط بالكمبيوتر الأول';
            }
          } else {
            dot.title = 'سيرفر الإدارة متوقف حالياً. انقر للتشغيل';
            if (btn) {
              btn.title = 'تشغيل لوحة تحكم الإدارة (المنجر) والسيرفرات وفتح الصفحة';
            }
          }
        }
      } catch (e) {
        dot.style.background = '#6b7280';
        dot.setAttribute('data-online', 'false');
        dot.title = 'السيرفر غير متصل';
      }
    }

    // جلب تاريخ آخر تحديث للنظام
    async function fetchUpdateInfo() {
      const lbl = document.getElementById('lblLastUpdate');
      if (!lbl) return;
      try {
        const res = await fetch(`${API_BASE}/api/update_info`);
        const data = await res.json();
        if (data.last_updated_at && data.last_updated_at !== 'غير محدد') {
          let dtStr = data.last_updated_at.split(' ')[0] + ' ' + (data.last_updated_at.split(' ')[1] || '').substring(0, 5);
          if (data.relative_time) {
            dtStr += ` (${data.relative_time})`;
          }
          lbl.innerText = dtStr;
        } else {
          lbl.innerText = "أحدث إصدار";
        }
      } catch (e) {
        lbl.innerText = "--";
      }
    }

    // التحقق من التحديثات من GitHub
    async function checkSystemUpdates() {
      const lbl = document.getElementById('lblLastUpdate');
      const oldText = lbl ? lbl.innerText : '';
      if (lbl) lbl.innerText = "جاري الفحص...";
      try {
        const res = await fetch(`${API_BASE}/api/check_update`, { method: 'POST' });
        const data = await res.json();
        alert(data.message || (data.success ? "النظام محدث بالكامل!" : "لا يمكن التحديث حالياً"));
        fetchUpdateInfo();
      } catch (e) {
        alert("تعذر الاتصال للتحقق من التحديثات.");
        if (lbl) lbl.innerText = oldText;
      }
    }

    async function loadConfig() {
      try {
        const res = await apiFetch('/api/config');
        const cfg = await res.json();
        document.getElementById('setGeminiKey').value = cfg.gemini_api_key || '';
        document.getElementById('setWebUrl').value = cfg.website_api_url || '';
        document.getElementById('setWebKey').value = cfg.website_api_key || '';
        const mInp = document.getElementById('setManagerUrl');
        if (mInp) mInp.value = cfg.manager_url || '';
      } catch (e) {}
    }

    async function loadGroups() {
      try {
        const res = await apiFetch('/api/groups');
        groupsData = await res.json();
        document.getElementById('stTotalLinks').innerText = groupsData.length;

        populateCustomGroupSelect();
        updateScrapeStartPreview();

        const tbody = document.getElementById('groupsTableBody');
        if (groupsData.length === 0) {
          tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:30px; color:var(--text-muted);">لا توجد روابط محفوظة حالياً. اضغط "إضافة رابط جديد" للبدء.</td></tr>`;
          return;
        }

        tbody.innerHTML = groupsData.map((g, idx) => `
          <tr style="${g.is_smart_start ? 'background:rgba(5,150,105,0.08);' : ''}">
            <td style="font-weight:700;">${idx+1}</td>
            <td>
              <div style="font-weight:800; color:#f8fafc; display:flex; align-items:center; gap:6px; flex-wrap:wrap;">
                <span>${g.name}</span>
                ${g.is_last_added ? '<span class="badge" style="background:#7c3aed; color:#fff; font-size:10px; padding:2px 8px; border-radius:6px;">🆕 آخر صفحة انضافت</span>' : ''}
                ${g.is_last_scraped ? '<span class="badge" style="background:#0284c7; color:#fff; font-size:10px; padding:2px 8px; border-radius:6px;">🕒 آخر صفحة مسحوبة</span>' : ''}
                ${g.is_smart_start ? '<span class="badge" style="background:#059669; color:#fff; font-size:10px; padding:2px 8px; border-radius:6px;">🎯 نقطة الانطلاق</span>' : ''}
              </div>
              <a href="${g.url}" target="_blank" style="font-size:11px; color:#60a5fa; text-decoration:none;">🔗 فتح المجموعة</a>
            </td>
            <td><span class="badge badge-info">${g.category || 'عام'}</span></td>
            <td style="font-weight:700; color:#38bdf8;">🕒 ${g.last_scraped_at || 'لم يُسحب بعد'}</td>
            <td style="font-weight:700; color:#34d399;">${g.last_ads_count || 0} إعلان</td>
            <td style="font-weight:700;">${g.total_ads_count || 0} إعلان</td>
            <td><span class="badge ${g.status==='قيد السحب'?'badge-warning':'badge-success'}">${g.status || 'جاهز'}</span></td>
            <td>
              <div style="display:flex; gap:6px;">
                <button class="btn btn-sm btn-success" onclick="scrapeSingleGroup('${g.url}')">⚡ سحب الآن</button>
                <button class="btn btn-danger btn-sm" onclick="deleteGroup(${g.id})">🗑️</button>
              </div>
            </td>
          </tr>
        `).join('');
      } catch (e) {}
    }

    let adsLimit = 60;

    function getAdRealIndex(ad, fallbackIdx) {
      if (!ad) return fallbackIdx;
      if (typeof ad._rawIndex === 'number' && ad._rawIndex >= 0 && adsData[ad._rawIndex] === ad) {
        return ad._rawIndex;
      }
      const i = adsData.indexOf(ad);
      if (i !== -1) {
        ad._rawIndex = i;
        return i;
      }
      if (ad.ad_url) {
        const found = adsData.findIndex(a => a && a.ad_url === ad.ad_url);
        if (found !== -1) {
          ad._rawIndex = found;
          return found;
        }
      }
      if (ad.clean_title) {
        const found = adsData.findIndex(a => a && a.clean_title === ad.clean_title);
        if (found !== -1) {
          ad._rawIndex = found;
          return found;
        }
      }
      return fallbackIdx;
    }

    async function loadAllAds(silent = false) {
      const grid = document.getElementById('adsCardsGrid');
      try {
        if (!silent && adsData.length === 0 && grid) {
          grid.innerHTML = `<div style="grid-column:1/-1; text-align:center; padding:50px; color:#60a5fa; font-weight:800; font-size:16px;">⏳ جاري تجهيز وعرض الإعلانات...</div>`;
        }
        const res = await apiFetch('/api/ads');
        if (!res.ok) throw new Error("تعذر جلب الإعلانات من السيرفر (" + res.status + ")");
        const data = await res.json();
        adsData = Array.isArray(data.pending) ? data.pending : [];
        adsData.forEach((a, i) => { if (a && typeof a === 'object') a._rawIndex = i; });
        if (Array.isArray(data.published)) {
          publishedAdsData = data.published;
        }
        
        const badgePending = document.getElementById('badgePending');
        if (badgePending) badgePending.innerText = adsData.length;
        
        const pubCount = data.published_count !== undefined ? data.published_count : (publishedAdsData ? publishedAdsData.length : 0);
        const badgePub = document.getElementById('badgePublished');
        if (badgePub) badgePub.innerText = pubCount;
        const stPub = document.getElementById('stPublishedAds');
        if (stPub) stPub.innerText = pubCount;
        
        const fCount = data.flagged_count || 0;
        const stFlagged = document.getElementById('stFlaggedAds');
        if (stFlagged) stFlagged.innerText = fCount;
        const badgeFlagged = document.getElementById('badgeFlagged');
        if (badgeFlagged) badgeFlagged.innerText = fCount;

        const readyCount = adsData.filter(a => a && a.evaluation && a.evaluation.is_ready_to_publish).length;
        const stReady = document.getElementById('stReadyAds');
        if (stReady) stReady.innerText = readyCount;

        renderAdsGrid();
        if (publishedAdsData && publishedAdsData.length > 0) {
          renderPublishedGrid();
        }
      } catch (e) {
        console.error("Error loading ads:", e);
        if (grid && (!silent || adsData.length === 0)) {
          grid.innerHTML = `
            <div style="grid-column:1/-1; text-align:center; padding:50px 20px; background:var(--card-bg); border-radius:16px; border:1px solid #ef4444; color:#f87171;">
              <div style="font-size:32px; margin-bottom:10px;">⚠️</div>
              <div style="font-weight:800; font-size:16px; margin-bottom:6px;">تعذر تحميل وتجهيز الإعلانات حالياً</div>
              <div style="font-size:12px; color:var(--text-muted); margin-bottom:16px;">${escapeHtml(e.message || String(e))}</div>
              <button class="btn btn-primary" onclick="loadAllAds(false)" style="padding:10px 22px; font-weight:800; font-size:13px;">🔄 إعادة المحاولة الآن</button>
            </div>
          `;
        }
      }
    }

    function filterAds(type, el) {
      currentFilter = type;
      adsLimit = 60;
      el.parentElement.querySelectorAll('button').forEach(b => b.classList.remove('active'));
      el.classList.add('active');
      renderAdsGrid();
    }

    function renderAdsGrid() {
      try {
        const grid = document.getElementById('adsCardsGrid');
        if (!grid) return;
        let filtered = Array.isArray(adsData) ? adsData : [];
        if (currentFilter === 'ready') filtered = filtered.filter(a => a && a.evaluation && a.evaluation.is_ready_to_publish);
        if (currentFilter === 'review') filtered = filtered.filter(a => a && (!a.evaluation || !a.evaluation.is_ready_to_publish));

        if (filtered.length === 0) {
          grid.innerHTML = `
            <div style="grid-column:1/-1; text-align:center; padding:60px 20px; background:var(--card-bg); border-radius:16px; color:var(--text-muted); border:1px solid var(--border);">
              <div style="font-size:36px; margin-bottom:12px;">📦</div>
              <div style="font-size:16px; font-weight:800; color:#f8fafc; margin-bottom:6px;">لا توجد إعلانات مطابقة لفلتر العرض حالياً</div>
              <div style="font-size:12px; color:var(--text-muted);">ابدأ السحب المتوازي من تبويب "تشغيل السحب المتوازي" لتظهر الإعلانات هنا فوراً وتلقائياً.</div>
            </div>
          `;
          return;
        }

        const visibleAds = filtered.slice(0, adsLimit);
        const cardsHtml = visibleAds.map((ad, vIdx) => {
          if (!ad) return '';
          const idx = getAdRealIndex(ad, vIdx);
          try {
            const ev = (typeof ad.evaluation === 'object' && ad.evaluation !== null) ? ad.evaluation : {};
            const sp = (typeof ev.specs_details === 'object' && ev.specs_details !== null) ? ev.specs_details : {};
            const sh = (typeof ev.sharia_details === 'object' && ev.sharia_details !== null) ? ev.sharia_details : {};

            const rawTitle = ad.clean_title || ad.title || (ad.description || '').substring(0, 60) || 'إعلان بدون عنوان';
            const title = String(rawTitle);
            const city = sp.city_name || ad.city_name || ad.location_detected || 'دمشق';
            const subDistClean = ad.sub_district_name || sp.sub_district_name || '';
            const cat = ad.category || 'عام';
            const catHierarchy = ad.category_hierarchy || `${cat} (ID: ${ad.leaf_category_id || 1143})`;
            const accountName = ad.publisher_name || 'أبو محمد الشامي';
            
            const priceInfo = (typeof ad.price_info === 'object' && ad.price_info !== null) ? ad.price_info : {};
            const priceNum = (priceInfo.amount !== undefined && priceInfo.amount !== null && !isNaN(Number(priceInfo.amount))) ? Number(priceInfo.amount) : '';
            const currCode = (priceInfo.currency === 'USD') ? 'USD' : 'SYP';
            const currSymbol = currCode === 'USD' ? '$' : 'ل.س';
            const priceDisplay = priceNum !== '' ? `${Number(priceNum).toLocaleString()} ${currSymbol}` : 'على السوم';
            
            const images = Array.isArray(ad.nimages) ? ad.nimages : [];
            const firstImg = images.length > 0 ? `${API_BASE}/imgs/${encodeURIComponent(images[0])}` : '';

            const adId = encodeURIComponent(String(ad.ad_url || ad.clean_title || (ad.description || '').substring(0, 30)));
            const thumbsHtml = images.map((img, i) => `
              <div class="ad-thumb-wrapper">
                <img src="${API_BASE}/imgs/${encodeURIComponent(img)}" class="ad-thumb ${i===0?'active':''}" onclick="const mainImg=document.getElementById('adMainImg-${idx}'); if(mainImg) mainImg.src='${API_BASE}/imgs/${encodeURIComponent(img)}'" onerror="this.style.display='none'" />
                <button type="button" class="del-thumb-btn" title="حذف هذه الصورة نهائياً" onclick="deleteAdImage('${adId}', '${encodeURIComponent(img)}', ${idx}, event)">✕</button>
              </div>
            `).join('');

            // أشرطة الفحص
            const specsStatusHtml = sp.has_images && sp.has_desc && sp.has_phone ? 
              `<span style="color:#34d399;">✔️ مكتمل (${sp.images_count || images.length} صور + هاتف + وصف + موقع)</span>` :
              `<span style="color:#f87171;">⚠️ ناقص بعض الحقول</span>`;

            const shFlags = Array.isArray(sh.flags) ? sh.flags : [];
            const summaryStr = sh.summary || ad.moderation_summary || '';
            const isAiDone = Boolean(ad.ai_evaluated || ev.is_ai_evaluated);
            let shariaStatusHtml = '';
            if (sh.is_safe) {
              if (isAiDone) {
                shariaStatusHtml = `<span style="color:#34d399; font-weight:800;" title="${escapeHtml(summaryStr)}">🟢 مطابق للضوابط (Gemini Vision API)</span>`;
              } else {
                shariaStatusHtml = `<span style="color:#facc15; font-weight:700;" title="الإعلان بانتظار فحص الرؤية الذكية">⏳ بانتظار فحص AI (Gemini)</span>`;
              }
            } else {
              shariaStatusHtml = `<span style="color:#f87171; font-weight:800;" title="${escapeHtml(summaryStr)}">🚫 ملاحظة رقابية: ${escapeHtml(shFlags.join(', ') || summaryStr || 'بحاجة لمراجعة')}</span>`;
            }

            const dupStatusHtml = ad.is_duplicate ?
              `<span style="color:#ef4444; font-weight:700;">⚠️ مكرر مسبقاً على الموقع</span>` :
              `<span style="color:#34d399; font-weight:700;">✔️ جديد كلياً (غير مكرر)</span>`;

            const readyBadgeHtml = ev.is_ready_to_publish ?
              `<span class="badge badge-success" style="font-size:12px;">🚀 جاهز للنشر الفوري</span>` :
              `<span class="badge badge-warning" style="font-size:12px;">⏳ بحاجة لمراجعة</span>`;

            // استخراج بادجات المواصفات الفنية
            const specsObj = (typeof ad.specifications === 'object' && ad.specifications !== null) ? ad.specifications : {};
            const specItems = [];
            if (specsObj.make) specItems.push(`🏢 الشركة: ${specsObj.make}`);
            if (specsObj.model) specItems.push(`🚗 الطراز: ${specsObj.model}`);
            if (specsObj.year) specItems.push(`📅 سنة: ${specsObj.year}`);
            if (specsObj.transmission) specItems.push(`⚙️ الكير: ${specsObj.transmission}`);
            if (specsObj.fuel_type) specItems.push(`⛽ الوقود: ${specsObj.fuel_type}`);
            if (specsObj.condition) specItems.push(`✨ الهيكل: ${specsObj.condition}`);
            if (specsObj.color) specItems.push(`🎨 اللون: ${specsObj.color}`);
            if (specsObj.mileage) specItems.push(`📟 ممشى: ${specsObj.mileage}`);
            if (specsObj.area) specItems.push(`📐 مساحة: ${specsObj.area}`);
            if (specsObj.rooms) specItems.push(`🚪 غرف: ${specsObj.rooms}`);
            if (Array.isArray(specsObj.features) && specsObj.features.length) specItems.push(`⭐ ميزات: ${specsObj.features.slice(0, 3).join(', ')}`);

            const specsBadgesHtml = specItems.length > 0 ? `
              <div style="display:flex; flex-wrap:wrap; gap:4px; margin:6px 0;">
                ${specItems.map(s => `<span style="background:rgba(56,189,248,0.12); color:#38bdf8; border:1px solid rgba(56,189,248,0.25); border-radius:6px; padding:2px 6px; font-size:10px; font-weight:700;">${escapeHtml(s)}</span>`).join('')}
              </div>
            ` : '';

            // تقرير الذكاء الاصطناعي
            const aiReviewText = (ad.ai_review && ad.ai_review.full_text) ? 
              ad.ai_review.full_text : 
              (ad.moderation_summary || 'تم فحص وتدقيق الإعلان ومطابقته للضوابط الشرعية والشكلية.');

            const descText = ad.clean_description || ad.description || 'لا يوجد وصف متاح';

            // خيارات المدن السورية
            const activeCityId = Number(ad['id-citie'] || 1);
            const cityOptionsHtml = SYRIAN_CITIES.map(c => {
              const isSel = (c.id === activeCityId || (!ad['id-citie'] && (city.includes(c.name) || c.name.includes(city)))) ? 'selected' : '';
              return `<option value="${c.id}" data-name="${c.name}" ${isSel}>${c.name}</option>`;
            }).join('');

            return `
              <div class="ad-card" id="adCard-${idx}">
                <div class="ad-gallery">
                  <img id="adMainImg-${idx}" src="${firstImg}" onerror="this.src='https://placehold.co/600x400/1e293b/f8fafc?text=No+Image'" onclick="openImageLightbox('${firstImg}', '${escapeHtml(title)}', '${priceDisplay}', '#${idx+1}')" style="cursor:zoom-in;" title="انقر لتكبير الصورة" />
                  <div class="ad-thumbs">${thumbsHtml}</div>
                </div>

                <div class="ad-body">
                  
                  <!-- زر اختيار وتعديل التصنيف التفاعلي الهرمي -->
                  <div style="margin-bottom:4px;">
                    <label style="font-size:11px; color:var(--text-muted); font-weight:700; display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                      <span>🏷️ تصنيف الإعلان (القسم الهرمي):</span>
                      <span style="color:#38bdf8; font-size:10px; cursor:pointer;" onclick="openCategoryPickerForAd(${idx})">انقر للتغيير ▾</span>
                    </label>
                    <button type="button" class="btn-category-select" onclick="openCategoryPickerForAd(${idx})" title="انقر لاختيار وتصفح القسم الهرمي المناسب لمواصفات هذا الإعلان">
                      <div style="display:flex; align-items:center; gap:8px; overflow:hidden;">
                        <span class="cat-pill-icon"><i class="fa-solid fa-layer-group"></i></span>
                        <span class="cat-pill-text" id="catDisplay-${idx}">${escapeHtml(catHierarchy)}</span>
                      </div>
                      <span class="cat-pill-badge"><i class="fa-solid fa-pen-to-square"></i> تغيير القسم ▾</span>
                    </button>
                  </div>

                  <!-- صندوق المراحل التفصيلي -->
                  <div class="verification-box">
                    <div class="pillar-row">
                      <span class="pillar-label">1️⃣ المواصفات والبيانات:</span>
                      ${specsStatusHtml}
                    </div>
                    <div class="pillar-row">
                      <span class="pillar-label">2️⃣ الفحص الشرعي والرقابي:</span>
                      ${shariaStatusHtml}
                    </div>
                    <div class="pillar-row">
                      <span class="pillar-label">3️⃣ عدم التكرار على الموقع:</span>
                      ${dupStatusHtml}
                    </div>
                    <div class="pillar-row">
                      <span class="pillar-label">4️⃣ حالة الجاهزية للنشر:</span>
                      ${readyBadgeHtml}
                    </div>
                  </div>

                  <!-- بادجات المواصفات المستخرجة -->
                  ${specsBadgesHtml}

                  <!-- رد وتقرير الذكاء الاصطناعي الشامل قابل للطي -->
                  <details style="background:rgba(99,102,241,0.08); border:1px solid rgba(99,102,241,0.3); border-radius:10px; padding:8px 12px; margin:4px 0;">
                    <summary style="font-size:11px; font-weight:800; color:#a5b4fc; cursor:pointer; display:flex; align-items:center; justify-content:space-between;">
                      <span>🤖 رد وتقرير فحص الذكاء الاصطناعي (Gemini)</span>
                      <span style="color:#34d399; font-size:10px;">عرض/طي ▾</span>
                    </summary>
                    <div style="font-size:11px; color:#cbd5e1; line-height:1.55; white-space:pre-line; background:rgba(15,23,42,0.65); padding:8px 10px; border-radius:6px; font-family:monospace; border:1px solid rgba(255,255,255,0.05); margin-top:8px;">${escapeHtml(aiReviewText)}</div>
                  </details>

                  <!-- حقول التعديل المباشرة (Inputs) لكافة بيانات الإعلان -->
                  <div class="ad-edit-fields">
                    
                    <!-- حقل 1: العنوان المهيكل -->
                    <div class="form-group" style="margin:0;">
                      <label style="font-size:11px; color:#93c5fd; font-weight:700; margin-bottom:3px; display:block;">📝 العنوان المهيكل:</label>
                      <input type="text" class="ad-title-input" id="titleInp-${idx}" value="${escapeHtml(title)}" placeholder="عنوان الإعلان..." oninput="markAdDirty(${idx})" />
                    </div>

                    <!-- حقل 2: السعر والعملة -->
                    <div style="display:grid; grid-template-columns: 2fr 1fr; gap:8px;">
                      <div class="form-group" style="margin:0;">
                        <label style="font-size:11px; color:#fde047; font-weight:700; margin-bottom:3px; display:block;">💰 السعر:</label>
                        <input type="number" class="form-control" id="priceInp-${idx}" value="${priceNum}" placeholder="السعر رقماً..." oninput="markAdDirty(${idx})" />
                      </div>
                      <div class="form-group" style="margin:0;">
                        <label style="font-size:11px; color:var(--text-muted); font-weight:700; margin-bottom:3px; display:block;">العملة:</label>
                        <select class="form-control" id="currencySel-${idx}" onchange="markAdDirty(${idx})">
                          <option value="SYP" ${currCode === 'SYP' ? 'selected' : ''}>ل.س (سوري)</option>
                          <option value="USD" ${currCode === 'USD' ? 'selected' : ''}>$ (دولار)</option>
                        </select>
                      </div>
                    </div>

                    <!-- حقل 3: المدينة والمنطقة -->
                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px;">
                      <div class="form-group" style="margin:0;">
                        <label style="font-size:11px; color:#60a5fa; font-weight:700; margin-bottom:3px; display:block;">📍 المدينة:</label>
                        <select class="form-control" id="citySel-${idx}" onchange="markAdDirty(${idx})">
                          ${cityOptionsHtml}
                        </select>
                      </div>
                      <div class="form-group" style="margin:0;">
                        <label style="font-size:11px; color:var(--text-muted); font-weight:700; margin-bottom:3px; display:block;">المنطقة / الحي:</label>
                        <input type="text" class="form-control" id="areaInp-${idx}" value="${escapeHtml(subDistClean)}" placeholder="مثال: المزة، الصالحية..." oninput="markAdDirty(${idx})" />
                      </div>
                    </div>

                    <!-- حقل 4: رقم الهاتف والمعلن -->
                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px;">
                      <div class="form-group" style="margin:0;">
                        <label style="font-size:11px; color:#38bdf8; font-weight:700; margin-bottom:3px; display:block;">📞 رقم الهاتف:</label>
                        <input type="text" class="form-control" id="phoneInp-${idx}" value="${escapeHtml(ad.phone_number || '')}" placeholder="09xxxxxxxx" dir="ltr" oninput="markAdDirty(${idx})" />
                      </div>
                      <div class="form-group" style="margin:0;">
                        <label style="font-size:11px; color:#c084fc; font-weight:700; margin-bottom:3px; display:block;">👤 اسم المعلن:</label>
                        <input type="text" class="form-control" id="publisherInp-${idx}" value="${escapeHtml(accountName)}" placeholder="اسم المعلن..." oninput="markAdDirty(${idx})" />
                      </div>
                    </div>

                    <!-- حقل 5: الوصف الكامل -->
                    <div class="form-group" style="margin:0;">
                      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:3px;">
                        <label style="font-size:11px; color:var(--text-muted); font-weight:700;">📄 نص الوصف والمواصفات:</label>
                        <a href="${escapeHtml(ad.ad_url || '#')}" target="_blank" style="font-size:10px; color:#60a5fa; text-decoration:none;">🔗 فتح فيسبوك الأصل</a>
                      </div>
                      <textarea class="ad-desc-textarea" id="descInp-${idx}" rows="3" placeholder="اكتب أو عدل نص الوصف..." oninput="markAdDirty(${idx})">${escapeHtml(descText)}</textarea>
                    </div>

                  </div>

                  <!-- شريط أزرار الإجراءات مع زر الحفظ البارز -->
                  <div style="display:flex; gap:6px; margin-top:auto; padding-top:10px; border-top:1px solid var(--border); flex-wrap:wrap;">
                    <button id="saveBtn-${idx}" class="btn btn-primary" style="flex:1; min-width:130px; font-weight:800; background:linear-gradient(135deg, #1d4ed8, #2563eb); border:1px solid #3b82f6; display:flex; align-items:center; justify-content:center; gap:6px;" onclick="saveAdChanges(${idx})" title="حفظ وتثبيت التعديلات المدخلة فورياً">
                      <span>💾</span> <span id="saveBtnText-${idx}">حفظ التعديلات</span>
                    </button>
                    <button id="pubBtn-${idx}" class="btn btn-success" style="flex:1.2; min-width:140px; font-weight:800;" onclick="publishSingleAd(${idx})">✅ نشر للموقع ومجلد الاستيراد</button>
                    <button id="aiBtn-${idx}" class="btn btn-outline btn-sm" style="border-color:#38bdf8; color:#38bdf8; font-weight:700;" onclick="reclassifySingleAd(${idx})" title="إعادة فحص وتصنيف الإعلان بالذكاء الاصطناعي (Gemini)">🤖 فحص AI</button>
                    <button id="rejBtn-${idx}" class="btn btn-warning btn-sm" onclick="rejectSingleAd(${idx})" title="استبعاد الإعلان ونقله للمخالفات">⚠️ استبعاد</button>
                    <button id="delBtn-${idx}" class="btn btn-danger btn-sm" onclick="deleteSingleAd(${idx})" title="حذف نهائي للإعلان وصوره من الجهاز">🗑️ حذف نهائي</button>
                  </div>

                </div>
              </div>
            `;
          } catch (cardErr) {
            console.error("Error rendering ad card at index", idx, cardErr);
            return `
              <div class="ad-card" id="adCard-${idx}" style="border:1px dashed #f59e0b; padding:20px; text-align:center;">
                <div style="color:#f59e0b; font-weight:800; margin-bottom:6px;">⚠️ تعذر عرض تفاصيل هذا الإعلان</div>
                <div style="font-size:11px; color:var(--text-muted);">${escapeHtml(ad.clean_title || ad.title || 'إعلان')}</div>
                <button class="btn btn-danger btn-sm" style="margin-top:10px;" onclick="deleteSingleAd(${idx})">🗑️ حذف</button>
              </div>
            `;
          }
        }).join('');

        let moreHtml = '';
        if (filtered.length > adsLimit) {
          moreHtml = `
            <div style="grid-column:1/-1; text-align:center; padding:24px; background:var(--card-inner); border-radius:14px; border:1px solid var(--border); margin-top:15px; display:flex; justify-content:center; align-items:center; gap:12px; flex-wrap:wrap;">
              <button class="btn btn-primary" onclick="adsLimit += 60; renderAdsGrid();" style="padding:12px 24px; font-weight:800; font-size:14px;">
                📥 عرض المزيد من الإعلانات (+60) [المعروض حالياً ${visibleAds.length} من ${filtered.length}]
              </button>
              <button class="btn btn-outline" onclick="adsLimit = filtered.length; renderAdsGrid();" style="padding:12px 24px; font-weight:800; font-size:14px;">
                ⚡ عرض كافة الإعلانات دفعة واحدة (${filtered.length})
              </button>
            </div>
          `;
        }

        grid.innerHTML = cardsHtml + moreHtml;
      } catch (err) {
        console.error("renderAdsGrid error:", err);
        const grid = document.getElementById('adsCardsGrid');
        if (grid) {
          grid.innerHTML = `
            <div style="grid-column:1/-1; text-align:center; padding:40px; background:var(--card-bg); border-radius:16px; border:1px solid #ef4444; color:#f87171;">
              <div style="font-size:24px; margin-bottom:8px;">⚠️</div>
              <div style="font-weight:800; font-size:15px;">حدث خطأ أثناء عرض الإعلانات</div>
              <div style="font-size:12px; color:var(--text-muted); margin-top:6px;">${escapeHtml(err.message || String(err))}</div>
              <button class="btn btn-primary btn-sm" style="margin-top:12px;" onclick="renderAdsGrid()">🔄 إعادة المحاولة</button>
            </div>
          `;
        }
      }
    }

    const activePublishing = new Set();

    async function publishSingleAd(idx) {
      if (activePublishing.has(idx)) {
        return;
      }
      activePublishing.add(idx);

      const ad = adsData[idx];
      if (!ad) {
        activePublishing.delete(idx);
        return;
      }

      const btn = document.getElementById(`pubBtn-${idx}`);
      const rejBtn = document.getElementById(`rejBtn-${idx}`);
      const card = document.getElementById(`adCard-${idx}`);
      const origBtnText = btn ? btn.innerHTML : '';

      if (btn) {
        btn.disabled = true;
        btn.style.opacity = '0.7';
        btn.style.cursor = 'not-allowed';
        btn.innerHTML = '⏳ جاري النشر والرفع للموقع...';
      }
      if (rejBtn) {
        rejBtn.disabled = true;
      }

      // قراءة وتطبيق كافة الحقول المعدلة على ad فوراً قبل النشر
      const titleInp = document.getElementById(`titleInp-${idx}`);
      if (titleInp && titleInp.value.trim()) {
        ad.clean_title = titleInp.value.trim();
        ad.title = ad.clean_title;
      }
      const priceInp = document.getElementById(`priceInp-${idx}`);
      const currencySel = document.getElementById(`currencySel-${idx}`);
      if (priceInp || currencySel) {
        ad.price_info = {
          amount: (priceInp && priceInp.value !== '') ? Number(priceInp.value) : null,
          currency: currencySel ? currencySel.value : 'SYP'
        };
      }
      const citySel = document.getElementById(`citySel-${idx}`);
      const areaInp = document.getElementById(`areaInp-${idx}`);
      if (citySel) {
        ad['id-citie'] = Number(citySel.value);
        ad.city_name = citySel.options[citySel.selectedIndex]?.dataset.name || citySel.options[citySel.selectedIndex]?.text || 'دمشق';
        ad.location_detected = ad.city_name;
      }
      if (areaInp) {
        ad.sub_district_name = areaInp.value.trim();
      }
      const phoneInp = document.getElementById(`phoneInp-${idx}`);
      if (phoneInp) {
        ad.phone_number = phoneInp.value.trim();
      }
      const publisherInp = document.getElementById(`publisherInp-${idx}`);
      if (publisherInp) {
        ad.publisher_name = publisherInp.value.trim();
      }
      const descInp = document.getElementById(`descInp-${idx}`);
      if (descInp) {
        ad.clean_description = descInp.value.trim();
        ad.description = ad.clean_description;
      }

      try {
        const res = await apiFetch('/api/approve', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ ad })
        });
        const data = await res.json();

        if (data.success) {
          if (btn) {
            btn.innerHTML = '✅ تم النشر بنجاح!';
            btn.style.background = '#059669';
          }
          if (card) {
            card.style.transition = 'all 0.4s ease';
            card.style.opacity = '0';
            card.style.transform = 'scale(0.95)';
          }
          if (data.message) {
            alert(data.message);
          }
          await loadAllAds();
          await loadPublishedAds();
        } else {
          alert(data.message || 'حدث خطأ أثناء النشر');
          if (btn) {
            btn.disabled = false;
            btn.style.opacity = '1';
            btn.style.cursor = 'pointer';
            btn.innerHTML = origBtnText;
          }
          if (rejBtn) {
            rejBtn.disabled = false;
          }
        }
      } catch (e) {
        alert("تعذر الاتصال بالسيرفر! تأكد من تشغيل start_app.bat");
        if (btn) {
          btn.disabled = false;
          btn.style.opacity = '1';
          btn.style.cursor = 'pointer';
          btn.innerHTML = origBtnText;
        }
        if (rejBtn) {
          rejBtn.disabled = false;
        }
      } finally {
        activePublishing.delete(idx);
      }
    }

    async function rejectSingleAd(idx) {
      const ad = adsData[idx];
      const rejBtn = document.getElementById(`rejBtn-${idx}`);
      const pubBtn = document.getElementById(`pubBtn-${idx}`);
      if (rejBtn) rejBtn.disabled = true;
      if (pubBtn) pubBtn.disabled = true;

      try {
        await apiFetch('/api/reject', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ ad })
        });
        loadAllAds();
      } catch (e) {
        alert("تعذر الاتصال بالسيرفر! تأكد من تشغيل start_app.bat");
        if (rejBtn) rejBtn.disabled = false;
        if (pubBtn) pubBtn.disabled = false;
      }
    }

    async function deleteAdImage(adIdentifier, imgNameEncoded, cardIndex, event) {
      if (event) {
        event.stopPropagation();
        event.preventDefault();
      }
      if (!confirm("هل أنت متأكد من رغبتك في حذف هذه الصورة من الإعلان نهائياً؟")) return;

      const imgName = decodeURIComponent(imgNameEncoded);
      const cleanAdId = decodeURIComponent(adIdentifier);
      try {
        const res = await apiFetch('/api/delete_ad_image', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            image_name: imgName,
            ad_url: cleanAdId,
            clean_title: cleanAdId,
            ad_index: cardIndex
          })
        });
        const data = await res.json();
        if (data.success) {
          if (adsData[cardIndex]) {
            if (data.ad) {
              adsData[cardIndex] = data.ad;
            } else if (data.remaining_images) {
              adsData[cardIndex].nimages = data.remaining_images;
            }
          }
          renderAdsGrid();
        } else {
          alert(data.message || 'فشل حذف الصورة');
        }
      } catch (e) {
        alert("تعذر حذف الصورة: " + e);
      }
    }

    async function bulkPublishReady() {
      if (!confirm("هل تريد تصدير ونشر كافة الإعلانات الجاهزة للنشر الآن؟")) return;
      try {
        const res = await apiFetch('/api/bulk_approve', { method: 'POST' });
        const data = await res.json();
        alert(data.message);
        loadAllAds();
        loadPublishedAds();
      } catch (e) {
        alert("تعذر الاتصال بالسيرفر! تأكد من تشغيل start_app.bat");
      }
    }

    async function reclassifySingleAd(idx) {
      const ad = adsData[idx];
      if (!ad) return;
      const btn = document.getElementById(`aiBtn-${idx}`);
      if (btn) { btn.disabled = true; btn.innerText = '⏳ جاري الفحص...'; }
      try {
        const res = await apiFetch('/api/reclassify_ad_with_ai', {
          method: 'POST',
          body: JSON.stringify({ ad_index: idx, ad: ad })
        });
        const data = await res.json();
        if (data.success && data.ad) {
          adsData[idx] = data.ad;
          adsData[idx]._rawIndex = idx;
          renderAdsGrid();
          alert(data.message || 'تمت إعادة الفحص والتصنيف بنجاح! 🤖');
        } else {
          alert(data.message || 'تعذر إعادة التصنيف بالذكاء الاصطناعي');
        }
      } catch (err) {
        alert('خطأ أثناء الفحص: ' + err);
      } finally {
        if (btn) { btn.disabled = false; btn.innerText = '🤖 فحص AI'; }
      }
    }

    async function reclassifyAllAdsWithAi() {
      if (!adsData.length) {
        alert('لا توجد إعلانات حالياً في قائمة المراجعة!');
        return;
      }
      if (!confirm(`هل تريد إعادة فحص وتصنيف كافة الإعلانات (${adsData.length}) باستخدام الذكاء الاصطناعي (Gemini Vision API)؟`)) return;
      const overlay = document.createElement('div');
      overlay.style = 'position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.75); z-index:99999; display:flex; justify-content:center; align-items:center; color:#fff; font-size:18px; font-weight:800; flex-direction:column; gap:16px;';
      overlay.innerHTML = '<div>⏳ جاري فحص وتصنيف الإعلانات بالذكاء الاصطناعي... يرجى الانتظار</div>';
      document.body.appendChild(overlay);
      try {
        const res = await apiFetch('/api/reclassify_all_with_ai', { method: 'POST' });
        const data = await res.json();
        alert(data.message);
        await loadAllAds();
      } catch (e) {
        alert('خطأ أثناء الفحص الجماعي: ' + e);
      } finally {
        if (document.body.contains(overlay)) {
          document.body.removeChild(overlay);
        }
      }
    }

    async function loadPublishedAds() {
      try {
        const res = await apiFetch('/api/published_ads');
        const data = await res.json();
        publishedAdsData = data.published || [];
        const count = publishedAdsData.length;
        const badgePub = document.getElementById('badgePublished');
        if (badgePub) badgePub.innerText = count;
        const stPub = document.getElementById('stPublishedAds');
        if (stPub) stPub.innerText = count;
        const pubListCount = document.getElementById('publishedListCount');
        if (pubListCount) pubListCount.innerText = count;
        filterPublishedAds();
      } catch (e) {}
    }

    function filterPublishedAds() {
      const q = (document.getElementById('searchPublishedInput')?.value || '').trim().toLowerCase();
      const cat = (document.getElementById('filterPublishedCat')?.value || '').trim();

      filteredPublished = publishedAdsData.filter(ad => {
        const title = (ad.clean_title || ad.title || '').toLowerCase();
        const desc = (ad.clean_description || ad.description || '').toLowerCase();
        const phone = (ad.phone_number || '').toLowerCase();
        const pubName = (ad.publisher_name || '').toLowerCase();
        const city = (ad.city_name || ad.location_detected || '').toLowerCase();
        const category = (ad.category || ad.category_hierarchy || '').toLowerCase();

        const matchQ = !q || title.includes(q) || desc.includes(q) || phone.includes(q) || pubName.includes(q) || city.includes(q) || category.includes(q);
        const matchCat = !cat || category.includes(cat.toLowerCase());
        return matchQ && matchCat;
      });

      renderPublishedGrid();
    }

    function renderPublishedGrid() {
      try {
        const grid = document.getElementById('publishedCardsGrid');
        if (!grid) return;

        const hasFilter = (document.getElementById('searchPublishedInput')?.value || '').trim() || (document.getElementById('filterPublishedCat')?.value || '').trim();
        const list = hasFilter ? filteredPublished : publishedAdsData;

        if (!list || list.length === 0) {
          grid.innerHTML = `<div style="grid-column:1/-1; text-align:center; padding:60px; background:var(--card-bg); border-radius:16px; color:var(--text-muted);">
            <div style="font-size:36px; margin-bottom:12px;">📭</div>
            <div style="font-size:16px; font-weight:800; color:#f8fafc;">لا توجد إعلانات منشورة حتى الآن مطابقة للبحث!</div>
            <div style="font-size:13px; margin-top:8px; color:var(--text-muted);">عندما تقوم بنشر الإعلانات من تبويب "مراجعة ونشر الإعلانات"، ستظهر تلقائياً هنا في هذه القائمة المنفصلة.</div>
          </div>`;
          return;
        }

        grid.innerHTML = list.map((ad, idx) => {
          if (!ad) return '';
          const rawTitle = ad.clean_title || ad.title || (ad.description || '').substring(0, 60) || 'إعلان منشور';
          const title = String(rawTitle);
          const city = ad.city_name || ad.location_detected || 'دمشق';
          const subDist = ad.sub_district_name && ad.sub_district_name !== 'عام' ? ` (${ad.sub_district_name})` : '';
          const cat = ad.category || 'عام';
          const catHierarchy = ad.category_hierarchy || `${cat} (ID: ${ad.leaf_category_id || 1143})`;
          const accountName = ad.publisher_name || 'أبو محمد الشامي';
          const currSymbol = (ad.price_info && ad.price_info.currency === 'USD') ? '$' : 'ل.س';
          const price = ad.price_info && ad.price_info.amount ? `${Number(ad.price_info.amount).toLocaleString()} ${currSymbol}` : 'السعر: على السوم';
          const pubDate = ad.published_at || 'تاريخ غير محدد';

          const images = Array.isArray(ad.nimages) ? ad.nimages : [];
          const firstImg = images.length > 0 ? `${API_BASE}/imgs/${encodeURIComponent(images[0])}` : '';

          const thumbsHtml = images.map((img, i) => `
            <img src="${API_BASE}/imgs/${encodeURIComponent(img)}" class="ad-thumb ${i===0?'active':''}" onclick="const pubMain=document.getElementById('pubMainImg-${idx}'); if(pubMain) pubMain.src='${API_BASE}/imgs/${encodeURIComponent(img)}'" onerror="this.style.display='none'" />
          `).join('');

          // بادجات المواصفات الفنية
          const specsObj = (typeof ad.specifications === 'object' && ad.specifications !== null) ? ad.specifications : {};
          const specItems = [];
          if (specsObj.make) specItems.push(`🏢 الشركة: ${specsObj.make}`);
          if (specsObj.model) specItems.push(`🚗 الطراز: ${specsObj.model}`);
          if (specsObj.year) specItems.push(`📅 سنة: ${specsObj.year}`);
          if (specsObj.transmission) specItems.push(`⚙️ الكير: ${specsObj.transmission}`);
          if (specsObj.fuel_type) specItems.push(`⛽ الوقود: ${specsObj.fuel_type}`);
          if (specsObj.condition) specItems.push(`✨ الهيكل: ${specsObj.condition}`);
          if (specsObj.color) specItems.push(`🎨 اللون: ${specsObj.color}`);
          if (specsObj.mileage) specItems.push(`📟 ممشى: ${specsObj.mileage}`);
          if (specsObj.area) specItems.push(`📐 مساحة: ${specsObj.area}`);
          if (specsObj.rooms) specItems.push(`🚪 غرف: ${specsObj.rooms}`);
          if (Array.isArray(specsObj.features) && specsObj.features.length) specItems.push(`⭐ ميزات: ${specsObj.features.slice(0, 3).join(', ')}`);

          const specsBadgesHtml = specItems.length > 0 ? `
            <div style="display:flex; flex-wrap:wrap; gap:4px; margin:6px 0;">
              ${specItems.map(s => `<span style="background:rgba(56,189,248,0.12); color:#38bdf8; border:1px solid rgba(56,189,248,0.25); border-radius:6px; padding:2px 6px; font-size:10px; font-weight:700;">${escapeHtml(s)}</span>`).join('')}
            </div>
          ` : '';

          const aiReviewText = (ad.ai_review && ad.ai_review.full_text) ? 
            ad.ai_review.full_text : 
            (ad.moderation_summary || 'تم فحص وتدقيق الإعلان ومطابقته للضوابط الشرعية والشكلية وتم نشره.');

          const descText = ad.clean_description || ad.description || 'لا يوجد وصف متاح';

          return `
            <div class="ad-card" id="pubCard-${idx}" style="border: 1px solid rgba(139,92,246,0.35); box-shadow: 0 4px 20px rgba(139,92,246,0.08);">
              <div class="ad-gallery">
                <img id="pubMainImg-${idx}" src="${firstImg}" onerror="this.src='https://placehold.co/600x400/1e293b/f8fafc?text=No+Image'" />
                <div class="ad-thumbs">${thumbsHtml}</div>
              </div>

              <div class="ad-body">
                <!-- شريط الحالة وتاريخ النشر -->
                <div style="display:flex; justify-content:space-between; align-items:center; font-size:11px; margin-bottom:8px; flex-wrap:wrap; gap:4px; border-bottom:1px solid rgba(255,255,255,0.06); padding-bottom:6px;">
                  <span class="badge badge-success" style="font-size:11px;">✅ تم النشر وتصدير الملفات</span>
                  <span style="color:#a78bfa; font-weight:700;">🕒 ${escapeHtml(pubDate)}</span>
                </div>

                <!-- التصنيف بأصغر ابن واسم الحساب -->
                <div style="display:flex; justify-content:space-between; align-items:center; font-size:12px; font-weight:800; margin-bottom:6px; flex-wrap:wrap; gap:4px;">
                  <span style="background:rgba(37,99,235,0.2); color:#60a5fa; padding:3px 8px; border-radius:6px; border:1px solid rgba(59,130,246,0.3);">🏷️ ${escapeHtml(catHierarchy)}</span>
                  <span style="color:#c084fc; background:rgba(168,85,247,0.15); padding:3px 8px; border-radius:6px; border:1px solid rgba(168,85,247,0.3);">👤 المعلن: ${escapeHtml(accountName)}</span>
                </div>

                <!-- العنوان -->
                <div style="font-size:14px; font-weight:800; color:#f8fafc; line-height:1.4; margin:4px 0;">${escapeHtml(title)}</div>

                <!-- بادجات المواصفات -->
                ${specsBadgesHtml}

                <!-- الموقع والسعر -->
                <div style="display:flex; justify-content:space-between; font-size:12px; font-weight:700; margin:6px 0;">
                  <span style="color:#60a5fa;">📍 ${escapeHtml(city)}${escapeHtml(subDist)}</span>
                  <span style="color:#fde047;">💰 ${escapeHtml(price)}</span>
                </div>

                <!-- صندوق الوصف -->
                <div class="ad-desc-box">${escapeHtml(descText)}</div>

                <!-- الهاتف ورابط فيسبوك -->
                <div style="display:flex; justify-content:space-between; align-items:center; font-size:13px; font-weight:700; color:#38bdf8; margin:6px 0;">
                  <span>📞 ${escapeHtml(ad.phone_number || 'لا يوجد')}</span>
                  <a href="${escapeHtml(ad.ad_url || '#')}" target="_blank" style="font-size:11px; color:#60a5fa; text-decoration:none; display:inline-flex; align-items:center; gap:4px;">🔗 فتح المنشور في فيسبوك</a>
                </div>

                <!-- تقرير الفحص والذكاء الاصطناعي -->
                <div style="background:rgba(99,102,241,0.06); border:1px solid rgba(99,102,241,0.25); border-radius:8px; padding:8px 10px; margin:6px 0;">
                  <div style="font-size:10px; font-weight:800; color:#a5b4fc; margin-bottom:4px; display:flex; justify-content:space-between;">
                    <span>🤖 تقرير الذكاء الاصطناعي المعتمد:</span>
                    <span style="color:#34d399;">✔️ مُدقق ومُعتمد</span>
                  </div>
                  <div style="font-size:10px; color:#cbd5e1; line-height:1.5; white-space:pre-line; max-height:80px; overflow-y:auto; font-family:monospace;">${escapeHtml(aiReviewText)}</div>
                </div>

                <!-- أزرار الإجراءات الخاصة بالإعلان المنشور -->
                <div style="display:flex; gap:8px; margin-top:auto; padding-top:10px; border-top:1px solid var(--border);">
                  <button class="btn btn-outline btn-sm" style="flex:1;" onclick="openImportFolder()">📂 فتح مجلد الاستيراد</button>
                  <button class="btn btn-warning btn-sm" onclick="revertPublishedAd(${idx})" title="إلغاء النشر وإعادة الإعلان للمسودة">🔄 إعادة للمراجعة</button>
                  <button class="btn btn-danger btn-sm" onclick="deletePublishedAd(${idx})" title="حذف من سجل المنشورات">🗑️</button>
                </div>

              </div>
            </div>
          `;
        }).join('');
      } catch (err) {
        console.error("renderPublishedGrid error:", err);
      }
    }

    async function openImportFolder() {
      try {
        const res = await apiFetch('/api/open_folder', { method: 'POST' });
        const data = await res.json();
        if (!data.success) {
          alert("المجلد موجود على سطح المكتب: إعلانات_للاستيراد");
        }
      } catch (e) {
        alert("المجلد موجود على سطح المكتب باسم: إعلانات_للاستيراد");
      }
    }

    async function revertPublishedAd(idx) {
      const hasFilter = (document.getElementById('searchPublishedInput')?.value || '').trim() || (document.getElementById('filterPublishedCat')?.value || '').trim();
      const list = hasFilter ? filteredPublished : publishedAdsData;
      const ad = list[idx];
      if (!ad) return;
      if (!confirm(`هل أنت متأكد من إعادة إعلان "${(ad.clean_title || '').substring(0, 30)}..." إلى قائمة المراجعة؟`)) return;
      try {
        await apiFetch('/api/revert_ad', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ ad })
        });
        await loadAllAds();
        await loadPublishedAds();
        alert("تمت إعادة الإعلان إلى قائمة المراجعة بنجاح! 🔄");
      } catch (e) {
        alert("تعذر الاتصال بالسيرفر!");
      }
    }

    async function deletePublishedAd(idx) {
      const hasFilter = (document.getElementById('searchPublishedInput')?.value || '').trim() || (document.getElementById('filterPublishedCat')?.value || '').trim();
      const list = hasFilter ? filteredPublished : publishedAdsData;
      const ad = list[idx];
      if (!ad) return;
      if (!confirm(`هل أنت متأكد من حذف هذا الإعلان نهائياً من سجل المنشورات؟`)) return;
      try {
        await apiFetch('/api/delete_published', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ ad })
        });
        await loadAllAds();
        await loadPublishedAds();
      } catch (e) {
        alert("تعذر الاتصال بالسيرفر!");
      }
    }

    let flaggedAdsData = [];

    async function loadFlaggedAds() {
      try {
        const grid = document.getElementById('flaggedCardsGrid');
        if (flaggedAdsData.length === 0 && grid) {
          grid.innerHTML = `<div style="grid-column:1/-1; text-align:center; padding:50px; color:#f87171; font-weight:800; font-size:16px;">⏳ جاري تحميل الإعلانات المحظورة وأسباب الحظر...</div>`;
        }
        const res = await apiFetch('/api/flagged_ads');
        const data = await res.json();
        flaggedAdsData = data.flagged || [];
        const count = flaggedAdsData.length;
        
        const badgeFlagged = document.getElementById('badgeFlagged');
        if (badgeFlagged) badgeFlagged.innerText = count;
        const stFlagged = document.getElementById('stFlaggedAds');
        if (stFlagged) stFlagged.innerText = count;
        const flaggedListCount = document.getElementById('flaggedListCount');
        if (flaggedListCount) flaggedListCount.innerText = count;

        renderFlaggedGrid();
      } catch (e) {
        console.error("Error loading flagged ads:", e);
      }
    }

    function renderFlaggedGrid() {
      const grid = document.getElementById('flaggedCardsGrid');
      if (!grid) return;
      if (!flaggedAdsData || flaggedAdsData.length === 0) {
        grid.innerHTML = `
          <div style="grid-column:1/-1; text-align:center; padding:70px 20px; background:var(--card-inner); border-radius:14px; border:1px solid var(--border);">
            <div style="font-size:36px; margin-bottom:12px;">🛡️</div>
            <div style="font-size:16px; font-weight:800; color:#34d399; margin-bottom:6px;">سجل المحظورات نظيف تماماً!</div>
            <div style="font-size:13px; color:var(--text-muted);">كافة الإعلانات المسحوبة مطابقة للضوابط الشرعية والقانونية ومجتازة لفحص الرؤية البصرية (Gemini Vision).</div>
          </div>
        `;
        return;
      }

      grid.innerHTML = flaggedAdsData.map((ad, idx) => {
        const title = ad.clean_title || ad.title || (ad.description || '').substring(0, 50) || 'إعلان بدون عنوان';
        const phone = ad.phone_number || 'لا يوجد هاتف';
        const desc = ad.clean_description || ad.description || 'لا يوجد تفاصيل';
        const city = ad.city_name || ad.location_detected || 'سوريا';
        const date = ad.extracted_at || 'حديثاً';
        const reason = ad.rejection_reason || ad.moderation_summary || 'مخالفة لضوابط النشر والرقابة الشرعية';
        const flags = Array.isArray(ad.flags) ? ad.flags : [];
        const images = Array.isArray(ad.nimages) ? ad.nimages : [];
        const firstImg = images.length > 0 ? `${API_BASE}/imgs/${encodeURIComponent(images[0])}` : '';

        return `
          <div class="ad-card" id="flagCard-${idx}" style="border:1px solid rgba(239,68,68,0.45); box-shadow:0 4px 20px rgba(239,68,68,0.12);">
            <div class="ad-gallery" style="position:relative;">
              <img src="${firstImg || 'https://placehold.co/600x400/450a0a/fca5a5?text=Blocked+Ad'}" onerror="this.src='https://placehold.co/600x400/450a0a/fca5a5?text=Blocked+Ad'" />
              <div style="position:absolute; top:8px; right:8px; background:#dc2626; color:#fff; padding:4px 10px; border-radius:6px; font-size:11px; font-weight:800; box-shadow:0 2px 8px rgba(0,0,0,0.4);">
                🚫 إعلان محظور ومستبعد
              </div>
            </div>

            <div class="ad-body">
              <!-- شريط سبب الحظر الصادر من الذكاء الاصطناعي -->
              <div style="background:#450a0a; border:1px solid #ef4444; border-radius:10px; padding:12px; margin-bottom:10px;">
                <div style="font-weight:900; font-size:13px; color:#fee2e2; display:flex; align-items:center; gap:6px;">
                  <span>🚫 سبب الحظر:</span>
                  <span style="color:#fca5a5;">${escapeHtml(reason)}</span>
                </div>
                ${ad.moderation_summary && ad.moderation_summary !== reason ? `
                  <div style="font-size:11px; color:#fecaca; margin-top:4px; line-height:1.4;">
                    📝 تقرير الفحص: ${escapeHtml(ad.moderation_summary)}
                  </div>
                ` : ''}
                ${flags.length > 0 ? `
                  <div style="display:flex; gap:4px; flex-wrap:wrap; margin-top:8px;">
                    ${flags.map(f => `<span style="background:rgba(220,38,38,0.4); border:1px solid #dc2626; color:#fee2e2; padding:2px 8px; border-radius:4px; font-size:10px; font-weight:700;">⚠️ ${escapeHtml(f)}</span>`).join('')}
                  </div>
                ` : ''}
              </div>

              <!-- عنوان ومعلومات الإعلان -->
              <div style="font-weight:800; font-size:14px; color:#f87171; margin-bottom:4px; line-height:1.4;">
                ${escapeHtml(title)}
              </div>
              <div style="display:flex; justify-content:space-between; font-size:11px; color:var(--text-muted); margin-bottom:6px;">
                <span>📍 ${escapeHtml(city)}</span>
                <span>📅 ${escapeHtml(date)}</span>
              </div>
              <div class="ad-desc-box" style="border-color:rgba(239,68,68,0.25); max-height:80px;">${escapeHtml(desc)}</div>

              <div style="display:flex; justify-content:space-between; align-items:center; font-size:12px; font-weight:700; color:#38bdf8; margin-top:6px;">
                <span>📞 ${escapeHtml(phone)}</span>
                <a href="${escapeHtml(ad.ad_url || '#')}" target="_blank" style="font-size:11px; color:var(--text-muted); text-decoration:none;">🔗 رابط فيسبوك</a>
              </div>

              <!-- أزرار الإجراءات -->
              <div style="display:flex; gap:6px; margin-top:auto; padding-top:10px; border-top:1px solid var(--border); flex-wrap:wrap;">
                <button class="btn btn-success btn-sm" style="flex:1; min-width:130px;" onclick="unflagSingleAd(${idx})" title="إلغاء الحظر ونقل الإعلان إلى قائمة المراجعة">↩️ إلغاء الحظر للمراجعة</button>
                <button class="btn btn-outline btn-sm" style="border-color:#38bdf8; color:#38bdf8; font-weight:700;" onclick="recheckFlaggedAdWithAi(${idx})" title="إعادة فحص وتدقيق الإعلان مجدداً عبر Gemini Vision API">🤖 إعادة فحص AI</button>
                <button class="btn btn-danger btn-sm" onclick="deleteFlaggedSingleAd(${idx})" title="حذف نهائي للإعلان ومسح كافة صوره من الجهاز">🗑️ حذف نهائي</button>
              </div>

            </div>
          </div>
        `;
      }).join('');
    }

    async function unflagSingleAd(idx) {
      const ad = flaggedAdsData[idx];
      if (!ad) return;
      try {
        const res = await apiFetch('/api/unflag_ad', {
          method: 'POST',
          body: JSON.stringify({ ad_index: idx, ad })
        });
        const data = await res.json();
        alert(data.message || 'تم إلغاء الحظر ونقل الإعلان للمراجعة');
        await loadFlaggedAds();
        await loadAllAds();
      } catch (e) {
        alert("تعذر الاتصال بالسيرفر: " + e);
      }
    }

    async function recheckFlaggedAdWithAi(idx) {
      const ad = flaggedAdsData[idx];
      if (!ad) return;
      try {
        const res = await apiFetch('/api/reclassify_ad_with_ai', {
          method: 'POST',
          body: JSON.stringify({ ad_index: idx, ad, from_flagged: true })
        });
        const data = await res.json();
        if (data.success && data.ad) {
          if (data.ad.is_safe) {
            alert("🟢 نجح الفحص: الإعلان سليم ومطابق للضوابط وتم نقله لقائمة المراجعة للنشر!");
            await loadFlaggedAds();
            await loadAllAds();
          } else {
            alert(`🚫 نتيجة الفحص بالذكاء الاصطناعي: لا يزال محظوراً:\nالسبب: ${data.ad.rejection_reason || data.ad.moderation_summary}`);
            await loadFlaggedAds();
          }
        } else {
          alert(data.message || 'تعذر إعادة الفحص');
        }
      } catch (e) {
        alert("خطأ أثناء الفحص: " + e);
      }
    }

    async function deleteFlaggedSingleAd(idx) {
      const ad = flaggedAdsData[idx];
      if (!ad) return;
      if (!confirm(`هل أنت متأكد من حذف هذا الإعلان المحظور وصوره نهائياً من الجهاز؟`)) return;
      try {
        const res = await apiFetch('/api/delete_flagged_ad', {
          method: 'POST',
          body: JSON.stringify({ ad_index: idx, ad })
        });
        const data = await res.json();
        alert(data.message || 'تم حذف الإعلان');
        await loadFlaggedAds();
        await loadAllAds();
      } catch (e) {
        alert("تعذر الاتصال بالسيرفر: " + e);
      }
    }

    async function clearFlaggedAds() {
      if (!flaggedAdsData.length) {
        alert('سجل المحظورات فارغ بالفعل!');
        return;
      }
      if (!confirm(`هل أنت متأكد من تفريغ كافة الإعلانات المحظورة (${flaggedAdsData.length}) نهائياً؟`)) return;
      try {
        const res = await apiFetch('/api/clear_flagged_ads', { method: 'POST' });
        const data = await res.json();
        alert(data.message || 'تم تفريغ سجل المحظورات بنجاح');
        await loadFlaggedAds();
        await loadAllAds();
      } catch (e) {
        alert("تعذر الاتصال بالسيرفر: " + e);
      }
    }

    function normalizeGroupUrl(url) {
      if (!url) return '';
      let u = String(url).trim();
      if (u.indexOf('?') !== -1) u = u.split('?')[0];
      if (u.indexOf('#') !== -1) u = u.split('#')[0];
      u = u.replace(/\/+$/, '').toLowerCase();
      u = u.replace(/^https?:\/\//, '');
      u = u.replace(/^(www\.|m\.|web\.|mbasic\.|touch\.)/, '');
      return u.replace(/\/+$/, '');
    }

    function getOrderedGroupsForScraping(mode = 'smart', customUrl = null) {
      if (!groupsData || groupsData.length === 0) return [];
      let list = [...groupsData];

      let targetIdx = 0;
      if (customUrl) {
        const normCustom = normalizeGroupUrl(customUrl);
        const idx = list.findIndex(g => normalizeGroupUrl(g.url) === normCustom);
        if (idx !== -1) targetIdx = idx;
      } else if (mode === 'last_added') {
        const idx = list.findIndex(g => g.is_last_added);
        if (idx !== -1) targetIdx = idx;
      } else if (mode === 'last_scraped') {
        const idx = list.findIndex(g => g.is_last_scraped);
        if (idx !== -1) targetIdx = idx;
      } else if (mode === 'first') {
        targetIdx = 0;
      } else { // smart (تلقائي: من آخر صفحة انضافت أو سحبت)
        const idx = list.findIndex(g => g.is_smart_start);
        if (idx !== -1) targetIdx = idx;
      }

      return list.slice(targetIdx).concat(list.slice(0, targetIdx));
    }

    function updateScrapeStartPreview() {
      const modeSel = document.getElementById('scrapeStartMode');
      const customSel = document.getElementById('scrapeCustomGroupSelect');
      const infoBox = document.getElementById('scrapeStartGroupName');
      if (!modeSel || !infoBox) return;

      const mode = modeSel.value;
      if (customSel) {
        customSel.style.display = (mode === 'custom') ? 'block' : 'none';
      }

      const customUrl = (mode === 'custom' && customSel) ? customSel.value : null;
      const ordered = getOrderedGroupsForScraping(mode, customUrl);
      if (ordered.length > 0) {
        const first = ordered[0];
        let tag = '';
        if (first.is_last_added) tag = ' (🆕 آخر صفحة انضافت)';
        else if (first.is_last_scraped) tag = ' (🕒 آخر صفحة مسحوبة)';
        infoBox.innerHTML = `<b>${first.name}</b>${tag}`;
      } else {
        infoBox.innerText = 'لا توجد مجموعات محفوظة';
      }
    }

    function populateCustomGroupSelect() {
      const sel = document.getElementById('scrapeCustomGroupSelect');
      if (!sel) return;
      sel.innerHTML = groupsData.map(g => `<option value="${g.url}">${g.name} (${g.category || 'عام'})</option>`).join('');
    }

    function parseArabicInt(str, defaultVal = 0) {
      if (!str) return defaultVal;
      const arabicDigits = ['٠','١','٢','٣','٤','٥','٦','٧','٨','٩'];
      let s = String(str).replace(/[٠-٩]/g, d => arabicDigits.indexOf(d));
      let val = parseInt(s.replace(/[^0-9-]/g, ''));
      return isNaN(val) ? defaultVal : val;
    }

    async function startAllScraping() {
      if (!groupsData || groupsData.length === 0) {
        alert("يرجى إضافة روابط مجموعات أولاً!");
        return;
      }

      const modeSel = document.getElementById('scrapeStartMode');
      const startMode = modeSel ? modeSel.value : 'smart';
      const customSel = document.getElementById('scrapeCustomGroupSelect');
      const customUrl = (startMode === 'custom' && customSel) ? customSel.value : null;

      const orderedGroups = getOrderedGroupsForScraping(startMode, customUrl);
      const groupsUrls = orderedGroups.map(g => g.url);

      let rawTimeout = parseArabicInt(document.getElementById('inpTimeout').value, 60);
      if (rawTimeout < 20) rawTimeout = rawTimeout * 10;
      const timeoutSec = Math.max(45, rawTimeout);

      let rawMaxAds = parseArabicInt(document.getElementById('inpMaxAds').value, 100);
      if (rawMaxAds <= 0) rawMaxAds = 100;

      let rawConcurrent = parseArabicInt(document.getElementById('inpConcurrent').value, 4);
      rawConcurrent = Math.max(1, Math.min(5, rawConcurrent));

      const params = {
        groups: groupsUrls,
        start_mode: startMode,
        start_url: customUrl || (orderedGroups[0] ? orderedGroups[0].url : null),
        concurrent_tabs: rawConcurrent,
        max_ads_per_group: rawMaxAds,
        timeout_seconds: timeoutSec,
        import_dir: document.getElementById('inpImportDir').value.trim()
      };

      const btnStart = document.getElementById('btnStartScraping');
      const btnStop = document.getElementById('btnStopScraping');
      if (btnStart) btnStart.style.display = 'none';
      if (btnStop) btnStop.style.display = 'inline-flex';
      const logBox = document.getElementById('liveLogsContainer');
      if (logBox) logBox.innerHTML = `[${new Date().toLocaleTimeString()}] 🚀 جاري تشغيل المتصفح وإطلاق السحب المتوازي (${rawConcurrent} تبويبات)...`;

      try {
        const res = await apiFetch('/api/start', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(params)
        });
        const data = await res.json();
        if (!data.success) {
          alert(data.message || "تعذر بدء السحب.");
          if (btnStart) btnStart.style.display = 'inline-flex';
          if (btnStop) btnStop.style.display = 'none';
        } else {
          setTimeout(pollScraperStatus, 600);
          setTimeout(pollScraperStatus, 1800);
        }
      } catch (e) {
        alert("تعذر الاتصال بالسيرفر! تأكد من تشغيل start_app.bat");
        if (btnStart) btnStart.style.display = 'inline-flex';
        if (btnStop) btnStop.style.display = 'none';
      }
    }

    async function stopAllScraping() {
      try {
        await apiFetch('/api/stop', { method: 'POST' });
      } catch (e) {}
    }

    async function scrapeSingleGroup(url) {
      let rawTimeout = parseArabicInt(document.getElementById('inpTimeout').value, 60);
      if (rawTimeout < 20) rawTimeout = rawTimeout * 10;
      const timeoutSec = Math.max(45, rawTimeout);

      let rawMaxAds = parseArabicInt(document.getElementById('inpMaxAds').value, 100);
      if (rawMaxAds <= 0) rawMaxAds = 100;

      const params = {
        groups: [url],
        concurrent_tabs: 1,
        max_ads_per_group: rawMaxAds,
        timeout_seconds: timeoutSec,
        import_dir: document.getElementById('inpImportDir').value.trim()
      };
      try {
        await apiFetch('/api/start', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(params)
        });
        switchTab('tab-scraper', document.querySelectorAll('.nav-btn')[1]);
        setTimeout(pollScraperStatus, 600);
        setTimeout(pollScraperStatus, 1800);
      } catch (e) {
        alert("تعذر الاتصال بالسيرفر! تأكد من تشغيل start_app.bat");
      }
    }

    async function pollScraperStatus() {
      try {
        const res = await apiFetch('/api/status');
        const st = await res.json();
        
        const btnStart = document.getElementById('btnStartScraping');
        const btnStop = document.getElementById('btnStopScraping');
        if (btnStart && btnStop) {
          if (st.is_running) {
            btnStart.style.display = 'none';
            btnStop.style.display = 'inline-flex';
          } else {
            btnStart.style.display = 'inline-flex';
            btnStop.style.display = 'none';
          }
        }

        const tabsBox = document.getElementById('activeTabsLiveList');
        if (tabsBox) {
          const keys = Object.keys(st.active_tabs || {});
          if (keys.length === 0) {
            tabsBox.innerHTML = `<div style="font-size:12px; color:var(--text-muted); text-align:center; padding:10px;">لا توجد تبويبات نشطة حالياً</div>`;
          } else {
            tabsBox.innerHTML = keys.map(k => `
              <div style="display:flex; justify-content:space-between; background:var(--card-inner); padding:8px 12px; border-radius:8px; font-size:12px; font-weight:700;">
                <div>⚡ تبويب ${parseInt(k)+1}: <span style="color:#60a5fa;">مجموعة [${st.active_tabs[k].group_idx}]</span></div>
                <div style="color:#34d399;">${st.active_tabs[k].status}</div>
              </div>
            `).join('');
          }
        }

        if (st.pending_count !== undefined) {
          const bp = document.getElementById('badgePending');
          if (bp) bp.innerText = st.pending_count;
          const sra = document.getElementById('stReadyAds');
          if (sra) sra.innerText = st.ready_count || 0;
          const spa = document.getElementById('stPublishedAds');
          if (spa) spa.innerText = st.published_count || 0;
          const sfa = document.getElementById('stFlaggedAds');
          if (sfa) sfa.innerText = st.flagged_count || 0;

          // تحديث حي فوري لشبكة الإعلانات إذا تم سحب إعلانات جديدة أثناء تواجد المستخدم في تبويب المراجعة
          const reviewTab = document.getElementById('tab-review');
          if (reviewTab && reviewTab.classList.contains('active')) {
            if (st.pending_count !== adsData.length) {
              loadAllAds(true);
            }
          }
        }

        if (st.gemini_usage) {
          try { updateAiQuotaUI(st.gemini_usage); } catch(err){}
        }

        if (st.logs && st.logs.length > 0) {
          const logBox = document.getElementById('liveLogsContainer');
          if (logBox) {
            logBox.innerHTML = st.logs.join('<br>');
            logBox.scrollTop = logBox.scrollHeight;
          }
        }
      } catch (e) {}
    }

    function openAddGroupModal() {
      document.getElementById('addGroupModal').style.display = 'flex';
    }
    function closeAddGroupModal() {
      document.getElementById('addGroupModal').style.display = 'none';
    }

    async function saveNewGroup() {
      const name = document.getElementById('mGrpName').value.trim();
      const url = document.getElementById('mGrpUrl').value.trim();
      const cat = document.getElementById('mGrpCat').value;
      if (!name || !url) {
        alert("يرجى إدخال اسم ورابط المجموعة!");
        return;
      }

      // فحص مسبق لمنع تكرار إضافة نفس الصفحة مرتين
      const normInput = normalizeGroupUrl(url);
      const duplicate = groupsData.find(g => normalizeGroupUrl(g.url) === normInput);
      if (duplicate) {
        alert(`❌ لا يمكن إضافة نفس الصفحة مرتين!\nهذا الرابط مضاف مسبقاً باسم: "${duplicate.name}"`);
        return;
      }

      try {
        const res = await apiFetch('/api/add_group', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ name, url, category: cat })
        });
        const data = await res.json();
        if (data.success) {
          closeAddGroupModal();
          document.getElementById('mGrpName').value = '';
          document.getElementById('mGrpUrl').value = '';
          await loadGroups();
          alert("✅ تمت إضافة الصفحة بنجاح!");
        } else {
          alert(data.message || "❌ فشل إضافة الرابط.");
        }
      } catch (e) {
        alert("تعذر الاتصال بالسيرفر! يرجى تشغيل start_app.bat");
      }
    }

    async function deleteGroup(id) {
      if (!confirm("هل أنت متأكد من حذف هذا الرابط؟")) return;
      try {
        await apiFetch('/api/delete_group', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ id })
        });
        loadGroups();
      } catch (e) {
        alert("تعذر الاتصال بالسيرفر! يرجى تشغيل start_app.bat");
      }
    }

    async function saveSettings() {
      const webKeyVal = document.getElementById('setWebKey').value.trim();
      const webUrlVal = document.getElementById('setWebUrl').value.trim();
      const managerUrlVal = document.getElementById('setManagerUrl') ? document.getElementById('setManagerUrl').value.trim() : '';
      const cfg = {
        gemini_api_key: document.getElementById('setGeminiKey').value.trim(),
        website_api_url: webUrlVal || 'https://api.lelbai.com/public/api/listings',
        website_api_key: webKeyVal || '67|5181926855ca52522dec3990517f272b027b745f',
        manager_url: managerUrlVal
      };
      try {
        await apiFetch('/api/config', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(cfg)
        });
        alert("تم حفظ الإعدادات بنجاح! ✅");
        checkManagerStatus();
      } catch (e) {
        alert("تعذر الاتصال بالسيرفر! يرجى تشغيل start_app.bat");
      }
    }

    async function openLoginBrowser() {
      const btn = document.getElementById("btnLogin") || document.querySelector("button[onclick='openLoginBrowser()']");
      const oldHtml = btn ? btn.innerHTML : '🔐 تسجيل دخول فيسبوك';
      if (btn) btn.innerHTML = '⏳ جاري تشغيل المتصفح...';
      try {
        const res = await apiFetch('/api/login', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
          if (btn) {
            btn.innerHTML = '🟢 المتصفح مفتوح أمامك الآن';
            btn.style.borderColor = '#10b981';
            btn.style.color = '#10b981';
            setTimeout(() => {
              btn.innerHTML = oldHtml;
              btn.style.borderColor = '';
              btn.style.color = '';
            }, 12000);
          }
        } else {
          alert(data.message || "حدث خطأ أثناء فتح المتصفح.");
          if (btn) btn.innerHTML = oldHtml;
        }
      } catch (e) {
        alert("تعذر الاتصال بالسيرفر! يرجى تشغيل start_app.bat");
        if (btn) btn.innerHTML = oldHtml;
      }
    }

    async function deleteSingleAd(idx) {
      const ad = adsData[idx];
      if (!ad) return;
      if (!confirm(`هل أنت متأكد من حذف هذا الإعلان نهائياً ومسح صوره من الجهاز؟`)) return;
      try {
        const res = await apiFetch('/api/delete_ad', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ ad, ad_index: idx })
        });
        const data = await res.json();
        if (data.success) {
          adsData.splice(idx, 1);
          adsData.forEach((a, i) => { if (a && typeof a === 'object') a._rawIndex = i; });
          renderAdsGrid();
          loadAllAds();
        } else {
          alert(data.message || 'فشل حذف الإعلان');
        }
      } catch (e) {
        alert("تعذر الاتصال بالسيرفر! يرجى تشغيل start_app.bat");
      }
    }

    async function clearAllPendingAds() {
      if (!confirm("⚠️ هل أنت متأكد تماماً من تفريغ ومسح كافة الإعلانات غير المنشورة (المسودات) ومسح صورها نهائياً؟")) return;
      try {
        const res = await apiFetch('/api/clear_pending_ads', { method: 'POST' });
        const data = await res.json();
        alert(data.message || "تم مسح كافة الإعلانات بنجاح!");
        await loadAllAds();
      } catch (e) {
        alert("تعذر الاتصال بالسيرفر! يرجى تشغيل start_app.bat");
      }
    }

    async function clearAllGroups() {
      if (!confirm("⚠️ هل أنت متأكد من مسح وتفريغ كافة روابط المجموعات المحفوظة؟")) return;
      try {
        const res = await apiFetch('/api/clear_groups', { method: 'POST' });
        const data = await res.json();
        alert(data.message || "تم تفريغ كافة الروابط بنجاح!");
        await loadGroups();
      } catch (e) {
        alert("تعذر الاتصال بالسيرفر! يرجى تشغيل start_app.bat");
      }
    }

    async function loadStarterGroups() {
      if (!confirm("هل تريد استيراد قائمة الروابط المقترحة لمجموعات سورية نشطة؟")) return;
      try {
        const res = await apiFetch('/api/load_starter_groups', { method: 'POST' });
        const data = await res.json();
        alert(data.message || "تم استيراد الروابط المقترحة بنجاح!");
        await loadGroups();
      } catch (e) {
        alert("تعذر الاتصال بالسيرفر! يرجى تشغيل start_app.bat");
      }
    }

    async function clearPublishedAds() {
      if (!confirm("⚠️ هل أنت متأكد من مسح وتفريغ سجل الإعلانات المنشورة؟")) return;
      try {
        const res = await apiFetch('/api/clear_published_ads', { method: 'POST' });
        const data = await res.json();
        alert(data.message || "تم تفريغ سجل المنشورات بنجاح!");
        await loadPublishedAds();
        await loadAllAds();
      } catch (e) {
        alert("تعذر الاتصال بالسيرفر! يرجى تشغيل start_app.bat");
      }
    }

    async function clearFlaggedAds() {
      if (!confirm("هل أنت متأكد من مسح سجل الإعلانات المستبعدة (المخالفة)؟")) return;
      try {
        const res = await apiFetch('/api/clear_flagged_ads', { method: 'POST' });
        const data = await res.json();
        alert(data.message || "تم تفريغ سجل الإعلانات المستبعدة بنجاح!");
        await loadAllAds();
      } catch (e) {
        alert("تعذر الاتصال بالسيرفر! يرجى تشغيل start_app.bat");
      }
    }

    async function clearAllImages() {
      if (!confirm("⚠️ تحذير: هل أنت متأكد من تنظيف وحذف كافة الصور المحملة من مجلد الصور على القرص؟")) return;
      try {
        const res = await apiFetch('/api/clear_all_images', { method: 'POST' });
        const data = await res.json();
        alert(data.message || "تم تنظيف الصور بنجاح!");
      } catch (e) {
        alert("تعذر الاتصال بالسيرفر! يرجى تشغيل start_app.bat");
      }
    }

    async function resetAllSystemData() {
      const confirmation = prompt("⚠️ تنبيه خطير: سيتم تصفير المنظومة بالكامل ومسح كافة الإعلانات والمنشورات والمخالفات والصور والبدء من الصفر تماماً!\nللتأكيد، اكتب كلمة (تصفير) في المربع أدناه:");
      if (confirmation !== "تصفير") {
        alert("تم إلغاء عملية التصفير.");
        return;
      }
      try {
        const res = await apiFetch('/api/reset_all_data', { method: 'POST' });
        const data = await res.json();
        alert(data.message || "تمت إعادة ضبط المنظومة بنجاح!");
        await loadAllAds();
        await loadPublishedAds();
        await loadGroups();
      } catch (e) {
        alert("تعذر الاتصال بالسيرفر! يرجى تشغيل start_app.bat");
      }
    }

    async function fetchAiQuotaInfo(showAlert = false) {
      try {
        const res = await apiFetch('/api/gemini_usage');
        const data = await res.json();
        updateAiQuotaUI(data.usage, data.models);
        if (showAlert) {
          const rem = data.usage ? data.usage.remaining_today : 1500;
          const used = data.usage ? data.usage.calls_today : 0;
          alert(`📊 تقرير رصيد الذكاء الاصطناعي اليومي:\n• النموذج الفعال: ${data.usage.model || 'gemini-3.8-flash'}\n• المتبقي اليوم: ${rem} من 1,500 طلب\n• المستهلك اليوم: ${used} طلب\n• حالة الفحص البصري (Vision): يعمل ومفعل بكفاءة عالية 🟢`);
        }
      } catch (e) {}
    }

    function updateAiQuotaUI(usage, models) {
      if (!usage) return;
      const rem = (usage.remaining_today !== undefined) ? usage.remaining_today : 1500;
      const used = (usage.calls_today !== undefined) ? usage.calls_today : 0;
      const isConn = usage.is_connected !== false;

      const counterEl = document.getElementById('aiCallsCounter');
      if (counterEl) {
        counterEl.innerText = `المتبقي: ${rem.toLocaleString()} / 1,500`;
      }
      const dotEl = document.getElementById('aiStatusDot');
      if (dotEl) {
        dotEl.style.background = isConn ? '#10b981' : '#f59e0b';
        dotEl.style.boxShadow = isConn ? '0 0 6px #10b981' : '0 0 6px #f59e0b';
      }

      const stRemEl = document.getElementById('stAiRemaining');
      if (stRemEl) {
        stRemEl.innerText = rem.toLocaleString();
      }

      const remBox = document.getElementById('aiRemainingBox');
      if (remBox) remBox.innerText = rem.toLocaleString();
      const usedBox = document.getElementById('aiUsedBox');
      if (usedBox) usedBox.innerText = used.toLocaleString();
      const badgeStatus = document.getElementById('aiModelBadgeStatus');
      if (badgeStatus) {
        badgeStatus.innerText = usage.status_label || (isConn ? 'متصل ونشط 🟢' : 'بانتظار المفتاح ⚠️');
        badgeStatus.className = isConn ? 'badge badge-success' : 'badge badge-warning';
      }
    }

    init();
  </script>
</body>
</html>

"""

# ==============================================================================
# خدمات الربط مع لوحة تحكم المنجر وتحديثات النظام
# ==============================================================================
def is_port_listening(port: int, host: str = "127.0.0.1", timeout: float = 0.15) -> bool:
    """فحص ما إذا كان البورت يعمل ومستمع للاتصالات."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False

def ensure_mysql_running() -> bool:
    """التأكد من تشغيل خادم MySQL (XAMPP) الضروري لعمل لوحة الإدارة وقاعدة البيانات."""
    if is_port_listening(3306):
        return True

    # 1. محاولة تشغيل خدمة ويندوز
    try:
        subprocess.run(["net", "start", "mysql"], capture_output=True, timeout=5)
    except Exception:
        pass

    if is_port_listening(3306):
        return True

    # 2. تشغيل mysqld.exe مباشرة من مسار XAMPP
    mysqld_exe = r"C:\xampp\mysql\bin\mysqld.exe"
    my_ini = r"C:\xampp\mysql\bin\my.ini"
    if os.path.exists(mysqld_exe):
        try:
            subprocess.Popen(
                [mysqld_exe, f"--defaults-file={my_ini}", "--standalone"],
                cwd=r"C:\xampp",
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
        except Exception as e:
            print(f"Error starting mysqld: {e}")

    for _ in range(8):
        time.sleep(0.4)
        if is_port_listening(3306):
            return True

    return is_port_listening(3306)

def find_php_executable() -> Optional[str]:
    """البحث عن مفسر PHP لتشغيل المنجر"""
    candidates = [
        os.path.join(BASE_DIR, "php", "php.exe"),
        os.path.join(BASE_DIR, "manager", "php", "php.exe"),
        "php",
        r"C:\xampp\php\php.exe",
        r"C:\php\php.exe",
        r"C:\Program Files\php\php.exe",
    ]
    for c in candidates:
        try:
            res = subprocess.run([c, "-v"], capture_output=True, timeout=2)
            if res.returncode == 0:
                return c
        except Exception:
            continue
    return None

def ensure_portable_php() -> Optional[str]:
    """تجهيز وتنزيل نسخة PHP 8.2 محمولة تلقائياً عند عدم توفر PHP على الجهاز"""
    php_dir = os.path.join(BASE_DIR, "php")
    php_exe = os.path.join(php_dir, "php.exe")
    if os.path.exists(php_exe):
        return php_exe

    try:
        import zipfile
        import urllib.request
        os.makedirs(php_dir, exist_ok=True)
        zip_path = os.path.join(php_dir, "php_portable.zip")
        
        url = "https://windows.php.net/downloads/releases/php-8.2.34-nts-Win32-vs16-x64.zip"
        print("  ⏳ جاري تنزيل بيئة PHP المحمولة للويندوز...")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=90) as resp, open(zip_path, 'wb') as f:
            shutil.copyfileobj(resp, f)

        print("  📦 جاري فك ضغط بيئة PHP...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(php_dir)
        try:
            os.remove(zip_path)
        except Exception:
            pass

        ini_dev = os.path.join(php_dir, "php.ini-development")
        ini_prod = os.path.join(php_dir, "php.ini")
        if os.path.exists(ini_dev) and not os.path.exists(ini_prod):
            with open(ini_dev, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            replacements = [
                (";extension_dir = \"ext\"", "extension_dir = \"ext\""),
                (";extension=curl", "extension=curl"),
                (";extension=fileinfo", "extension=fileinfo"),
                (";extension=mbstring", "extension=mbstring"),
                (";extension=openssl", "extension=openssl"),
                (";extension=pdo_mysql", "extension=pdo_mysql"),
            ]
            for old, new in replacements:
                content = content.replace(old, new)
            with open(ini_prod, "w", encoding="utf-8") as f:
                f.write(content)

        if os.path.exists(php_exe):
            print("  ✅ تم تجهيز بيئة PHP بنجاح!")
            return php_exe
    except Exception as e:
        print(f"❌ خطأ أثناء إعداد PHP المحمول: {e}")
    return None

def get_manager_directory() -> str:
    """تحديد مسار مجلد المنجر: الأولوية للمجلد المدمج داخل هذا المشروع"""
    integrated_manager = os.path.join(BASE_DIR, "manager")
    if os.path.exists(os.path.join(integrated_manager, "artisan")):
        return integrated_manager
    
    cfg = load_config()
    configured_dir = cfg.get("manager_servers_dir", r"C:\xampp\htdocs\projects\AZ")
    if os.path.exists(os.path.join(configured_dir, "manager", "artisan")):
        return os.path.join(configured_dir, "manager")
    if os.path.exists(os.path.join(configured_dir, "artisan")):
        return configured_dir
    return None

def get_manager_system_status(client_host: str = "localhost") -> dict:
    """التحقق من حالة سيرفر المنجر وبقية خدمات المنصة في الوقت الفعلي."""
    cfg = load_config()
    custom_manager_url = cfg.get("manager_url", "").strip()
    manager_dir = get_manager_directory()
    is_installed = manager_dir is not None

    is_local = client_host in ["localhost", "127.0.0.1", "::1"]
    lan_ip = get_lan_ip()
    display_host = "localhost" if is_local else (client_host if client_host else lan_ip)

    effective_manager_url = custom_manager_url or f"http://{display_host}:8002"

    manager_running = False
    if custom_manager_url and not any(h in custom_manager_url for h in ["localhost", "127.0.0.1"]):
        try:
            import urllib.request
            req = urllib.request.Request(custom_manager_url, headers={"User-Agent": "Lelbai/1.0"})
            with urllib.request.urlopen(req, timeout=1.2) as resp:
                if resp.status in (200, 301, 302, 401, 403):
                    manager_running = True
        except Exception:
            manager_running = False
    else:
        manager_running = is_port_listening(8002)

    backend_running = is_port_listening(8000)
    frontend_running = is_port_listening(3000)
    mysql_running = is_port_listening(3306)
    desktop_shortcut = os.path.join(os.path.expanduser("~"), "Desktop", "لوحة تحكم المنجر.lnk")

    return {
        "manager_running": manager_running,
        "backend_running": backend_running,
        "frontend_running": frontend_running,
        "mysql_running": mysql_running,
        "shortcut_exists": os.path.exists(desktop_shortcut),
        "is_installed": is_installed,
        "manager_url": effective_manager_url,
        "lan_url": f"http://{lan_ip}:8002"
    }

def launch_manager_and_all_servers(client_host: str = "localhost") -> dict:
    """تشغيل كافة سيرفرات المنجر وقاعدة البيانات والتحقق من جاهزيتها قبل فتح لوحة التحكم."""
    cfg = load_config()
    custom_manager_url = cfg.get("manager_url", "").strip()
    manager_dir = get_manager_directory()
    az_base = cfg.get("manager_servers_dir", r"C:\xampp\htdocs\projects\AZ")
    start_servers_bat = os.path.join(az_base, "start_servers.bat")

    is_local = client_host in ["localhost", "127.0.0.1", "::1"]
    lan_ip = get_lan_ip()
    display_host = "localhost" if is_local else (client_host if client_host else lan_ip)
    manager_url = custom_manager_url or f"http://{display_host}:8002"
    lan_url = f"http://{lan_ip}:8002"

    # 1. إذا كان رابط المنجر مخصصاً لـ IP خارجي
    if custom_manager_url and not any(h in custom_manager_url for h in ["localhost", "127.0.0.1"]):
        try:
            import urllib.request
            req = urllib.request.Request(custom_manager_url, headers={"User-Agent": "Lelbai/1.0"})
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                if resp.status in (200, 301, 302, 401, 403):
                    return {
                        "success": True,
                        "message": "تم الاتصال بسيرفر المنجر على الشبكة بنجاح! 🚀",
                        "url": custom_manager_url,
                        "lan_url": custom_manager_url,
                        "manager_running": True
                    }
        except Exception:
            pass
        return {
            "success": False,
            "not_installed": False,
            "message": f"تعذر الاتصال بسيرفر المنجر عبر الرابط ({custom_manager_url}).",
            "url": custom_manager_url,
            "lan_url": custom_manager_url,
            "manager_running": False
        }

    # 2. فحص ما إذا كان سيرفر المنجر يعمل مسبقاً محلياً
    if is_port_listening(8002):
        return {
            "success": True,
            "message": "سيرفر الإدارة يعمل بالفعل وهو جاهز للاستخدام! 🚀",
            "url": manager_url,
            "lan_url": lan_url,
            "manager_running": True
        }

    # 3. التحقق من وجود مجلد المنجر
    if not manager_dir:
        return {
            "success": False,
            "not_installed": True,
            "message": (
                "🔒 لم يتم العثور على مجلد المنجر (manager).\n\n"
                "يرجى التأكد من تنزيل مجلد manager المدمج داخل مستودع المنظومة."
            ),
            "url": manager_url,
            "lan_url": lan_url,
            "manager_running": False
        }

    # 4. إطلاق المنجر عبر PHP artisan مباشرة
    php_exe = find_php_executable()
    if not php_exe:
        print("[+] PHP غير متوفر محلياً، جاري تنزيل وتجهيز بيئة PHP المحمولة تلقائياً...")
        php_exe = ensure_portable_php()

    if not php_exe:
        return {
            "success": False,
            "not_installed": False,
            "php_missing": True,
            "message": (
                "⚠️ لم يتم العثور على مفسر PHP على هذا الجهاز.\n\n"
                "لتشغيل صفحة المنجر محلياً، يلزم وجود بيئة PHP.\n"
                "يرجى التأكد من توفر اتصال بالإنترنت ليتم تحميل النسخة المحمولة تلقائياً، أو تثبيت برنامج XAMPP."
            ),
            "url": manager_url,
            "lan_url": lan_url,
            "manager_running": False
        }

    custom_ini = os.path.join(os.path.dirname(php_exe), "php.ini")
    cmd = [php_exe]
    if os.path.exists(custom_ini):
        cmd.extend(["-c", custom_ini])
    cmd.extend(["artisan", "serve", "--host=0.0.0.0", "--port=8002", "--no-reload"])

    try:
        subprocess.Popen(
            cmd,
            cwd=manager_dir,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        )
    except Exception as e:
        print(f"Error launching php artisan serve: {e}")

    # أيضاً تشغيل start_servers.bat إن وجد في مسار XAMPP لتشغيل الخدمات التابعة
    if os.path.exists(start_servers_bat):
        try:
            subprocess.Popen(
                f'start "" "{start_servers_bat}"',
                cwd=az_base,
                shell=True
            )
        except Exception as e:
            pass

    # انتظار حتى 6 ثوانٍ لبدء المنفذ 8002
    manager_ready = False
    for _ in range(12):
        time.sleep(0.5)
        if is_port_listening(8002):
            manager_ready = True
            break

    if not manager_ready:
        return {
            "success": False,
            "not_installed": False,
            "message": "جاري تجهيز سيرفرات الإدارة في الخلفية، يرجى الانتظار بضع ثوانٍ ثم النقر مجدداً.",
            "url": manager_url,
            "lan_url": lan_url,
            "manager_running": False
        }

    return {
        "success": True,
        "message": "تم إطلاق سيرفرات الإدارة بنجاح وهي جاهزة الآن! 🚀",
        "url": manager_url,
        "lan_url": lan_url,
        "manager_running": True
    }

def get_system_update_info() -> dict:
    """جلب معلومات آخر تحديث للنظام وتاريخه من Git أو الملف المخزن."""
    last_update_file = os.path.join(BASE_DIR, "last_update.json")
    info = {
        "last_updated_at": "غير محدد",
        "relative_time": "",
        "commit_sha": "",
        "commit_message": "",
        "status": "up_to_date"
    }
    
    try:
        git_dir = os.path.join(BASE_DIR, ".git")
        if os.path.exists(git_dir):
            out = subprocess.check_output(
                ["git", "log", "-1", "--format=%ci|%cr|%h|%s"],
                cwd=BASE_DIR,
                stderr=subprocess.DEVNULL,
                universal_newlines=True
            ).strip()
            if out and "|" in out:
                parts = out.split("|", 3)
                info["last_updated_at"] = parts[0]
                info["relative_time"] = parts[1]
                info["commit_sha"] = parts[2]
                info["commit_message"] = parts[3] if len(parts) > 3 else ""
                return info
    except Exception:
        pass

    if os.path.exists(last_update_file):
        try:
            with open(last_update_file, "r", encoding="utf-8") as f:
                saved = json.load(f)
                info.update(saved)
                return info
        except Exception:
            pass

    return info

def check_and_apply_updates() -> dict:
    """التحقق من وجود تحديثات من GitHub وسحبها وتطبيقها تلقائياً مع حماية بيانات المستخدم."""
    git_dir = os.path.join(BASE_DIR, ".git")
    if os.path.exists(git_dir):
        try:
            lock_file = os.path.join(git_dir, "index.lock")
            if os.path.exists(lock_file):
                try:
                    os.remove(lock_file)
                except Exception:
                    pass

            user_files = ["config.json", "groups_data.json"]
            backup = {}
            for uf in user_files:
                uf_path = os.path.join(BASE_DIR, uf)
                if os.path.exists(uf_path):
                    try:
                        with open(uf_path, "rb") as f:
                            data = f.read()
                            if len(data.strip()) > 10:
                                backup[uf] = data
                    except Exception:
                        pass

            subprocess.run(["git", "fetch", "origin", "--prune"], cwd=BASE_DIR, capture_output=True, timeout=25)
            try:
                branches = subprocess.check_output(["git", "branch", "-r"], cwd=BASE_DIR, universal_newlines=True)
            except Exception:
                branches = ""
            target = "origin/main" if "origin/main" in branches else "origin/master"

            subprocess.run(["git", "checkout", "-f", "-B", "main", target], cwd=BASE_DIR, capture_output=True, timeout=20)
            subprocess.run(["git", "reset", "--hard", target], cwd=BASE_DIR, capture_output=True, timeout=20)
            subprocess.run(["git", "clean", "-fd", "-e", "imgs/", "-e", "*.json"], cwd=BASE_DIR, capture_output=True, timeout=15)

            for uf, data in backup.items():
                if data and len(data.strip()) > 10:
                    try:
                        with open(os.path.join(BASE_DIR, uf), "wb") as f:
                            f.write(data)
                    except Exception:
                        pass

            info = get_system_update_info()
            return {
                "success": True,
                "message": "تم تحديث كافة ملفات النظام من GitHub بنجاح 100%! 🚀",
                "info": info
            }
        except Exception as e:
            return {"success": False, "message": f"خطأ أثناء التحديث: {str(e)}"}
    else:
        return {"success": False, "message": "المجلد الحالي لا يحتوي على مستودع Git محلي."}

# ==============================================================================
# معالج الطلبات لـ API وسيرفر الويب
# ==============================================================================
CURRENTLY_PUBLISHING = set()
PUBLISH_LOCK = threading.Lock()

class ControlCenterHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def handle(self):
        try:
            super().handle()
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            pass
        except Exception:
            pass

    def handle_one_request(self):
        try:
            super().handle_one_request()
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            self.close_connection = True
        except Exception:
            self.close_connection = True

    def send_cors_headers(self):
        try:
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")
        except Exception:
            pass

    def do_OPTIONS(self):
        try:
            self.send_response(200)
            self.send_cors_headers()
            self.end_headers()
        except Exception:
            pass

    def send_json(self, data, status=200):
        try:
            payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(payload)
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            pass
        except Exception:
            pass

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/favicon.ico":
            self.send_response(204)
            self.send_cors_headers()
            self.end_headers()
            return

        if path in ["/", "/index.html"]:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_cors_headers()
            self.end_headers()
            dash_file = os.path.join(BASE_DIR, "control_dashboard.html")
            page_content = HTML_PAGE
            try:
                if os.path.exists(dash_file):
                    with open(dash_file, "r", encoding="utf-8") as f:
                        page_content = f.read()
            except Exception:
                page_content = HTML_PAGE
            self.wfile.write(page_content.encode("utf-8"))
            return

        elif path == "/api/groups":
            groups = read_json_file(GROUPS_DATA_FILE)
            enriched = enrich_groups_metadata(groups)
            self.send_json(enriched)
            return

        elif path == "/api/ads":
            raw_pending = read_json_file(PENDING_FILE)
            published = read_json_file(PUBLISHED_FILE)
            flagged = read_json_file(FLAGGED_FILE)

            # استبعاد أي إعلان تم نشره أو حذفه مسبقاً من قائمة المراجعة تلقائياً
            published_ids = {p.get("ad_url", "").strip() for p in published if p.get("ad_url")} | {p.get("clean_title", "").strip() for p in published if p.get("clean_title")}
            flagged_ids = {f.get("ad_url", "").strip() for f in flagged if f.get("ad_url")} | {f.get("clean_title", "").strip() for f in flagged if f.get("clean_title")}

            clean_pending = []
            for ad in raw_pending:
                u = ad.get("ad_url", "").strip()
                t = ad.get("clean_title", "").strip()
                if (u and u in published_ids) or (t and t in published_ids):
                    continue
                if (u and u in flagged_ids) or (t and t in flagged_ids):
                    continue
                clean_pending.append(ad)

            if len(clean_pending) != len(raw_pending):
                raw_pending = clean_pending
                write_json_file(PENDING_FILE, raw_pending)

            enriched_pending = []
            for ad in raw_pending:
                try:
                    enriched_pending.append(enrich_ad_status(ad))
                except Exception as ex:
                    print(f"[!] تحذير أثناء إثراء إعلان المراجعة: {ex}")
                    enriched_pending.append(ad)

            resp = {
                "pending": enriched_pending,
                "pending_count": len(enriched_pending),
                "published_count": len(published),
                "flagged_count": len(flagged)
            }
            self.send_json(resp)
            return

        elif path == "/api/published_ads":
            published = read_json_file(PUBLISHED_FILE)
            enriched_published = []
            for ad in published:
                try:
                    enriched_published.append(enrich_ad_status(ad))
                except Exception:
                    enriched_published.append(ad)
            self.send_json({
                "published": enriched_published,
                "count": len(enriched_published)
            })
            return

        elif path == "/api/categories":
            cats = read_json_file(CATEGORIES_DB_FILE)
            self.send_json(cats)
            return

        elif path == "/api/flagged_ads":
            flagged = read_json_file(FLAGGED_FILE)
            self.send_json({
                "flagged": flagged,
                "count": len(flagged)
            })
            return

        elif path == "/api/status":
            with task_manager.lock:
                is_running = task_manager.is_running
                start_time = task_manager.start_time
                total_groups = task_manager.total_groups_count
                completed_groups = task_manager.completed_groups_count
                total_ads = task_manager.total_ads_collected
                active_tabs = dict(task_manager.active_tabs)
                logs_snapshot = list(task_manager.logs[-25:])

            elapsed = int(time.time() - start_time) if is_running else 0
            h, m, s = elapsed // 3600, (elapsed % 3600) // 60, elapsed % 60
            time_str = f"{h:02d}:{m:02d}:{s:02d}"

            raw_pending = read_json_file(PENDING_FILE)
            published = read_json_file(PUBLISHED_FILE)
            flagged = read_json_file(FLAGGED_FILE)

            published_ids = {p.get("ad_url", "").strip() for p in published if p.get("ad_url")} | {p.get("clean_title", "").strip() for p in published if p.get("clean_title")}
            flagged_ids = {f.get("ad_url", "").strip() for f in flagged if f.get("ad_url")} | {f.get("clean_title", "").strip() for f in flagged if f.get("clean_title")}

            clean_pending = [p for p in raw_pending if not ((p.get("ad_url", "").strip() and p.get("ad_url", "").strip() in published_ids) or (p.get("clean_title", "").strip() and p.get("clean_title", "").strip() in published_ids) or (p.get("ad_url", "").strip() and p.get("ad_url", "").strip() in flagged_ids) or (p.get("clean_title", "").strip() and p.get("clean_title", "").strip() in flagged_ids))]

            ready_count = sum(1 for p in clean_pending if (p.get("ai_evaluated") and p.get("is_safe", True)))

            resp = {
                "is_running": is_running,
                "elapsed_time": time_str,
                "total_groups": total_groups,
                "completed_groups": completed_groups,
                "total_ads": total_ads,
                "active_tabs": active_tabs,
                "logs": logs_snapshot,
                "pending_count": len(clean_pending),
                "ready_count": ready_count,
                "published_count": len(published),
                "flagged_count": len(flagged),
                "gemini_usage": get_gemini_usage_info(load_config().get("gemini_api_key", ""))
            }
            self.send_json(resp)
            return

        elif path == "/api/gemini_usage":
            cfg = load_config()
            usage = get_gemini_usage_info(cfg.get("gemini_api_key", ""))
            models_info = [
                {
                    "name": "gemini-3-flash-preview (النموذج الافتراضي المعتمد)",
                    "model_id": "gemini-3-flash-preview",
                    "supports_vision": True,
                    "vision_desc": "فحص الصور والنصوص بالرؤية السحابية الفائقة (Gemini Vision API)",
                    "daily_limit": 1500,
                    "rpm_limit": 15,
                    "is_active": True,
                    "status_label": "نشط ومعتمد تلقائياً 🟢"
                },
                {
                    "name": "gemini-3.5-flash",
                    "model_id": "gemini-3.5-flash",
                    "supports_vision": True,
                    "vision_desc": "طراز سحابي فائق السرعة لفحص الصور والنصوص",
                    "daily_limit": 1500,
                    "rpm_limit": 15,
                    "is_active": False,
                    "status_label": "مدعوم واحتياطي تلقائي ✅"
                },
                {
                    "name": "gemini-3.6-flash",
                    "model_id": "gemini-3.6-flash",
                    "supports_vision": True,
                    "vision_desc": "طراز متقدم لفحص الصور والنصوص وهيكلة البيانات",
                    "daily_limit": 1500,
                    "rpm_limit": 15,
                    "is_active": False,
                    "status_label": "مدعوم واحتياطي ✅"
                }
            ]
            self.send_json({
                "usage": usage,
                "models": models_info
            })
            return

        elif path == "/api/config":
            cfg = load_config()
            self.send_json(cfg)
            return

        elif path.startswith("/imgs/"):
            img_name = os.path.basename(path)
            candidate_paths = [
                os.path.join(IMGS_DIR, img_name),
                os.path.join(BASE_DIR, "imgs", img_name),
                os.path.join(BASE_DIR, "assets", "imgs", img_name),
                os.path.expanduser(os.path.join("~/Desktop/1/imgs", img_name)),
                os.path.expanduser(os.path.join("~/Desktop/تنزيل الاعلانات/asstes/imgs", img_name))
            ]
            img_path = next((p for p in candidate_paths if os.path.exists(p)), None)
            if img_path:
                ext = img_name.split(".")[-1].lower()
                mime = "image/webp" if ext == "webp" else ("image/jpeg" if ext in ["jpg", "jpeg"] else "image/png")
                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_cors_headers()
                self.send_header("Cache-Control", "public, max-age=86400")
                self.end_headers()
                with open(img_path, "rb") as f:
                    self.wfile.write(f.read())
                return
            self.send_response(404)
            self.send_cors_headers()
            self.end_headers()
        elif path == "/api/manager_status":
            client_host = self.headers.get("Host", "").split(":")[0].strip() or "localhost"
            self.send_json(get_manager_system_status(client_host))
            return

        elif path == "/api/update_info":
            self.send_json(get_system_update_info())
            return

        elif path == "/api/check_update":
            self.send_json(check_and_apply_updates())
            return

        self.send_response(404)
        self.send_cors_headers()
        self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        
        try:
            req_data = json.loads(body)
        except Exception:
            req_data = {}

        if path == "/api/add_group":
            raw_url = req_data.get("url", "").strip()
            if not raw_url:
                self.send_json({"success": False, "message": "يرجى إدخال رابط المجموعة أو الصفحة!"})
                return

            norm_input = normalize_group_url(raw_url)
            groups = read_json_file(GROUPS_DATA_FILE)

            # فحص صارم لمنع تكرار إضافة نفس الصفحة أو المجموعة مرتين
            for g in groups:
                if normalize_group_url(g.get("url", "")) == norm_input:
                    existing_name = g.get("name", "المجموعة")
                    self.send_json({
                        "success": False,
                        "message": f"❌ لا يمكن إضافة نفس الصفحة مرتين! هذا الرابط مضاف مسبقاً باسم: ({existing_name})."
                    })
                    return

            new_id = (max([g.get("id", 0) for g in groups]) + 1) if groups else 1
            now_str = time.strftime("%Y-%m-%d %H:%M:%S")
            new_entry = {
                "id": new_id,
                "name": req_data.get("name", f"مجموعة {new_id}").strip(),
                "url": raw_url,
                "category": req_data.get("category", "عام"),
                "created_at": now_str,
                "last_scraped_at": "لم يُسحب بعد",
                "last_ads_count": 0,
                "total_ads_count": 0,
                "status": "جاهز"
            }
            groups.append(new_entry)
            write_json_file(GROUPS_DATA_FILE, groups)
            self.send_json({"success": True, "message": "تمت إضافة الرابط بنجاح! ✅", "group": new_entry})
            return

        elif path == "/api/delete_group":
            gid = req_data.get("id")
            groups = read_json_file(GROUPS_DATA_FILE)
            groups = [g for g in groups if g.get("id") != gid]
            write_json_file(GROUPS_DATA_FILE, groups)
            self.send_json({"success": True})
            return

        elif path == "/api/start":
            start_mode = req_data.get("start_mode", "smart")
            start_url = req_data.get("start_url")
            incoming_groups = req_data.get("groups", [])
            
            # ترتيب المجموعات بناءً على نقطة الانطلاق المطلوبة
            if not incoming_groups or "start_mode" in req_data:
                ordered_objs = get_ordered_groups(start_mode, None, start_url)
                if ordered_objs:
                    req_data["groups"] = [g.get("url") for g in ordered_objs if g.get("url")]

            ok, msg = task_manager.start_scraping_job(req_data)
            self.send_json({"success": ok, "message": msg})
            return

        elif path == "/api/stop":
            ok, msg = task_manager.stop_scraping_job()
            self.send_json({"success": ok, "message": msg})
            return

        elif path == "/api/login":
            if task_manager.is_running:
                self.send_json({"success": False, "message": "⚠️ يرجى إيقاف عملية السحب أولاً بالضغط على 'إيقاف السحب' قبل فتح نافذة تسجيل الدخول!"})
                return
            user_data_dir = os.path.join(BASE_DIR, "browser_session")
            clean_browser_session_locks(user_data_dir)
            login_bat = os.path.join(BASE_DIR, "login.bat")
            login_script = os.path.join(BASE_DIR, "login.py")
            try:
                if sys.platform == "win32" and os.path.exists(login_bat):
                    os.startfile(login_bat)
                else:
                    flags = getattr(subprocess, 'CREATE_NEW_CONSOLE', 0)
                    subprocess.Popen([sys.executable, login_script], cwd=BASE_DIR, creationflags=flags)
            except Exception:
                flags = getattr(subprocess, 'CREATE_NEW_CONSOLE', 0)
                subprocess.Popen([sys.executable, login_script], cwd=BASE_DIR, creationflags=flags)
            self.send_json({"success": True, "message": "تم إطلاق نافذة المتصفح بنجاح! 🟢"})
            return

        elif path == "/api/approve":
            ad = req_data.get("ad", {})
            ad_url = ad.get("ad_url")
            ad_title = ad.get("clean_title")
            ad_identifier = ad_url or ad_title or f"{ad.get('phone_number')}_{ad.get('description', '')[:30]}"

            with PUBLISH_LOCK:
                if ad_identifier in CURRENTLY_PUBLISHING:
                    self.send_json({"success": False, "message": "⏳ جاري نشر هذا الإعلان حالياً بالفعل، يرجى الانتظار بضع ثوانٍ!"})
                    return

                # التحقق الصارم من عدم وجود الإعلان مسبقاً في سجل الإعلانات المنشورة
                published = read_json_file(PUBLISHED_FILE)
                if any((p.get("ad_url") and p.get("ad_url") == ad_url) or 
                       (p.get("clean_title") and p.get("clean_title") == ad_title) for p in published):
                    # إزالة الإعلان من المسودة لأنه منشور بالفعل
                    pending = read_json_file(PENDING_FILE)
                    pending = [p for p in pending if not ((ad_url and p.get("ad_url") == ad_url) or (ad_title and p.get("clean_title") == ad_title))]
                    write_json_file(PENDING_FILE, pending)
                    self.send_json({"success": True, "message": "⚠️ هذا الإعلان تم نشره بالفعل مسبقاً! تم نقله لقسم المنشورات."})
                    return

                CURRENTLY_PUBLISHING.add(ad_identifier)

            try:
                ok, msg = publish_ad_to_website(ad)
                if ok:
                    pending = read_json_file(PENDING_FILE)
                    pending = [p for p in pending if not ((ad_url and p.get("ad_url") == ad_url) or (not ad_url and p.get("clean_title") == ad_title))]
                    write_json_file(PENDING_FILE, pending)
            finally:
                with PUBLISH_LOCK:
                    CURRENTLY_PUBLISHING.discard(ad_identifier)

            self.send_json({"success": ok, "message": msg, "api_ok": ok})
            return

        elif path == "/api/save_ad":
            ad = req_data.get("ad", {})
            ad_idx = req_data.get("index")
            ad_url = (ad.get("ad_url") or "").strip()
            ad_title = (ad.get("clean_title") or "").strip()

            pending = read_json_file(PENDING_FILE)
            found_idx = -1
            if ad_url:
                for i, p in enumerate(pending):
                    if p.get("ad_url", "").strip() == ad_url:
                        found_idx = i
                        break
            if found_idx == -1 and ad_title:
                for i, p in enumerate(pending):
                    if p.get("clean_title", "").strip() == ad_title:
                        found_idx = i
                        break
            if found_idx == -1 and ad_idx is not None and isinstance(ad_idx, int) and 0 <= ad_idx < len(pending):
                found_idx = ad_idx

            if found_idx != -1 and found_idx < len(pending):
                existing = pending[found_idx]
                existing.update(ad)
                pending[found_idx] = existing
                write_json_file(PENDING_FILE, pending)
                self.send_json({"success": True, "message": "تم حفظ وتحديث بيانات الإعلان بنجاح في سجل المراجعة!", "ad": existing})
            else:
                self.send_json({"success": False, "message": "لم يتم العثور على الإعلان المطلوب تحديثه في قائمة المراجعة"})
            return

        elif path == "/api/reject":
            ad = req_data.get("ad", {})
            ad_url = ad.get("ad_url")
            ad_title = ad.get("clean_title")
            pending = read_json_file(PENDING_FILE)
            pending = [p for p in pending if not ((ad_url and p.get("ad_url") == ad_url) or (not ad_url and p.get("clean_title") == ad_title))]
            write_json_file(PENDING_FILE, pending)

            flagged = read_json_file(FLAGGED_FILE)
            flagged.append(ad)
            write_json_file(FLAGGED_FILE, flagged)
            self.send_json({"success": True, "message": "تم استبعاد الإعلان بنجاح"})
            return

        elif path == "/api/delete_ad_image":
            image_name = req_data.get("image_name", "").strip()
            ad_url = req_data.get("ad_url", "").strip()
            ad_title = req_data.get("clean_title", "").strip()
            ad_idx = req_data.get("ad_index")

            if not image_name:
                self.send_json({"success": False, "message": "لم يتم تحديد اسم الصورة المراد حذفها!"})
                return

            pending = read_json_file(PENDING_FILE)
            target_ad = None
            found_idx = -1

            # محاولة العثور على الإعلان بالرابط أو العنوان أو اسم الصورة أو الفهرس
            for i, p in enumerate(pending):
                if (ad_url and p.get("ad_url") == ad_url) or \
                   (ad_title and p.get("clean_title") == ad_title) or \
                   (image_name in p.get("nimages", [])):
                    target_ad = p
                    found_idx = i
                    break

            if target_ad is None and ad_idx is not None and isinstance(ad_idx, int) and 0 <= ad_idx < len(pending):
                target_ad = pending[ad_idx]
                found_idx = ad_idx

            if target_ad is None:
                self.send_json({"success": False, "message": "لم يتم العثور على الإعلان المستهدف في قائمة المراجعة!"})
                return

            # إزالة الصورة من الإعلان
            nimages = target_ad.get("nimages", [])
            download_urls = target_ad.get("images dowlod", [])
            
            new_nimages = []
            new_urls = []
            for idx_img, fname in enumerate(nimages):
                if fname != image_name:
                    new_nimages.append(fname)
                    if idx_img < len(download_urls):
                        new_urls.append(download_urls[idx_img])

            target_ad["nimages"] = new_nimages
            target_ad["images dowlod"] = new_urls

            # حذف الملف فعلياً من القرص لحماية المساحة
            file_path = os.path.join(IMGS_DIR, image_name)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass

            # إعادة تقييم وإثراء حالة الإعلان
            enriched = enrich_ad_status(target_ad)
            pending[found_idx] = enriched
            write_json_file(PENDING_FILE, pending)

            self.send_json({
                "success": True,
                "message": "تم حذف الصورة نهائياً وتحديث الإعلان بنجاح! 🗑️",
                "remaining_images": new_nimages,
                "ad": enriched
            })
            return

        elif path == "/api/bulk_approve":
            pending = read_json_file(PENDING_FILE)
            published_count = 0
            api_count = 0
            cfg = load_config()
            has_api = bool(cfg.get("website_api_url", "").strip())
            remaining = []
            
            for ad in pending:
                ev = enrich_ad_status(ad).get("evaluation", {})
                if ev.get("is_ready_to_publish", True):
                    ok, _ = publish_ad_to_website(ad)
                    published_count += 1
                    if ok:
                        if has_api:
                            api_count += 1
                    else:
                        remaining.append(ad)
                else:
                    remaining.append(ad)
            
            write_json_file(PENDING_FILE, remaining)

            if has_api:
                msg = f"تم نشر {api_count} إعلان بنجاح على سيرفر الموقع! 🚀 وتجهيز {published_count} في مجلد الاستيراد."
            else:
                msg = f"تم تجهيز وتصدير {published_count} إعلان بنجاح إلى مجلد إعلانات_للاستيراد على سطح المكتب! 📁\n(⚠️ ملاحظة: لم يتم الرفع المباشر عبر الإنترنت لأن رابط الـ API غير محدد في الإعدادات)"

            self.send_json({"success": True, "message": msg})
            return

        elif path == "/api/config":
            cfg = load_config()
            cfg["gemini_api_key"] = req_data.get("gemini_api_key", cfg.get("gemini_api_key"))
            cfg["website_api_url"] = req_data.get("website_api_url", cfg.get("website_api_url"))
            cfg["website_api_key"] = req_data.get("website_api_key", cfg.get("website_api_key"))
            if "manager_url" in req_data:
                cfg["manager_url"] = str(req_data.get("manager_url", "")).strip()
            save_config(cfg)
            task_manager.gemini_processor = GeminiProcessor()
            self.send_json({"success": True})
            return

        elif path == "/api/open_folder":
            import_base = os.path.join(os.path.expanduser("~"), "Desktop", "إعلانات_للاستيراد")
            if not os.path.exists(import_base):
                os.makedirs(import_base, exist_ok=True)
            try:
                os.startfile(import_base)
                self.send_json({"success": True, "message": "تم فتح مجلد الاستيراد بنجاح"})
            except Exception as e:
                self.send_json({"success": False, "message": str(e)})
            return

        elif path == "/api/revert_ad":
            ad = req_data.get("ad", {})
            ad_url = ad.get("ad_url") or ad.get("clean_title")
            published = read_json_file(PUBLISHED_FILE)
            published = [p for p in published if (p.get("ad_url") or p.get("clean_title")) != ad_url]
            write_json_file(PUBLISHED_FILE, published)

            pending = read_json_file(PENDING_FILE)
            if not any((p.get("ad_url") or p.get("clean_title")) == ad_url for p in pending):
                ad_pending = ad.copy()
                ad_pending.pop("publish_status", None)
                ad_pending.pop("published_at", None)
                pending.insert(0, ad_pending)
                write_json_file(PENDING_FILE, pending)
            self.send_json({"success": True, "message": "تم إعادة الإعلان إلى قائمة المراجعة"})
            return

        elif path in ["/api/delete_published", "/api/delete_published_ad"]:
            ad = req_data.get("ad", {})
            ad_url = ad.get("ad_url") or req_data.get("ad_url") or ad.get("clean_title") or req_data.get("clean_title")
            published = read_json_file(PUBLISHED_FILE)
            published = [p for p in published if (p.get("ad_url") or p.get("clean_title")) != ad_url]
            write_json_file(PUBLISHED_FILE, published)
            self.send_json({"success": True, "message": "تم حذف الإعلان من سجل المنشورات بنجاح! 🗑️"})
            return

        elif path == "/api/delete_ad":
            # حذف إعلان محدد ومسح صوره من الجهاز
            ad = req_data.get("ad", {})
            ad_url = ad.get("ad_url") or req_data.get("ad_url")
            clean_title = ad.get("clean_title") or req_data.get("clean_title")
            ad_idx = req_data.get("ad_index")

            pending = read_json_file(PENDING_FILE)
            target = None
            found_idx = -1

            for i, p in enumerate(pending):
                if (ad_url and p.get("ad_url") == ad_url) or (clean_title and p.get("clean_title") == clean_title):
                    target = p
                    found_idx = i
                    break
            if target is None and ad_idx is not None and isinstance(ad_idx, int) and 0 <= ad_idx < len(pending):
                target = pending[ad_idx]
                found_idx = ad_idx

            if target:
                for img_name in target.get("nimages", []):
                    img_path = os.path.join(IMGS_DIR, img_name)
                    if os.path.exists(img_path):
                        try:
                            os.remove(img_path)
                        except Exception:
                            pass
                pending.pop(found_idx)
                write_json_file(PENDING_FILE, pending)
                self.send_json({"success": True, "message": "تم حذف الإعلان ومسح صوره نهائياً بنجاح! 🗑️"})
            else:
                self.send_json({"success": False, "message": "لم يتم العثور على الإعلان المستهدف."})
            return

        elif path == "/api/clear_pending_ads":
            # تفريغ كافة الإعلانات غير المنشورة ومسح صورها
            pending = read_json_file(PENDING_FILE)
            for p in pending:
                for img_name in p.get("nimages", []):
                    img_path = os.path.join(IMGS_DIR, img_name)
                    if os.path.exists(img_path):
                        try:
                            os.remove(img_path)
                        except Exception:
                            pass
            write_json_file(PENDING_FILE, [])
            self.send_json({"success": True, "message": "تم مسح وتفريغ كافة الإعلانات ومسح صورها بنجاح! 🗑️"})
            return

        elif path == "/api/clear_groups":
            write_json_file(GROUPS_DATA_FILE, [])
            self.send_json({"success": True, "message": "تم تفريغ كافة روابط المجموعات بنجاح! 🗑️"})
            return

        elif path == "/api/load_starter_groups":
            write_json_file(GROUPS_DATA_FILE, DEFAULT_STARTER_GROUPS)
            self.send_json({"success": True, "message": f"تم استيراد {len(DEFAULT_STARTER_GROUPS)} روابط مقترحة بنجاح! 📥"})
            return

        elif path == "/api/clear_published_ads":
            write_json_file(PUBLISHED_FILE, [])
            self.send_json({"success": True, "message": "تم تفريغ سجل الإعلانات المنشورة بنجاح! 🗑️"})
            return

        elif path == "/api/clear_flagged_ads":
            write_json_file(FLAGGED_FILE, [])
            self.send_json({"success": True, "message": "تم تفريغ سجل الإعلانات المستبعدة بنجاح! 🗑️"})
            return

        elif path == "/api/unflag_ad":
            ad = req_data.get("ad", {})
            ad_url = ad.get("ad_url") or req_data.get("ad_url")
            clean_title = ad.get("clean_title") or req_data.get("clean_title")
            ad_idx = req_data.get("ad_index")

            flagged = read_json_file(FLAGGED_FILE)
            target = None
            found_idx = -1
            for i, f in enumerate(flagged):
                if (ad_url and f.get("ad_url") == ad_url) or (clean_title and f.get("clean_title") == clean_title):
                    target = f
                    found_idx = i
                    break
            if target is None and ad_idx is not None and isinstance(ad_idx, int) and 0 <= ad_idx < len(flagged):
                target = flagged[ad_idx]
                found_idx = ad_idx
            if target is None:
                target = ad

            if target:
                if found_idx != -1 and found_idx < len(flagged):
                    flagged.pop(found_idx)
                    write_json_file(FLAGGED_FILE, flagged)
                
                target["is_safe"] = True
                target["moderation_status"] = "safe"
                target["rejection_reason"] = None
                pending = read_json_file(PENDING_FILE)
                target_url = target.get("ad_url")
                target_title = target.get("clean_title")
                if not any((target_url and p.get("ad_url") == target_url) or (target_title and p.get("clean_title") == target_title) for p in pending):
                    pending.insert(0, target)
                    write_json_file(PENDING_FILE, pending)
                
                self.send_json({"success": True, "message": "تم إلغاء الحظر ونقل الإعلان إلى قائمة المراجعة بنجاح! 🟢"})
            else:
                self.send_json({"success": False, "message": "لم يتم العثور على الإعلان المستهدف."})
            return

        elif path == "/api/delete_flagged_ad":
            ad = req_data.get("ad", {})
            ad_url = ad.get("ad_url") or req_data.get("ad_url")
            clean_title = ad.get("clean_title") or req_data.get("clean_title")
            ad_idx = req_data.get("ad_index")

            flagged = read_json_file(FLAGGED_FILE)
            target = None
            found_idx = -1
            for i, f in enumerate(flagged):
                if (ad_url and f.get("ad_url") == ad_url) or (clean_title and f.get("clean_title") == clean_title):
                    target = f
                    found_idx = i
                    break
            if target is None and ad_idx is not None and isinstance(ad_idx, int) and 0 <= ad_idx < len(flagged):
                target = flagged[ad_idx]
                found_idx = ad_idx

            if target:
                for img_name in target.get("nimages", []):
                    img_path = os.path.join(IMGS_DIR, img_name)
                    if os.path.exists(img_path):
                        try: os.remove(img_path)
                        except Exception: pass
                flagged.pop(found_idx)
                write_json_file(FLAGGED_FILE, flagged)
                self.send_json({"success": True, "message": "تم حذف الإعلان المخالف وصوره نهائياً بنجاح! 🗑️"})
            else:
                self.send_json({"success": False, "message": "لم يتم العثور على الإعلان المطلوب."})
            return

        elif path == "/api/clear_all_images":
            deleted_count = 0
            if os.path.exists(IMGS_DIR):
                for f in os.listdir(IMGS_DIR):
                    fp = os.path.join(IMGS_DIR, f)
                    if os.path.isfile(fp) and not f.startswith("."):
                        try:
                            os.remove(fp)
                            deleted_count += 1
                        except Exception:
                            pass
            self.send_json({"success": True, "message": f"تم مسح {deleted_count} صورة من القرص بنجاح! 🗑️"})
            return

        elif path == "/api/reset_all_data":
            write_json_file(PENDING_FILE, [])
            write_json_file(PUBLISHED_FILE, [])
            write_json_file(FLAGGED_FILE, [])
            write_json_file(ALL_ADS_FILE, [])
            if os.path.exists(IMGS_DIR):
                for f in os.listdir(IMGS_DIR):
                    fp = os.path.join(IMGS_DIR, f)
                    if os.path.isfile(fp) and not f.startswith("."):
                        try:
                            os.remove(fp)
                        except Exception:
                            pass
            self.send_json({"success": True, "message": "تم تصفير كافة بيانات المنظومة بنجاح (إعادة ضبط المصنع)! 🔄"})
            return

        elif path == "/api/reclassify_ad_with_ai":
            ad = req_data.get("ad", {})
            ad_url = ad.get("ad_url") or req_data.get("ad_url")
            clean_title = ad.get("clean_title") or req_data.get("clean_title")
            ad_idx = req_data.get("ad_index")
            from_flagged = req_data.get("from_flagged", False)

            pending = read_json_file(PENDING_FILE)
            flagged = read_json_file(FLAGGED_FILE)
            target = None
            found_pending_idx = -1
            found_flagged_idx = -1

            if from_flagged:
                for i, f in enumerate(flagged):
                    if (ad_url and f.get("ad_url") == ad_url) or (clean_title and f.get("clean_title") == clean_title):
                        target = f
                        found_flagged_idx = i
                        break
                if target is None and ad_idx is not None and isinstance(ad_idx, int) and 0 <= ad_idx < len(flagged):
                    target = flagged[ad_idx]
                    found_flagged_idx = ad_idx
            else:
                for i, p in enumerate(pending):
                    if (ad_url and p.get("ad_url") == ad_url) or (clean_title and p.get("clean_title") == clean_title):
                        target = p
                        found_pending_idx = i
                        break
                if target is None and ad_idx is not None and isinstance(ad_idx, int) and 0 <= ad_idx < len(pending):
                    target = pending[ad_idx]
                    found_pending_idx = ad_idx

            if target is None:
                target = ad

            if not target:
                self.send_json({"success": False, "message": "لم يتم العثور على الإعلان المطلوب"})
                return

            try:
                processed = task_manager.gemini_processor.process_and_clean_ad(target, IMGS_DIR)
                if from_flagged or found_flagged_idx != -1:
                    if processed.get("is_safe", True):
                        if found_flagged_idx != -1 and found_flagged_idx < len(flagged):
                            flagged.pop(found_flagged_idx)
                            write_json_file(FLAGGED_FILE, flagged)
                        enriched = enrich_ad_status(processed, force_recalc=True)
                        pending.insert(0, enriched)
                        write_json_file(PENDING_FILE, pending)
                    else:
                        enriched = processed
                        if found_flagged_idx != -1 and found_flagged_idx < len(flagged):
                            flagged[found_flagged_idx] = enriched
                            write_json_file(FLAGGED_FILE, flagged)
                else:
                    if not processed.get("is_safe", True):
                        if found_pending_idx != -1 and found_pending_idx < len(pending):
                            pending.pop(found_pending_idx)
                            write_json_file(PENDING_FILE, pending)
                        flagged.insert(0, processed)
                        write_json_file(FLAGGED_FILE, flagged)
                        enriched = processed
                    else:
                        enriched = enrich_ad_status(processed, force_recalc=True)
                        if found_pending_idx != -1 and found_pending_idx < len(pending):
                            pending[found_pending_idx] = enriched
                            write_json_file(PENDING_FILE, pending)

                all_ads = read_json_file(ALL_ADS_FILE)
                for j, a in enumerate(all_ads):
                    if (ad_url and a.get("ad_url") == ad_url) or (clean_title and a.get("clean_title") == clean_title):
                        all_ads[j] = enriched
                        write_json_file(ALL_ADS_FILE, all_ads)
                        break

                self.send_json({
                    "success": True,
                    "message": f"تم فحص وتصنيف الإعلان بالذكاء الاصطناعي: {enriched.get('leaf_category_name', '')} [ID: {enriched.get('id-categorie', '')}] 🤖",
                    "ad": enriched
                })
            except Exception as e:
                self.send_json({"success": False, "message": f"خطأ أثناء التصنيف بالذكاء الاصطناعي: {e}"})
            return

        elif path == "/api/reclassify_all_with_ai":
            pending = read_json_file(PENDING_FILE)
            updated = []
            for p in pending:
                try:
                    proc = task_manager.gemini_processor.process_and_clean_ad(p, IMGS_DIR)
                    enr = enrich_ad_status(proc, force_recalc=True)
                    updated.append(enr)
                except Exception:
                    updated.append(enrich_ad_status(p, force_recalc=True))
            write_json_file(PENDING_FILE, updated)
            self.send_json({
                "success": True,
                "message": f"تمت إعادة تصنيف وهيكلة كافة الإعلانات ({len(updated)}) بالذكاء الاصطناعي بنجاح! 🤖",
                "count": len(updated)
            })
            return

        elif path == "/api/launch_manager":
            client_host = self.headers.get("Host", "").split(":")[0].strip() or "localhost"
            self.send_json(launch_manager_and_all_servers(client_host))
            return

        elif path == "/api/check_update":
            self.send_json(check_and_apply_updates())
            return

        self.send_response(404)
        self.send_cors_headers()
        self.end_headers()

class ThreadedHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True

    def handle_error(self, request, client_address):
        exc_type, _, _ = sys.exc_info()
        if exc_type in (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            return  # تجاهل هادئ لانقطاع الاتصال من المتصفح دون طباعة أخطاء
        super().handle_error(request, client_address)

def run_app():
    try:
        dash_path = os.path.join(BASE_DIR, "control_dashboard.html")
        with open(dash_path, "w", encoding="utf-8") as f:
            f.write(HTML_PAGE)
    except Exception:
        pass

    port = 5000
    server_address = ('', port)
    httpd = ThreadedHTTPServer(server_address, ControlCenterHandler)
    
    url = f"http://localhost:{port}"
    print(f"\n" + "="*65)
    print(f"🚀 تم تشغيل سيرفر لوحة التحكم المركزية بنجاح!")
    print(f"👉 جاري فتح صفحة التحكم في المتصفح: {url}")
    print(f"="*65 + "\n")

    threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[+] تم إيقاف السيرفر.")

if __name__ == "__main__":
    run_app()
