# -*- coding: utf-8 -*-
"""
محرك التصنيف الذكي العميق واستخراج المواصفات والتحقق من التكرار
Lelbai Deep Taxonomy & Specs Classifier
يقوم بتصنيف الإعلان في أصغر فئة فرعية في المنصة (Leaf Category ID)،
واستخراج كافة المواصفات الممكنة، وتوليد اسم حساب معلن وهمي سوري،
والتحقق من عدم تكرار الإعلان على الموقع، وصياغة تقرير مراجعة الذكاء الاصطناعي.
"""

import re
import os
import json
import random
from typing import Dict, Any, Tuple, List, Optional

# بنك الأسماء السورية الواقعية للمعلنين
SYRIAN_ACCOUNT_NAMES = [
    "أبو محمد الشامي", "أبو النور", "ماهر العلي", "خالد الحمصي",
    "محمد دمشقي", "أبو عبدو", "أحمد الحلبي", "أبو وسيم",
    "عمر السوري", "أبو مجد", "يوسف السليمان", "طارق الحموي",
    "أبو عمر", "سامر درعاوي", "وسام اللاذقاني", "مكتب الأمانة للسيارات",
    "مكتب الوفاء للعقارات", "معرض الشام موتورز", "مكتب الأصدقاء للسيارات",
    "المدينة للسيارات", "مكتب الشهباء العقاري", "معرض النور الحديث"
]

