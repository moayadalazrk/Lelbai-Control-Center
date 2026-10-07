# -*- coding: utf-8 -*-
"""
وحدة الفلترة وتصنيف المدن والمناطق السورية بالاعتماد على ملفات البيانات CSV:
- asstes/cities.csv
- asstes/sub_districts.csv

المخرجات التصنيفية المطلوبة:
- id-citie: معرف المدينة الرئيسية (أو null)
- id-sub_districts: معرف المنطقة الفرعية (أو null)
"""

import os
import re
import csv
from typing import List, Tuple, Optional, Dict, Any

# خريطة تحويل الأرقام المشرقية/الهندية والعربية إلى أرقام إنجليزية قياسية
EASTERN_TO_WESTERN_DIGITS = str.maketrans({
    '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
    '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9',
    '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
    '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9'
})

# تحميل بيانات المدن والمناطق من ملفات CSV
CITIES_BY_ID = {}
CITIES_BY_NAME = {}
SUB_DISTRICTS_BY_ID = {}
SUB_DISTRICTS_LIST = []

def _find_asset_path(filename: str) -> str:
    """البحث عن مسار ملف البيانات في مجلد asstes أو assets"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(base_dir, "asstes", filename),
        os.path.join(base_dir, "assets", filename),
        os.path.join(os.getcwd(), "asstes", filename),
        os.path.join(os.getcwd(), "assets", filename)
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return candidates[0]

def load_location_database():
    """تحميل وبناء فهارس المدن والمناطق السورية من ملفات CSV"""
    global CITIES_BY_ID, CITIES_BY_NAME, SUB_DISTRICTS_BY_ID, SUB_DISTRICTS_LIST
    
    CITIES_BY_ID.clear()
    CITIES_BY_NAME.clear()
    SUB_DISTRICTS_BY_ID.clear()
    SUB_DISTRICTS_LIST.clear()

    cities_path = _find_asset_path("cities.csv")
    sub_districts_path = _find_asset_path("sub_districts.csv")

    # 1. قراءة المدن
    if os.path.exists(cities_path):
        with open(cities_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                city_id = int(row["id"])
                name_ar = row["name_ar"].strip()
                slug = row.get("slug", "").strip()
                city_info = {
                    "id": city_id,
                    "name_ar": name_ar,
                    "slug": slug
                }
                CITIES_BY_ID[city_id] = city_info
                CITIES_BY_NAME[name_ar] = city_info
    else:
        # احتياط افتراضي في حال عدم وجود الملف
        default_cities = [
            (1, "دمشق"), (2, "ريف دمشق"), (3, "حلب"), (4, "ريف حلب"),
            (5, "إدلب"), (6, "حمص"), (7, "حماة"), (8, "اللاذقية"),
            (9, "دير الزور"), (10, "الحسكة"), (11, "درعا"), (12, "طرطوس"),
            (13, "الرقة"), (14, "السويداء"), (15, "القنيطرة")
        ]
        for cid, cname in default_cities:
            info = {"id": cid, "name_ar": cname, "slug": ""}
            CITIES_BY_ID[cid] = info
            CITIES_BY_NAME[cname] = info

    # 2. قراءة المناطق الفرعية
    if os.path.exists(sub_districts_path):
        with open(sub_districts_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sub_id = int(row["id"])
                city_id = int(row["city_id"])
                name_ar = row["name_ar"].strip()
                name_en = row.get("name_en", "").strip()
                slug = row.get("slug", "").strip()
                
                sub_info = {
                    "id": sub_id,
                    "city_id": city_id,
                    "name_ar": name_ar,
                    "name_en": name_en,
                    "slug": slug
                }
                SUB_DISTRICTS_BY_ID[sub_id] = sub_info
                SUB_DISTRICTS_LIST.append(sub_info)
                
        # ترتيب المناطق الفرعية حسب طول الاسم تنازلياً (الأطول أولاً) لتفادي التداخل
        SUB_DISTRICTS_LIST.sort(key=lambda x: len(x["name_ar"]), reverse=True)

# تحميل الفهارس عند استيراد الوحدة
load_location_database()

# مرادفات وصيغ شائعة للمدن السورية لربطها بـ ID المدينة في cities.csv
CITY_ALIASES = {
    "الشام": 1,
    "شام": 1,
    "دمشق المدينة": 1,
    "دمشق": 1,
    "ريف الشام": 2,
    "ريف دمشق": 2,
    "الشهباء": 3,
    "شهباء": 3,
    "حلب": 3,
    "ريف حلب": 4,
    "ادلب": 5,
    "إدلب": 5,
    "حمص": 6,
    "العدية": 6,
    "حماة": 7,
    "حماه": 7,
    "حما": 7,
    "اللاذقية": 8,
    "اللاذقيه": 8,
    "الاذقية": 8,
    "الاذقيه": 8,
    "لاذقية": 8,
    "لاذقيه": 8,
    "دير الزور": 9,
    "ديرالزور": 9,
    "الدير": 9,
    "الحسكة": 10,
    "الحسكه": 10,
    "حسكة": 10,
    "القامشلي": 10,
    "قامشلي": 10,
    "درعا": 11,
    "حوران": 11,
    "طرطوس": 12,
    "طرطوسية": 12,
    "طرطوس_المدينة": 12,
    "طرطوس المدينة": 12,
    "الرقة": 13,
    "الرقه": 13,
    "رقة": 13,
    "رقه": 13,
    "السويداء": 14,
    "السويدا": 14,
    "سويداء": 14,
    "سويدا": 14,
    "القنيطرة": 15,
    "القنيطره": 15,
    "الجولان": 15
}

# مرادفات خاصة ببعض المناطق الشائعة لربطها بالـ ID المناسب في sub_districts
SUB_DISTRICT_ALIASES = {
    "المزه": "المزة",
    "كفر سوسة": "كفرسوسة",
    "ابو رمانة": "أبو رمانة",
    "اشرفية صحنايا": "أشرفية صحنايا",
    "معضمية الشام": "معضمية الشام",
    "المعضمية": "معضمية الشام",
    "جديده عرطوز": "جديدة عرطوز",
    "عرطوز": "جديدة عرطوز",
    "الكسوه": "الكسوة",
    "محرده": "محردة",
    "جبله": "جبلة",
    "ازرع": "إزرع",
    "شرقي ركن الدين": "ركن الدين",
    "ركن الدين": "ركن الدين",
    "ميسات": "الميسات",
    "الميسات": "الميسات"
}

def normalize_text(text: str) -> str:
    """تنظيف وتوحيد النص والأرقام"""
    if not text:
        return ""
    text = text.translate(EASTERN_TO_WESTERN_DIGITS)
    return text

def extract_syrian_phone_numbers(text: str) -> List[str]:
    """
    استخراج أرقام الهواتف السورية من النص بجميع الصيغ:
    - موبايل: 09xxxxxxxx (10 خانات تبدأ بـ 093, 094, 095, 096, 098, 099, إلخ)
    - دولي: +9639xxxxxxxx أو 009639xxxxxxxx أو 9639xxxxxxxx
    - أرقام أرضية دولية: +96311xxxxxxx إلخ
    """
    if not text:
        return []
    
    norm_text = normalize_text(text)
    found_numbers = set()
    
    # النمط 1: أرقام الموبايل المحلية بصيغ متعددة
    mobile_local_pattern = re.compile(
        r'(?:(?<=\D)|(?<=^))'
        r'(09[345689][0-9\s\-_./()]{6,14}[0-9])'
        r'(?:(?=\D)|(?=$))'
    )
    
    for match in mobile_local_pattern.finditer(norm_text):
        raw_num = match.group(1)
        clean_num = re.sub(r'[^0-9]', '', raw_num)
        if len(clean_num) == 10 and clean_num.startswith("09"):
            found_numbers.add(clean_num)
            
    # النمط 2: الأرقام بالصيغة الدولية (+963 أو 00963 أو 963)
    intl_pattern = re.compile(
        r'(?:(?<=\D)|(?<=^))'
        r'(\+?963|00963)[0-9\s\-_./()]{8,15}[0-9]'
        r'(?:(?=\D)|(?=$))'
    )
    
    for match in intl_pattern.finditer(norm_text):
        raw_num = match.group(0)
        clean_num = re.sub(r'[^0-9]', '', raw_num)
        
        if clean_num.startswith("00963"):
            clean_num = clean_num[2:]
            
        if clean_num.startswith("9639") and len(clean_num) == 12:
            local_formatted = "0" + clean_num[3:]
            found_numbers.add(local_formatted)
        elif clean_num.startswith("963") and len(clean_num) in [11, 12]:
            found_numbers.add("+" + clean_num)
            
    # النمط 3: أرقام عامة تبدأ بـ 09 وتتكون بالضبط من 10 أرقام متتالية
    direct_pattern = re.findall(r'\b(09\d{8})\b', norm_text)
    for num in direct_pattern:
        found_numbers.add(num)

    return sorted(list(found_numbers))

def classify_location(text: str, group_context: str = "") -> Dict[str, Any]:
    """
    تصنيف الإعلان جغرافياً واستخراج:
    - id-citie: معرف المدينة في cities.csv (أو null)
    - id-sub_districts: معرف المنطقة في sub_districts.csv (أو null)
    - city_name: اسم المدينة بالعربي
    - sub_district_name: اسم المنطقة بالعربي (أو null)
    """
    if not text:
        text = ""

    # تنظيف الهاشتاغات والشرطات السفلية للبحث
    search_text = text.replace("#", " ").replace("_", " ")
    norm_text = normalize_text(search_text).lower()

    detected_city_id = None
    detected_sub_id = None
    detected_city_name = None
    detected_sub_name = None

    # 1. البحث أولاً عن المناطق الفرعية في نص الإعلان
    # أ) فحص المرادفات الخاصة بالمناطق
    for alias_name, target_sub_name in SUB_DISTRICT_ALIASES.items():
        pattern = r'(?:\b|\s|^|،|,)' + re.escape(alias_name.lower()) + r'(?:\b|\s|$|،|,)'
        if re.search(pattern, norm_text) or alias_name.lower() in norm_text:
            # مطابقة اسم المنطقة في قائمة المناطق
            for sub in SUB_DISTRICTS_LIST:
                if sub["name_ar"] == target_sub_name or sub["name_ar"] == alias_name:
                    detected_sub_id = sub["id"]
                    detected_city_id = sub["city_id"]
                    detected_sub_name = sub["name_ar"]
                    if detected_city_id in CITIES_BY_ID:
                        detected_city_name = CITIES_BY_ID[detected_city_id]["name_ar"]
                    break
            if detected_sub_id:
                break

    # ب) فحص كافة المناطق الفرعية من قاعدة البيانات
    if not detected_sub_id:
        for sub in SUB_DISTRICTS_LIST:
            sub_name = sub["name_ar"].lower()
            if len(sub_name) < 3:
                continue
            pattern = r'(?:\b|\s|^|،|,)' + re.escape(sub_name) + r'(?:\b|\s|$|،|,)'
            if re.search(pattern, norm_text) or sub_name in norm_text:
                detected_sub_id = sub["id"]
                detected_city_id = sub["city_id"]
                detected_sub_name = sub["name_ar"]
                if detected_city_id in CITIES_BY_ID:
                    detected_city_name = CITIES_BY_ID[detected_city_id]["name_ar"]
                break

    # 2. إذا لم يتم اكتشاف منطقة فرعية، نبحث عن اسم المدينة الرئيسية في النص
    if not detected_city_id:
        for alias, cid in CITY_ALIASES.items():
            pattern = r'(?:\b|\s|^|،|,)' + re.escape(alias.lower()) + r'(?:\b|\s|$|،|,)'
            if re.search(pattern, norm_text) or alias.lower() in norm_text:
                detected_city_id = cid
                if cid in CITIES_BY_ID:
                    detected_city_name = CITIES_BY_ID[cid]["name_ar"]
                break

    # 3. إذا لم يذكر في النص، نبحث في سياق واسم المجموعة (مثل: سيارات للبيع في دمشق)
    if not detected_city_id and group_context:
        norm_group = normalize_text(group_context).lower()
        for alias, cid in CITY_ALIASES.items():
            pattern = r'(?:\b|\s|^|،|,)' + re.escape(alias.lower()) + r'(?:\b|\s|$|،|,)'
            if re.search(pattern, norm_group) or alias.lower() in norm_group:
                detected_city_id = cid
                if cid in CITIES_BY_ID:
                    detected_city_name = CITIES_BY_ID[cid]["name_ar"]
                break

    # تركيب الوصف المكتشف للقراءة المباشرة
    if detected_city_name and detected_sub_name:
        location_detected = f"{detected_city_name} ({detected_sub_name})"
    elif detected_city_name:
        location_detected = detected_city_name
    else:
        location_detected = "سوريا"

    return {
        "id-citie": detected_city_id,
        "id-sub_districts": detected_sub_id,
        "city_name": detected_city_name,
        "sub_district_name": detected_sub_name,
        "location_detected": location_detected
    }

def clean_ad_description(text: str) -> str:
    """
    تنظيف نص ووصف الإعلان بدقة من كافة شوائب واجهة فيسبوك:
    - إزالة أزرار (عرض أقل / عرض المزيد / See more / See less)
    - إزالة صناديق التعليقات (اكتب تعليقاً عاماً...)
    - إزالة قوائم التعليقات والردود وعدادات التفاعل
    - إزالة سطور الوقت والتاريخ ورؤوس المشاركات المشتركة
    - إزالة اسم الناشر في البداية والنهاية وأزرار المتابعة (· متابعة)
    - إزالة عبارة (اكمل وصف / أكمل وصف)
    """
    if not text:
        return ""

    # 1. إزالة أزرار التوسيع
    text = re.sub(r'(?:عرض أقل|\.\.\.\s*عرض المزيد|عرض المزيد|See more|See less|\.\.\.\s*See more)', '', text)
    
    # 2. إزالة صندوق التعليقات وأي محتوى بعده
    text = re.sub(r'اكتب تعليق[اً|ا].*', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'Write a comment.*', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'عرض المزيد من التعليقات.*', '', text, flags=re.DOTALL)
    text = re.sub(r'View more comments.*', '', text, flags=re.DOTALL)
    
    lines = [line.strip() for line in text.split('\n')]
    cleaned_lines = []
    
    for line in lines:
        if not line:
            continue
            
        # إزالة عبارات (اكمل وصف / أكمل وصف / اكمل الوصف) إذا كانت سطر مستقل
        if re.match(r'^(?:أ|ا)?كمل\s+(?:ال)?وصف$', line.strip()):
            continue

        # تجاهل السطور التي تحتوي فقط على رموز أو أرقام فردية (مثل +11, +27, +39, ١٦, ٠, ·)
        if re.match(r'^(?:\+\d+|\d+|[٠-٩]+|[·•\-*#_~]+)$', line):
            continue
            
        # تجاهل سطور الوقت والتاريخ (مثل: ٤ د, ٣ س, 2 ي, 1 ع, 6 يناير 2025, 25 أغسطس...)
        if re.match(r'^(?:[٠-٩\d]+\s*(?:د|س|ي|ش|ع|م|h|m|d|w|y|min|hr|hrs|days?)\s*[·•]?.*)$', line):
            continue
        if re.match(r'^(?:\d{1,2}\s+(?:يناير|فبراير|مارس|أبريل|مايو|يونيو|يوليو|أغسطس|سبتمبر|أكتوبر|نوفمبر|ديسمبر).*)$', line):
            continue
            
        # تجاهل سطور أزرار التفاعل والمتابعة
        if line in ['أعجبني', 'رد', 'مشاركة', 'متابعة', '· متابعة', 'Like', 'Reply', 'Share', 'Follow', '· Follow', 'تمت المشاركة مع مجموعة عامة']:
            continue
        if re.match(r'^(?:[·•\-]\s*)?(?:متابعة|Follow)$', line):
            continue
            
        # تجاهل عبارات الردود على التعليقات (عرض رد واحد, عرض ردين...)
        if re.match(r'^عرض (?:رد واحد|ردين|\d+ ردود|\d+ من الردود).*', line):
            continue

        # تجاهل المقاطع الصوتية
        if 'المقطع الصوتي الأصلي' in line:
            continue

        # تنظيف العبارة من وسط السطور
        line = re.sub(r'\b(?:أ|ا)?كمل\s+(?:ال)?وصف\s*', '', line).strip()
        if not line:
            continue

        cleaned_lines.append(line)
        
    # إزالة اسم الناشر والمتابعة من النهاية
    while cleaned_lines and (
        cleaned_lines[-1] in ['متابعة', '· متابعة', 'Follow', '· Follow'] or
        re.match(r'^(?:[·•\-]\s*)?(?:متابعة|Follow)$', cleaned_lines[-1])
    ):
        cleaned_lines.pop()

    # إذا كان السطر الأخير يطابق السطر الأول (اسم ناشر مكرر في الأسفل)
    if len(cleaned_lines) >= 2 and cleaned_lines[0] == cleaned_lines[-1]:
        cleaned_lines.pop()

    # فحص وإزالة اسم الناشر من السطر الأول إذا كان مجرد اسم شخص بدون محتوى إعلاني
    if len(cleaned_lines) >= 2:
        first_line = cleaned_lines[0]
        ad_keywords = ['للبيع', 'مطلوب', 'للايجار', 'للإيجار', 'سيارة', 'شقة', 'ارض', 'محل', 'بسم الله', 'سلام', 'تويوتا', 'كيا', 'مرسيدس', 'هيونداي', 'نيسان', 'مازدا', 'هوندا', 'شيري', 'بي ام', 'bmw', 'mercedes', 'kia', 'hyundai', 'nissan', 'toyota']
        has_ad_keyword = any(kw in first_line.lower() for kw in ad_keywords)
        has_digits = bool(re.search(r'\d|[٠-٩]', first_line))
        word_count = len(first_line.split())
        
        if word_count <= 4 and not has_ad_keyword and not has_digits:
            cleaned_lines.pop(0)

    final_text = "\n".join(cleaned_lines).strip()
    return final_text

def validate_ad(text: str, group_context: str = "") -> Dict[str, Any]:
    """
    فحص الإعلان بالكامل وتطبيق شرطين إجباريين:
    1. وجود رقم هاتف سوري صحيح.
    2. تحديد المدينة الرئيسية بدقة من cities.csv (id-citie ليس None).
    إذا تحقق الشرطان -> is_valid = True (تحميل الصور وإضافة الإعلان).
    إذا لم يتحقق أحدهما -> is_valid = False (سكبه وتجاهله تماماً دون تحميل أي صورة).
    """
    cleaned_text = clean_ad_description(text)
    phones = extract_syrian_phone_numbers(text)
    has_syrian_phone = len(phones) > 0
    
    loc_info = classify_location(text, group_context=group_context)
    has_city = loc_info["id-citie"] is not None
    
    # الشرطان الإجباريان:
    # 1. رقم هاتف سوري
    # 2. تحديد المدينة الرئيسية
    is_valid = has_syrian_phone and has_city
    
    return {
        "is_valid": is_valid,
        "has_city": has_city,
        "has_syrian_phone": has_syrian_phone,
        "phones": phones,
        "id-citie": loc_info["id-citie"],
        "id-sub_districts": loc_info["id-sub_districts"],
        "city_name": loc_info["city_name"],
        "sub_district_name": loc_info["sub_district_name"],
        "location_detected": loc_info["location_detected"],
        "cleaned_description": cleaned_text
    }
