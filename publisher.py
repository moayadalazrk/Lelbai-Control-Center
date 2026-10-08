# -*- coding: utf-8 -*-
"""
محرك النشر والتصدير لمنصة (للبيع - Lelbai)
يقوم بتوليد مجلد الإعلان وملف info.txt وصوره داخل مجلد إعلانات_للاستيراد لرفعها للموقع فوراً.
"""

import os
import sys
import json
import time
import shutil
import re
import requests
import random
import secrets
from typing import Dict, Any, Tuple, List

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from config import load_config

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLISHED_FILE = os.path.join(BASE_DIR, "published_ads.json")
IMGS_DIR = os.path.join(BASE_DIR, "asstes", "imgs")

# مسار مجلد الاستيراد للموقع (ديناميكي لسطح مكتب أي مستخدم)
DESKTOP_IMPORT_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "إعلانات_للاستيراد")

# خريطة معرفات الأقسام لتوليد القسم_id بدقة
CATEGORY_ID_MAP = {
    "هيونداي": 1144, "كيا": 1155, "تويوتا": 1166, "مازدا": 1176, "نيسان": 1184,
    "سايبا": 1193, "سيامكو": 1199, "شام": 1199, "دايو": 1205, "سوزوكي": 1212,
    "ميتسوبيشي": 1219, "مرسيدس": 1226, "بي إم دبليو": 1235, "بيجو": 1242,
    "فولكس": 1251, "رينو": 1259, "جيلي": 1274, "شيري": 1282, "شانجان": 1288,
    "شيفروليه": 1295, "أوبل": 1303, "فورد": 1310, "هوندا": 1318, "أودي": 1336,
    "سكودا": 1343, "فيات": 1349, "لاند روفر": 1356, "سيارات": 1143,
    "دراجات": 3091, "ميتورات": 3091, "بسكليتات": 3117,
    "شقق": 3131, "فلل": 3132, "بيوت": 3132, "أراضي": 3133, "مزارع": 3133, "محلات": 3134, "عقارات": 29,
    "طاقة شمسية": 3136, "إنفيرترات": 3137, "بطاريات": 3137, "طاقة": 44,
    "جوالات": 3139, "هواتف": 3139, "آيباد": 3140, "كمبيوتر": 3141, "لابتوب": 3141, "شاشات": 3143, "إلكترونيات": 69,
    "أثاث": 3148, "غرف": 3148, "أجهزة كهربائية": 3149, "مفروشات": 3151, "منزل": 88,
    "وظائف": 3154, "خدمات": 202, "مواشي": 140, "أخرى": 259
}

from category_classifier import (
    classify_leaf_category,
    extract_detailed_specifications,
    extract_or_generate_account_name
)

def detect_category_id(ad: Dict[str, Any]) -> Tuple[int, str]:
    """تحديد القسم_id في أصغر فئة فرعية وفق شجرة أقسام الموقع (Leaf Category) مع ضمان عدم الوقوف عند أي قسم أب"""
    from ai_ad_enhancer import ensure_leaf_category_id, get_category_name_by_id
    if ad.get("leaf_category_id"):
        leaf_id = ensure_leaf_category_id(ad["leaf_category_id"])
        leaf_name = ad.get("leaf_category_name") if leaf_id == ad["leaf_category_id"] else get_category_name_by_id(leaf_id)
        return leaf_id, leaf_name
    
    desc = ad.get("clean_description") or ad.get("description", "")
    title = ad.get("clean_title", "")
    leaf = classify_leaf_category(f"{title} {desc}")
    leaf_id = ensure_leaf_category_id(leaf["category_id"])
    return leaf_id, get_category_name_by_id(leaf_id)