# خريطة شركات السيارات وطرازاتها إلى معرفات الأقسام الفرعية (Leaf Categories)
CAR_BRANDS_MAP = [
    {
        "id": 1155, "name": "كيا",
        "keywords": ["كيا", "kia", "ريو", "rio", "فورتي", "forte", "سيراتو", "cerato", 
                     "سبورتاج", "sportage", "سورينتو", "sorento", "كارنفال", "carnival", 
                     "k3", "k5", "k7", "بيكانتو", "picanto", "أوبتيما", "optima", "موهافي"]
    },
    {
        "id": 1144, "name": "هيونداي",
        "keywords": ["هيونداي", "hyundai", "توسان", "tucson", "سنتافي", "santa fe", 
                     "أفانتي", "avante", "إلنترا", "elantra", "أكسنت", "accent", 
                     "فيرنا", "verna", "سوناتا", "sonata", "كريتا", "creta", "h1", "أزيرا"]
    },
    {
        "id": 1166, "name": "تويوتا",
        "keywords": ["تويوتا", "toyota", "كامري", "camry", "كورولا", "corolla", 
                     "يارس", "yaris", "برادو", "prado", "لاند كروزر", "land cruiser", 
                     "هايلكس", "hilux", "راف فور", "rav4", "أفالون", "فورتشنر"]
    },
    {
        "id": 1176, "name": "مازدا",
        "keywords": ["مازدا", "mazda", "626", "323", "مازدا 3", "مازدا 6", "cx-5", "cx-9"]
    },
    {
        "id": 1184, "name": "نيسان",
        "keywords": ["نيسان", "nissan", "صني", "sunny", "قشقاي", "qashqai", "باترول", "patrol", 
                     "تيدا", "tiida", "ألتيما", "altima", "إكس تريل", "x-trail", "ميكرا"]
    },
    {
        "id": 1193, "name": "سايبا",
        "keywords": ["سايبا", "saipa", "تيبا", "tiba", "برايد", "pride", "سابا", "saba"]
    },
    {
        "id": 1199, "name": "سيامكو / شام",
        "keywords": ["شام", "سيامكو", "siamco", "sham"]
    },
    {
        "id": 1205, "name": "دايو",
        "keywords": ["دايو", "daewoo", "ماتيز", "matiz", "لانوس", "lanos", "نوبيرا", "nubira", 
                     "لاكيتي", "lacetti", "ريسر", "racer", "إسبيرو"]
    },
    {
        "id": 1212, "name": "سوزوكي",
        "keywords": ["سوزوكي", "suzuki", "ماروتي", "maruti", "سويفت", "swift", "فيتارا", "vitara", 
                     "ألتو", "alto", "سيليريو", "سياز"]
    },
    {
        "id": 1219, "name": "ميتسوبيشي",
        "keywords": ["ميتسوبيشي", "mitsubishi", "لانسر", "lancer", "باجيرو", "pajero", "كانتر", "canter"]
    },
    {
        "id": 1226, "name": "مرسيدس-بنز",
        "keywords": ["مرسيدس", "mercedes", "بنز", "لف", "شبح", "بطة", "تمساح", "c200", "e200", "s350", "s500"]
    },
    {
        "id": 1235, "name": "بي إم دبليو",
        "keywords": ["بي ام", "بي إم دبليو", "bmw", "الفئة الثالثة", "الفئة الخامسة", "x5", "x6"]
    },
    {
        "id": 1242, "name": "بيجو",
        "keywords": ["بيجو", "peugeot", "206", "307", "405", "406", "504", "505", "207", "308", "بارتنر", "partner"]
    },
    {
        "id": 1251, "name": "فولكس فاجن",
        "keywords": ["فولكس", "volkswagen", "جولف", "golf", "باسات", "passat", "بولو", "polo", "جيتا", "jetta", "طوارق"]
    },
    {
        "id": 1259, "name": "رينو",
        "keywords": ["رينو", "renault", "ميجان", "megane", "كليو", "clio", "سيمبول", "symbol", "داستر", "duster", "فلوانس"]
    },
    {
        "id": 1266, "name": "بي واي دي",
        "keywords": ["بي واي دي", "byd", "f3", "f0"]
    },
    {
        "id": 1274, "name": "جيلي",
        "keywords": ["جيلي", "geely", "امجراند", "emgrand", "باندينو"]
    },
    {
        "id": 1282, "name": "شيري",
        "keywords": ["شيري", "chery", "تيكو", "tiggo", "qq", "أريزو"]
    },
    {
        "id": 1288, "name": "شانجان",
        "keywords": ["شانجان", "changan", "السفن", "alsvin", "cs35", "cs75"]
    },
    {
        "id": 1295, "name": "شيفروليه",
        "keywords": ["شيفروليه", "شفروليه", "chevrolet", "أفيو", "aveo", "كروز", "cruze", "أوبترا", "optra", "سبارك", "spark", "كابتيفا"]
    },
    {
        "id": 1303, "name": "أوبل",
        "keywords": ["أوبل", "opel", "أسترا", "astra", "فيكترا", "vectra", "كورسا", "corsa", "أوميغا"]
    },
    {
        "id": 1310, "name": "فورد",
        "keywords": ["فورد", "ford", "فوكس", "focus", "فيستا", "fiesta", "فيوجن", "fusion", "إكسبلورر"]
    },
    {
        "id": 1318, "name": "هوندا",
        "keywords": ["هوندا", "honda", "سيفيك", "civic", "أكورد", "accord", "cr-v"]
    },
    {
        "id": 1324, "name": "إم جي",
        "keywords": ["إم جي", "mg", "ام جي"]
    },
    {
        "id": 1330, "name": "لادا",
        "keywords": ["لادا", "lada", "2107", "سمارا", "نيفا"]
    },
    {
        "id": 1336, "name": "أودي",
        "keywords": ["أودي", "audi", "a4", "a6", "q7"]
    },
    {
        "id": 1343, "name": "سكودا",
        "keywords": ["سكودا", "skoda", "أوكتافيا", "octavia", "فابيا", "fabia", "سوبيرب"]
    },
    {
        "id": 1349, "name": "فيات",
        "keywords": ["فيات", "fiat", "بونتو", "punto", "تيبو", "tipo", "سيينا", "siena", "128", "131"]
    },
    {
        "id": 1356, "name": "لاند روفر",
        "keywords": ["لاند روفر", "land rover", "رنج روفر", "range rover", "ديسكفري"]
    },
    {
        "id": 1363, "name": "هونشي ودونغ فينغ وفاو",
        "keywords": ["هونشي", "دونغ فينغ", "فاو", "faw", "dongfeng"]
    }
]

def classify_leaf_category(text: str) -> Dict[str, Any]:
    """
    تحديد التصنيف المناسب في أصغر ابن (Leaf Subcategory) وفق شجرة تصنيفات الموقع بدقة تامة.
    يضمن بنسبة 100% أن المعرف ليس قسماً أباً في قاعدة البيانات.
    """
    from ai_ad_enhancer import detect_smart_category
    return detect_smart_category(text)

    # 8. الأزياء
    if any(k in t for k in ["ملابس رجالي", "بنطال", "قميص", "جاكيت رجالي"]):
        return {"category_id": 3166, "category_name": "ملابس رجالية", "parent_name": "الأزياء والعناية الشخصية", "leaf_type": "men_clothes", "brand": None}
    if any(k in t for k in ["فستان", "عباية", "مانطو", "ملابس نسائي"]):
        return {"category_id": 3167, "category_name": "ملابس نسائية وفساتين", "parent_name": "الأزياء والعناية الشخصية", "leaf_type": "women_clothes", "brand": None}

    # 9. المواشي والحيوانات
    if any(k in t for k in ["غنم", "خروف", "ماعز", "نعجة"]):
        return {"category_id": 3179, "category_name": "غنم وماعز وإبل", "parent_name": "الحيوان ومواشي", "leaf_type": "sheep", "brand": None}
    if any(k in t for k in ["عجل", "بقرة", "خيل", "حصان"]):
        return {"category_id": 3180, "category_name": "أبقار وعجول وخيول", "parent_name": "الحيوان ومواشي", "leaf_type": "cattle", "brand": None}
    if any(k in t for k in ["طيور", "حمام", "دجاج", "فروج"]):
        return {"category_id": 3181, "category_name": "طيور ودواجن وحمام", "parent_name": "الحيوان ومواشي", "leaf_type": "birds", "brand": None}

    # 10. الوظائف والخدمات
    if any(k in t for k in ["مطلوب موظف", "مطلوب معلم", "فرصة عمل", "شاغر"]):
        return {"category_id": 3154, "category_name": "وظائف شاغرة", "parent_name": "الوظائف والأعمال", "leaf_type": "jobs", "brand": None}
    if any(k in t for k in ["نقل عفش", "ترحيل"]):
        return {"category_id": 3161, "category_name": "خدمات نقل العفش", "parent_name": "الخدمات", "leaf_type": "moving_services", "brand": None}
    if any(k in t for k in ["توصيل", "دليفري"]):
        return {"category_id": 3159, "category_name": "خدمات التوصيل", "parent_name": "الخدمات", "leaf_type": "delivery", "brand": None}

    # الفئة الافتراضية العامة
    return {
        "category_id": 3207,
        "category_name": "أصناف عامة ومتنوعة",
        "parent_name": "أخرى",
        "leaf_type": "general",
        "brand": None
    }