def format_syrian_phone(raw_phone: Any) -> str:
    """تنسيق وتجهيز رقم الهاتف ليتوافق مع اشتراطات السيرفر السوري (يبدأ بـ 09 ويتكون من 10 أرقام)"""
    if not raw_phone:
        return "0935841436"  # رقم افتراضي صالح لحساب الأدمن
    
    arabic_numerals = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
    clean = str(raw_phone).translate(arabic_numerals)
    digits = re.sub(r'\D', '', clean)
    
    if digits.startswith("00963"):
        digits = digits[5:]
    elif digits.startswith("963"):
        digits = digits[3:]
    elif digits.startswith("0"):
        digits = digits[1:]
        
    if digits.startswith("9") and len(digits) == 9:
        return "0" + digits
    elif len(digits) == 10 and digits.startswith("09"):
        return digits
    elif digits.startswith("9") and len(digits) > 9:
        return "0" + digits[:9]
        
    return "0935841436"

def format_price(amount: Any) -> str:
    """تحويل السعر لرقم صالح (أكبر من أو يساوي 0) لا يتجاوز الحد الأقصى"""
    if amount is None or amount == "":
        return "0"
    arabic_numerals = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
    clean = str(amount).translate(arabic_numerals)
    clean = re.sub(r'[^\d.]', '', clean)
    if not clean:
        return "0"
    try:
        val = float(clean)
        if val < 0:
            val = 0
        if val > 999999999:
            val = 999999999
        if val == int(val):
            return str(int(val))
        return str(val)
    except Exception:
        return "0"

def format_title(title: Any, desc: str = "") -> str:
    """ضمان أن العنوان بين 3 و 80 حرفاً"""
    t = str(title or "").replace("\n", " ").strip()
    if not t or len(t) < 3:
        clean_d = str(desc or "").replace("\n", " ").strip()
        t = clean_d[:75].strip() if clean_d else "إعلان مميز للبيع"
    if len(t) < 3:
        t = "إعلان للبيع"
    return t[:80].strip()

def format_description(desc: Any, title: str = "") -> str:
    """ضمان أن الوصف بين 10 و 5000 حرفاً"""
    d = str(desc or "").strip()
    if len(d) < 10:
        d = f"{title}\nتفاصيل إضافية: يرجى التواصل بالهاتف لمزيد من المعلومات."
    if len(d) < 10:
        d = d.ljust(12, '.')
    return d[:5000].strip()

def format_condition(cond: Any) -> str:
    """تحويل الحالة لقيمة يقبلها جدول قاعدة البيانات enum('new', 'used')"""
    if not cond:
        return "used"
    s = str(cond).strip().lower()
    if s in ["new", "جديد", "جديدة", "وكالة", "كرتونة"]:
        return "new"
    return "used"

def export_ad_to_import_folder(ad: Dict[str, Any]) -> Tuple[bool, str]:
    """
    تصدير الإعلان مباشرة إلى مجلد إعلانات_للاستيراد على سطح المكتب مع كافة صوره وملف info.txt
    """
    import_base = DESKTOP_IMPORT_DIR
    if not os.path.exists(import_base):
        import_base = os.path.join(os.path.expanduser("~"), "Desktop", "إعلانات_للاستيراد")
        os.makedirs(import_base, exist_ok=True)

    try:
        # 1. تحديد اسم مجلد الإعلان
        phone = format_syrian_phone(ad.get("phone_number"))
        timestamp_slug = int(time.time())
        folder_name = f"إعلان_{phone}_{timestamp_slug % 10000}"
        ad_folder_path = os.path.join(import_base, folder_name)
        os.makedirs(ad_folder_path, exist_ok=True)

        # 2. نسخ كافة صور الإعلان المعالجة إلى داخل مجلده
        nimages = ad.get("nimages", [])
        copied_images_count = 0
        for img_name in nimages:
            src_img = os.path.join(IMGS_DIR, img_name)
            if os.path.exists(src_img):
                dst_img = os.path.join(ad_folder_path, img_name)
                shutil.copy2(src_img, dst_img)
                copied_images_count += 1

        # 3. تجهيز بيانات ملف info.txt بدقة تامة وفق مواصفات المنصة
        title = format_title(ad.get("clean_title"), ad.get("clean_description") or ad.get("description", ""))
        cat_id, cat_name = detect_category_id(ad)
        city_id = int(ad.get("id-citie") or 1)
        sub_dist_id = ad.get("id-sub_districts")
        desc = format_description(ad.get("clean_description") or ad.get("description"), title)
        account_name = ad.get("publisher_name") or extract_or_generate_account_name(f"{title} {desc}")
        
        price_info = ad.get("price_info", {})
        price_amount = format_price(price_info.get("amount"))
        currency = price_info.get("currency") or "SYP"
        if currency not in ["USD", "SYP"]:
            currency = "SYP"

        ad_url = ad.get("ad_url") or ""

        info_lines = [
            f"العنوان: {title}",
            f"القسم_id: {cat_id}",
            f"المدينة_id: {city_id}"
        ]
        
        if sub_dist_id:
            info_lines.append(f"المنطقة_id: {sub_dist_id}")
            
        info_lines.append(f"السعر: {price_amount}")
        info_lines.append(f"العملة: {currency}")
        info_lines.append(f"الهاتف: {phone}")
        info_lines.append(f"اسم_المعلن: {account_name}")
            
        if ad_url:
            info_lines.append(f"رابط_الإعلان: {ad_url}")

        specs = ad.get("specifications") or {}
        if specs:
            info_lines.append("المواصفات:")
            if specs.get("make"): info_lines.append(f"- الماركة: {specs['make']}")
            if specs.get("model"): info_lines.append(f"- الطراز: {specs['model']}")
            if specs.get("year"): info_lines.append(f"- سنة الصنع: {specs['year']}")
            if specs.get("transmission"): info_lines.append(f"- ناقل الحركة: {specs['transmission']}")
            if specs.get("fuel_type"): info_lines.append(f"- الوقود: {specs['fuel_type']}")
            if specs.get("condition"): info_lines.append(f"- الحالة: {specs['condition']}")
            if specs.get("color"): info_lines.append(f"- اللون: {specs['color']}")
            if specs.get("mileage"): info_lines.append(f"- الكيلومتراج: {specs['mileage']}")
            if specs.get("area"): info_lines.append(f"- المساحة: {specs['area']}")
            if specs.get("rooms"): info_lines.append(f"- الغرف: {specs['rooms']}")
            if specs.get("features"): info_lines.append(f"- الميزات: {', '.join(specs['features'])}")
            
        info_lines.append(f"الوصف: {desc}")

        info_file_path = os.path.join(ad_folder_path, "info.txt")
        with open(info_file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(info_lines))
            f.flush()
            os.fsync(f.fileno())

        return True, f"تم التصدير بنجاح لمجلد: {folder_name} ({copied_images_count} صور)"

    except Exception as e:
        return False, f"خطأ أثناء تصدير الإعلان: {e}"