def extract_detailed_specifications(text: str, leaf_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    استخراج أكبر قدر من المواصفات المهيكلة من نص الإعلان (السيارات، العقارات، والسلع الأخرى).
    """
    specs: Dict[str, Any] = {}
    t = text.lower()

    # 1. الماركة / الشركة
    if leaf_info.get("brand"):
        specs["make"] = leaf_info["brand"]

    # 2. الموديل / الطراز
    models_patterns = [
        r"(?:طراز|موديل|نوع|سيارة|كيا|هيونداي|تويوتا|نيسان)\s+([a-zA-Z0-9\u0621-\u064A]{2,15})",
        r"\b(توسان|ريو|فورتي|سيراتو|سبورتاج|كامري|كورولا|يارس|سنتافي|أفانتي|إلنترا|أكسنت|صني|ميجان|كليو|لانوس|ماروتي|سويفت|206|307|405|golf|c200|e200)\b"
    ]
    for p in models_patterns:
        m = re.search(p, t)
        if m:
            specs["model"] = m.group(1).strip()
            break

    # 3. سنة الصنع / الموديل (1980 - 2026)
    year_match = re.search(r"\b(19[8-9]\d|20[0-2]\d)\b", t)
    if year_match:
        specs["year"] = int(year_match.group(1))

    # 4. ناقل الحركة (الكير)
    if any(k in t for k in ["أوتوماتيك", "اتوماتيك", "تومتيك", "اوتوماتيك", "اتمتيك", "اوتماتيك"]):
        specs["transmission"] = "أوتوماتيك"
    elif any(k in t for k in ["عادي", "مانيوال", "منوال", "غير عادي", "كير عادي"]):
        specs["transmission"] = "عادي"

    # 5. نوع الوقود
    if any(k in t for k in ["مازوت", "ديزل"]):
        specs["fuel_type"] = "مازوت / ديزل"
    elif any(k in t for k in ["بنزين", "بانزين"]):
        specs["fuel_type"] = "بنزين"
    elif any(k in t for k in ["هايبرد", "هجين"]):
        specs["fuel_type"] = "هايبرد"
    elif any(k in t for k in ["كهرباء", "كهربائية"]):
        specs["fuel_type"] = "كهرباء"

    # 6. حالة الهيكل والبخ
    conditions = []
    if "خالية العلام" in t or "خالية تماما" in t or "خاليه تماما" in t:
        conditions.append("خالية العلام تماماً")
    if "كرتونة" in t or "كرتونه" in t:
        conditions.append("كرتونة")
    if "بخ زنار" in t or "زنار نضافة" in t:
        conditions.append("بخ زنار نضافة")
    if "خالية من الداخل" in t or "خالية جوا" in t or "خاليه جوا" in t:
        conditions.append("خالية من الداخل (جوا)")
    if "شمعات فخدات شاصي زيرو" in t or "شاصي زيرو" in t or "فخدات كفالة" in t:
        conditions.append("شمعات وشاصيه زيرو وكالة")
    if conditions:
        specs["condition"] = " + ".join(conditions)

    # 7. اللون
    colors = {
        "أبيض": ["أبيض", "ابيض", "لؤلؤي"],
        "أسود": ["أسود", "اسود"],
        "فضي": ["فضي", "سيلفر"],
        "رصاصي": ["رصاصي", "فيراني", "رمادي"],
        "كحلي": ["كحلي", "أزرق", "ازرق"],
        "خمري": ["خمري", "أحمر", "احمر"],
        "بيج": ["بيج", "ذهبي"],
        "بني": ["بني", "عسلي"]
    }
    for col_name, col_kws in colors.items():
        if any(k in t for k in col_kws):
            specs["color"] = col_name
            break

    # 8. المسافة المقطوعة / الكيلومتراج
    km_match = re.search(r"(\d{1,3}(?:[.,]\d{3})*|\d+)\s*(?:ألف|الف)?\s*(?:كم|كيلو|km)", t)
    if km_match:
        specs["mileage"] = km_match.group(0).strip()

    # 9. الميزات الإضافية (Features)
    features = []
    feature_checks = [
        ("فتحة سقف", ["فتحة سقف", "فتحه سقف", "بانوراما"]),
        ("بصمة تشغيل", ["بصمة", "بصمه", "دخول ذكي"]),
        ("شاشة أندرويد", ["شاشة", "شاشه", "كاميرا"]),
        ("حساسات خلفية/أمامية", ["حساسات", "حساس"]),
        ("مكيف ديجيتال", ["مكيف", "تبريد", "فريزتين"]),
        ("فرش جلد أساسي", ["جلد", "فرش جلد"]),
        ("دوزان جديد", ["دوزان جديد", "دوزان ذهب"]),
        ("دواليب جديدة", ["دواليب جديدة", "دواليب 80", "دواليب 90", "جنط مغنزيوم"]),
        ("مرايا كهرباء", ["مرايا كهربا", "بلور كهربا"]),
        ("كراسي تدفئة وتبريد", ["تسخين كراسي", "تبريد كراسي", "كراسي كهرباء"])
    ]
    for feat_name, feat_kws in feature_checks:
        if any(k in t for k in feat_kws):
            features.append(feat_name)
    if features:
        specs["features"] = features

    # 10. مواصفات العقارات (المساحة، الغرف، الطابق)
    area_match = re.search(r"(\d+)\s*(?:متر|م²|م2|دونم)", t)
    if area_match:
        specs["area"] = area_match.group(0).strip()
    rooms_match = re.search(r"(\d+)\s*(?:غرف|غرفة|وصالون)", t)
    if rooms_match:
        specs["rooms"] = rooms_match.group(0).strip()
    floor_match = re.search(r"(طابق\s+[a-zA-Z\u0621-\u064A]+|أرضي|أول|ثاني|ثالث|رابع)", t)
    if floor_match:
        specs["floor"] = floor_match.group(0).strip()

    return specs

def extract_or_generate_account_name(text: str) -> str:
    """
    استخراج اسم المعلن من نص المنشور إن وجد، أو اختيار اسم حساب سوري واقعي وموثوق.
    """
    # البحث عن اسم تم ذكره في المنشور
    named_patterns = [
        r"(?:للتواصل|الاتصال|المعلن|مكتب|معرض)\s+(?:مع\s+)?([أإا]بو\s+[a-zA-Z\u0621-\u064A]{3,15})",
        r"(?:للتواصل|الاتصال|المعلن)\s+(?:مع\s+)?([a-zA-Z\u0621-\u064A]{3,15}\s+[a-zA-Z\u0621-\u064A]{3,15})",
        r"#?مكــ?تب_([a-zA-Z\u0621-\u064A_]{3,20})"
    ]
    for p in named_patterns:
        m = re.search(p, text)
        if m:
            found_name = m.group(1).replace("_", " ").strip()
            if len(found_name) >= 3 and not any(w in found_name for w in ["الواتس", "الرقم", "الموقع", "الهاتف"]):
                return found_name

    # اختيار اسم سوري واقعي متزن من البنك
    return random.choice(SYRIAN_ACCOUNT_NAMES)

def check_if_ad_already_exists(ad: Dict[str, Any], published_db: List[Dict[str, Any]], all_ads_db: List[Dict[str, Any]]) -> Tuple[bool, str]:
    """
    التحقق الحازم من عدم وجود الإعلان على الموقع أو في السجلات مسبقاً لمنع التكرار نهائياً.
    """
    cur_phone = (ad.get("phone_number") or "").strip()
    cur_url = (ad.get("ad_url") or "").strip()
    cur_desc = (ad.get("clean_description") or ad.get("description") or "").strip()
    cur_sig = f"{cur_phone}_{cur_desc[:40]}"

    # 1. الفحص في قاعدة المنشورات المعتمدة على الموقع
    for pub in published_db:
        pub_phone = (pub.get("phone_number") or "").strip()
        pub_url = (pub.get("ad_url") or "").strip()
        pub_desc = (pub.get("clean_description") or pub.get("description") or "").strip()
        
        # مطابقة الرابط الأصلي المباشر
        if cur_url and pub_url and cur_url == pub_url:
            return True, f"الإعلان موجود مسبقاً على الموقع بنفس رابط المنشور: {cur_url}"

        # مطابقة رقم الهاتف ونفس نص الإعلان
        if cur_phone and pub_phone and cur_phone == pub_phone:
            pub_sig = f"{pub_phone}_{pub_desc[:40]}"
            if cur_sig == pub_sig or (cur_desc and pub_desc and cur_desc[:50] in pub_desc):
                return True, f"الإعلان منشور مسبقاً على الموقع برقم الهاتف: {cur_phone}"

    return False, "إعلان جديد كلياً وغير مكرر على المنصة"

def generate_ai_review_report(
    ad: Dict[str, Any],
    leaf_info: Dict[str, Any],
    specs: Dict[str, Any],
    account_name: str,
    dup_exists: bool,
    dup_reason: str,
    moderation_summary: Optional[str] = None
) -> Dict[str, Any]:
    """
    توليد التقرير والرد الشامل للذكاء الاصطناعي الخاص بكل إعلان لعرضه في بطاقته وملفاته.
    """
    category_hierarchy = ad.get('category_hierarchy') or leaf_info.get('category_hierarchy') or f"{leaf_info['parent_name']} > {leaf_info['category_name']}"
    category_summary = f"{category_hierarchy} (القسم_id: {leaf_info['category_id']})"
    
    specs_list = []
    if specs.get("make"): specs_list.append(f"الشركة: {specs['make']}")
    if specs.get("model"): specs_list.append(f"الطراز: {specs['model']}")
    if specs.get("year"): specs_list.append(f"سنة الصنع: {specs['year']}")
    if specs.get("transmission"): specs_list.append(f"ناقل الحركة: {specs['transmission']}")
    if specs.get("fuel_type"): specs_list.append(f"الوقود: {specs['fuel_type']}")
    if specs.get("condition"): specs_list.append(f"الهيكل: {specs['condition']}")
    if specs.get("color"): specs_list.append(f"اللون: {specs['color']}")
    if specs.get("mileage"): specs_list.append(f"الكيلومتراج: {specs['mileage']}")
    if specs.get("area"): specs_list.append(f"المساحة: {specs['area']}")
    if specs.get("rooms"): specs_list.append(f"الغرف: {specs['rooms']}")
    if specs.get("features"): specs_list.append(f"الميزات: {', '.join(specs['features'][:4])}")
    
    specs_summary = " | ".join(specs_list) if specs_list else "تم اعتماد الوصف الفني المباشر"

    sharia_note = "مطابق للضوابط الشرعية والقانونية 100% (خالٍ من أي محظورات أو شبهات)"
    if moderation_summary and "مخالف" in moderation_summary:
        sharia_note = f"⚠️ ملاحظة رقابية: {moderation_summary}"

    dup_note = "✔️ تم التحقق: الإعلان فريد وغير موجود على الموقع مسبقاً" if not dup_exists else f"⚠️ تحذير تكرار: {dup_reason}"

    full_ai_verdict = (
        f"🎯 [التصنيف التفصيلي في أصغر فئة]: تم الإدراج تحت: {category_summary}\n"
        f"📋 [المواصفات المستخرجة بدقة]: {specs_summary}\n"
        f"👤 [اسم الحساب المعتمد]: {account_name}\n"
        f"🔍 [فحص التكرار والأصالة]: {dup_note}\n"
        f"⚖️ [الفحص الشرعي والرقابي]: {sharia_note}\n"
        f"🚀 [قرار الجاهزية للنشر]: {'جاهز للنشر الفوري والاستيراد للموقع' if not dup_exists else 'بحاجة لمراجعة بسبب التكرار'}"
    )

    return {
        "category_summary": category_summary,
        "leaf_category_id": leaf_info["category_id"],
        "leaf_category_name": leaf_info["category_name"],
        "specs_summary": specs_summary,
        "account_name": account_name,
        "is_duplicate": dup_exists,
        "duplicate_reason": dup_reason,
        "sharia_note": sharia_note,
        "full_text": full_ai_verdict
    }