def save_to_published_db(ad: Dict[str, Any]):
    """حفظ الإعلان المنشور في قاعدة بيانات الإعلانات المنشورة"""
    try:
        published_list = []
        if os.path.exists(PUBLISHED_FILE):
            try:
                with open(PUBLISHED_FILE, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        published_list = json.loads(content)
            except Exception:
                pass

        ad_id = ad.get("ad_url") or ad.get("clean_title")
        existing_ids = {item.get("ad_url") or item.get("clean_title") for item in published_list}
        
        ad_copy = ad.copy()
        if "published_at" not in ad_copy or not ad_copy["published_at"]:
            ad_copy["published_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        ad_copy["publish_status"] = "published"
        
        if ad_id not in existing_ids:
            published_list.append(ad_copy)
        else:
            # تحديث الإعلان الحالي إذا وجد
            for i, itm in enumerate(published_list):
                if (itm.get("ad_url") or itm.get("clean_title")) == ad_id:
                    published_list[i] = ad_copy
                    break
        
        with open(PUBLISHED_FILE, "w", encoding="utf-8") as f:
            json.dump(published_list, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
    except Exception as e:
        print(f"[!] خطأ أثناء حفظ الإعلان المنشور: {e}")

BRIDGE_URL = "https://api.lelbai.com/public/bridge.php"
BRIDGE_SECRET = "lelbai_bridge_secure_key_2026_9984"

def query_remote_db(sql: str, bindings: list = None) -> dict:
    """تنفيذ استعلام SELECT عبر الجسر المباشر لقاعدة البيانات"""
    try:
        payload = {"sql": sql, "bridge_secret": BRIDGE_SECRET}
        if bindings:
            payload["bindings"] = bindings
        resp = requests.post(
            f"{BRIDGE_URL}?action=query",
            json=payload,
            headers={"X-Bridge-Secret": BRIDGE_SECRET, "Content-Type": "application/json"},
            timeout=10
        )
        return resp.json()
    except Exception as e:
        print(f"[!] خطأ في استعلام الجسر: {e}")
        return {"success": False, "rows": []}

def execute_remote_db(sql: str, bindings: list = None) -> dict:
    """تنفيذ استعلام UPDATE/INSERT عبر الجسر المباشر لقاعدة البيانات"""
    try:
        payload = {"sql": sql, "bridge_secret": BRIDGE_SECRET}
        if bindings:
            payload["bindings"] = bindings
        resp = requests.post(
            f"{BRIDGE_URL}?action=statement",
            json=payload,
            headers={"X-Bridge-Secret": BRIDGE_SECRET, "Content-Type": "application/json"},
            timeout=10
        )
        return resp.json()
    except Exception as e:
        print(f"[!] خطأ في تنفيذ أمر الجسر: {e}")
        return {"success": False, "affected": 0}

def assign_listing_to_dummy_bot(listing_uuid: str, ad: Dict[str, Any]) -> Tuple[int, str]:
    """
    إنشاء حساب وهمي مستقل تماماً وخاص بهذا الإعلان فقط (حساب منفصل لكل إعلان)،
    ووسمه كإعلان مسحوب (is_scraped = 1, source_type = 'scraped') 
    لضمان عدم ظهوره نهائياً في الحساب الشخصي للأدمن، وضمان أن لكل إعلان حسابه المستقل.
    """
    raw_phone = format_syrian_phone(ad.get("phone_number"))
    publisher_name = ad.get("publisher_name") or extract_or_generate_account_name(
        f"{ad.get('clean_title', '')} {ad.get('clean_description', '')}"
    )
    city_id = int(ad.get("id-citie") or 1)
    source_url = ad.get("ad_url") or ""

    # فحص ما إذا كان رقم الهاتف غير مستخدم من قبل في جدول users
    phone_for_user = raw_phone
    if not phone_for_user or phone_for_user == "0935841436":
        phone_for_user = None
    else:
        chk = query_remote_db("SELECT id FROM users WHERE phone = ? LIMIT 1", [phone_for_user])
        if chk.get("rows"):
            phone_for_user = None  # مستخدم مسبقاً، سنولد رقماً فريداً جديداً لهذا الحساب

    # إذا كان الرقم مستخدماً أو خاصاً بالأدمن، نولد رقماً سورياً فريداً خاصاً بهذا الحساب الجديد
    while not phone_for_user:
        candidate = f"09{random.randint(11000000, 99999999)}"
        chk = query_remote_db("SELECT id FROM users WHERE phone = ? LIMIT 1", [candidate])
        if not chk.get("rows"):
            phone_for_user = candidate

    unique_suffix = secrets.token_hex(3)
    username_slug = f"usr_{phone_for_user[-6:]}_{unique_suffix}"

    # إنشاء حساب مستقل تماماً وخاص بهذا الإعلان فقط
    ins_res = execute_remote_db(
        """
        INSERT INTO users (name, username, phone, city_id, role, is_bot, created_at, updated_at)
        VALUES (?, ?, ?, ?, 'user', 1, NOW(), NOW())
        """,
        [publisher_name, username_slug, phone_for_user, city_id]
    )
    new_bot_id = int(ins_res.get("last_insert_id") or 4)

    # ربط الإعلان بالحساب الجديد المنفصل ووسمه كـ scraped
    execute_remote_db(
        """
        UPDATE listings 
        SET user_id = ?, is_scraped = 1, source_type = 'scraped', source_url = ?
        WHERE uuid = ?
        """,
        [new_bot_id, source_url, listing_uuid]
    )

    ad["assigned_user_id"] = new_bot_id
    ad["publisher_name"] = publisher_name
    ad["is_scraped"] = True
    return new_bot_id, publisher_name

def publish_ad_to_website(ad: Dict[str, Any]) -> Tuple[bool, str]:
    """
    نشر الإعلان:
    1. تصدير مباشر إلى مجلد إعلانات_للاستيراد (صور + info.txt).
    2. إرسال إلى API الموقع الرسمي بملفات الصور والمواصفات الكاملة.
    3. ربطه فوراً بحساب وهمي (is_scraped = 1) لحمايته من الظهور بحساب الأدمن.
    4. حفظه في سجل المنشورات المعتمدة.
    """
    # 0. التحقق الاستباقي من عدم التكرار محلياً أو على خادم الموقع
    ad_url = ad.get("ad_url")
    ad_title = ad.get("clean_title")
    if os.path.exists(PUBLISHED_FILE):
        try:
            with open(PUBLISHED_FILE, "r", encoding="utf-8") as f:
                c = f.read().strip()
                if c:
                    pub_data = json.loads(c)
                    for item in pub_data:
                        if (ad_url and item.get("ad_url") == ad_url) or (ad_title and item.get("clean_title") == ad_title):
                            return True, "⚠️ هذا الإعلان تم نشره بالفعل مسبقاً في سجل المنشورات!"
        except Exception:
            pass

    # التحقق من قاعدة البيانات عن بعد عبر الجسر
    if ad_url:
        chk_remote = query_remote_db("SELECT id, uuid FROM listings WHERE source_url = ? LIMIT 1", [ad_url])
        if chk_remote.get("rows"):
            existing_uuid = chk_remote["rows"][0].get("uuid")
            ad["server_uuid"] = existing_uuid
            ad["publish_status"] = "published"
            save_to_published_db(ad)
            return True, f"الإعلان موجود مسبقاً على الموقع برقم المعرف ({existing_uuid})!"

    # 1. تصدير فوري لمجلد الاستيراد
    export_ok, export_msg = export_ad_to_import_folder(ad)

    cfg = load_config()
    api_url = cfg.get("website_api_url", "").strip() or "https://api.lelbai.com/public/api/listings"
    api_key = cfg.get("website_api_key", "").strip() or "67|5181926855ca52522dec3990517f272b027b745f"

    online_published = False
    server_ad_id = None
    msg_detail = ""

    if api_url and api_url.startswith("http"):
        headers = {
            "Accept": "application/json",
            "User-Agent": "Lelbai-AdScraper-Bot/2.0"
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        title = format_title(ad.get("clean_title"), ad.get("clean_description") or ad.get("description", ""))
        desc = format_description(ad.get("clean_description") or ad.get("description"), title)
        cat_id, _ = detect_category_id(ad)
        city_id = int(ad.get("id-citie") or 1)
        sub_dist_id = ad.get("id-sub_districts")
        phone = format_syrian_phone(ad.get("phone_number"))
        price = format_price(ad.get("price_info", {}).get("amount"))
        currency = ad.get("price_info", {}).get("currency") or "SYP"
        if currency not in ["USD", "SYP"]:
            currency = "SYP"

        specs = dict(ad.get("specifications") or {})
        if sub_dist_id:
            specs["sub_district_id"] = sub_dist_id

        data = {
            "title": title,
            "category_id": cat_id,
            "city_id": city_id,
            "description": desc,
            "price": price,
            "currency": currency,
            "contact_phone": phone,
            "show_phone": "1",
            "condition": format_condition(specs.get("condition")),
            "commission_agreed": "1",
            "attributes": json.dumps(specs, ensure_ascii=False)
        }

        files = []
        open_handles = []
        nimages = ad.get("nimages", [])
        try:
            for img_name in nimages[:10]:
                img_path = os.path.join(IMGS_DIR, img_name)
                if os.path.exists(img_path):
                    ext = os.path.splitext(img_name)[1].lower()
                    mime = "image/webp"
                    if ext in [".jpg", ".jpeg"]:
                        mime = "image/jpeg"
                    elif ext == ".png":
                        mime = "image/png"
                    fh = open(img_path, "rb")
                    open_handles.append(fh)
                    files.append(("images[]", (img_name, fh, mime)))

            if files:
                resp = requests.post(api_url, data=data, files=files, headers=headers, timeout=45)
            else:
                data["images"] = nimages
                headers["Content-Type"] = "application/json"
                resp = requests.post(api_url, json=data, headers=headers, timeout=25)

            if resp.status_code in [200, 201]:
                online_published = True
                try:
                    res_json = resp.json()
                    server_ad_id = res_json.get("uuid") or res_json.get("listing_id")
                except Exception:
                    pass

                # ربط الإعلان فوراً بحساب وهمي مستقل خاص به (is_scraped = 1) وحمايته من الظهور بحساب الأدمن الشخصي
                bot_uid = 4
                account_disp = ""
                if server_ad_id:
                    bot_uid, account_disp = assign_listing_to_dummy_bot(server_ad_id, ad)

                ad["server_uuid"] = server_ad_id
                ad["server_status"] = "active"
                ad["publish_status"] = "published"
                if not account_disp:
                    account_disp = ad.get("publisher_name") or f"حساب #{bot_uid}"
                msg_detail = f"🚀 تم نشر الإعلان بنجاح في حساب وهمي خاص ومستقل باسم ({account_disp})!\nمعرف الإعلان: {server_ad_id or ''}"
            elif resp.status_code == 422:
                err_text = ""
                try:
                    err_json = resp.json()
                    errs = err_json.get("errors", {})
                    if isinstance(errs, dict):
                        parts = []
                        for k, v in errs.items():
                            parts.append(f"{k}: {', '.join(v) if isinstance(v, list) else v}")
                        err_text = " - ".join(parts)
                    else:
                        err_text = str(errs)
                except Exception:
                    err_text = resp.text[:120]
                msg_detail = f"⚠️ تم التجهيز محلياً في مجلد الاستيراد، لكن السيرفر رفض البيانات برمز (422):\n{err_text}"
            else:
                msg_detail = f"⚠️ تم التجهيز محلياً في مجلد الاستيراد، لكن خادم الموقع رد برمز ({resp.status_code}): {resp.text[:120]}"

        except Exception as e:
            msg_detail = f"⚠️ تم التجهيز محلياً في مجلد الاستيراد، لكن تعذر الاتصال بسيرفر الموقع: {e}"
        finally:
            for fh in open_handles:
                try:
                    fh.close()
                except Exception:
                    pass
    else:
        msg_detail = "📁 تم تجهيز وتصدير الإعلان إلى مجلد سطح المكتب (إعلانات_للاستيراد).\n⚠️ تنبيه: لم يتم الرفع المباشر عبر الإنترنت لأن حقل 'رابط API الموقع' غير محدد في صفحة الإعدادات."

    # 2. حفظ في قاعدة البيانات المحلية
    save_to_published_db(ad)

    return (online_published or not api_url), msg_detail

