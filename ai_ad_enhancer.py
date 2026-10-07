# -*- coding: utf-8 -*-
"""
محرك تحسين الإعلانات الفائق بالذكاء الاصطناعي (AI Ad Enhancer v3.0)
يقوم بتوليد:
1. عناوين تجارية جذابة واحترافية وفق معايير المتاجر الكبرى (بدون حشو، وسوم، أو كلمات تسويقية فارغة).
2. أوصاف مهيكلة ومنسقة بعناية في أقسام واضحة (📋 المواصفات، ✨ الحالة الفنية، ⭐ التجهيزات، 📍 المعاينة والتواصل).
3. تصنيف دقيق في أصغر فئة فرعية بالموقع (Deep Leaf Category) ودعم كامل لمصطلحات سوق السيارات والعقارات السورية (قصة، دوزان، شمعات، فراغة، إلخ).
4. استخراج شامل وموثوق للمواصفات والأسعار والميزات والحسابات المستقلة.
"""

import os
import re
import json
import random
from typing import Dict, Any, Tuple, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CATEGORIES_DB_FILE = os.path.join(BASE_DIR, "categories_db.json")
BRAND_LEAF_FILE = os.path.join(BASE_DIR, "brand_leaf_mapping.json")

try:
    with open(CATEGORIES_DB_FILE, "r", encoding="utf-8") as _f:
        CATEGORIES_DB = json.load(_f)
except Exception:
    CATEGORIES_DB = []

CAT_BY_ID = {c["id"]: c for c in CATEGORIES_DB}
PARENT_IDS = {c["parent_id"] for c in CATEGORIES_DB if c.get("parent_id") is not None}

try:
    with open(BRAND_LEAF_FILE, "r", encoding="utf-8") as _f:
        BRAND_LEAF_MAPPING = json.load(_f)
except Exception:
    BRAND_LEAF_MAPPING = {}

def get_category_name_by_id(cat_id: int) -> str:
    c = CAT_BY_ID.get(cat_id)
    return c["name_ar"] if c else "أخرى"

def build_category_hierarchy(cat_id: int) -> str:
    path = []
    curr = cat_id
    visited = set()
    while curr and curr not in visited:
        visited.add(curr)
        c = CAT_BY_ID.get(curr)
        if not c:
            break
        path.insert(0, c["name_ar"])
        curr = c.get("parent_id")
    return " > ".join(path) if path else "عام"

def ensure_leaf_category_id(cat_id: int) -> int:
    """
    قاعدة صارمة لا تقبل أي استثناء:
    لا يُسمح إطلاقاً بنشر إعلان تحت قسم رئيسي أو قسم له تفرعات (Parent Category).
    إذا كان المعرف المعطى قسماً أباً، يتم النزول به فوراً إلى أصغر فئة فرعية ابن (Leaf Category).
    """
    if cat_id not in PARENT_IDS:
        return cat_id
    if cat_id in (1, 1143):
        return 1832  # ماركات أخرى (Leaf مباشرة تحت سيارات للبيع 1143)
    if cat_id == 259:
        return 3207  # أصناف عامة ومتنوعة (Leaf مباشرة تحت أخرى 259)
    if str(cat_id) in BRAND_LEAF_MAPPING:
        return BRAND_LEAF_MAPPING[str(cat_id)].get("other_id", 1832)
    children = [c for c in CATEGORIES_DB if c.get("parent_id") == cat_id]
    for ch in children:
        if ch["id"] not in PARENT_IDS:
            return ch["id"]
        return ensure_leaf_category_id(ch["id"])
    return 3207

# كلمات مفتاحية وأسماء مستعارة لماركات السيارات الـ 30
BRAND_ALIASES = {
    1144: ['هيونداي', 'هيونداى', 'hyundai'],
    1155: ['كيا', 'kia'],
    1166: ['تويوتا', 'toyota'],
    1176: ['مازدا', 'ماذدا', 'mazda'],
    1184: ['نيسان', 'nissan'],
    1193: ['سايبا', 'saipa', 'سابا', 'saba'],
    1199: ['سيامكو', 'شام', 'siamco', 'sham'],
    1205: ['دايو', 'daewoo'],
    1212: ['سوزوكي', 'suzuki'],
    1219: ['ميتسوبيشي', 'مستوبيشي', 'mitsubishi'],
    1226: ['مرسيدس', 'مرسيدس-بنز', 'mercedes', 'بنز'],
    1235: ['بي إم دبليو', 'بي ام دبليو', 'بي ام', 'بي إم', 'bmw'],
    1242: ['بيجو', 'peugeot'],
    1251: ['فولكس فاجن', 'فولكسفاغن', 'فولكس', 'volkswagen', 'vw'],
    1259: ['رينو', 'renault'],
    1266: ['بي واي دي', 'byd'],
    1274: ['جيلي', 'geely'],
    1282: ['شيري', 'chery'],
    1288: ['شانجان', 'changan'],
    1295: ['شيفروليه', 'شفروليه', 'شفر', 'chevrolet', 'chevy'],
    1303: ['أوبل', 'اوبل', 'opel'],
    1310: ['فورد', 'ford'],
    1318: ['هوندا', 'honda'],
    1324: ['إم جي', 'ام جي', 'mg'],
    1330: ['لادا', 'lada'],
    1336: ['أودي', 'اودي', 'audi'],
    1343: ['سكودا', 'skoda'],
    1349: ['فيات', 'fiat'],
    1356: ['لاند روفر', 'رنج روفر', 'رينج روفر', 'land rover', 'range rover'],
    1363: ['هونشي', 'دونغ فينغ', 'فاو', 'faw', 'dongfeng', 'بيستون', 'bestune']
}

EXTRA_MODEL_ALIASES = {
    1229: ['شبح', 'فياغرا', 'w140', 'w220', 's350', 's500', 's320'],
    1230: ['لف', 'بطة', 'w123', 'w124'],
    1227: ['e200', 'e240', 'e300', 'w210', 'w211'],
    1228: ['c200', 'c180', 'c250', 'w202'],
    1164: ['k7', 'كادينزا', 'cadenza'],
    1160: ['k5', 'اوبتيما', 'أوبتيما', 'optima'],
    1157: ['k3', 'سيراتو', 'فورتي', 'cerato', 'forte'],
    1145: ['اكسنت', 'أكسنت', 'accent', 'فيرنا', 'verna'],
    1146: ['النترا', 'إلنترا', 'elantra', 'افانتي', 'أفانتي', 'avante'],
    1151: ['ازيرا', 'أزيرا', 'azera', 'غرانديور'],
    1357: ['فوغ', 'فوج', 'vogue'],
    1358: ['سبورت', 'sport'],
    1360: ['ايفوك', 'إيفوك', 'evoque', 'فيلار', 'velar'],
    1220: ['قرش', 'لانسر', 'lancer']
}

# خريطة الماركات وموديلاتها لسيارات للبيع مع المعرفات الرسمية لموقع للبيع Lelbai
CAR_MODELS_DB = [
    {
        "brand": "لاند روفر", "category_id": 1356, "category_name": "لاند روفر",
        "aliases": ["لاند روفر", "رينج روفر", "رنج روفر", "range rover", "range rove", "land rover"],
        "models": [
            ("رينج روفر فوج", ["فوج", "vogue", "hse"]),
            ("رينج روفر سبورت", ["سبورت", "sport"]),
            ("إيفوك", ["ايفوك", "إيفوك", "evoque"]),
            ("فيلار", ["فيلار", "velar"]),
            ("ديفندر", ["ديفندر", "defender"]),
            ("ديسكفري", ["ديسكفري", "discovery"])
        ]
    },
    {
        "brand": "كيا", "category_id": 1155, "category_name": "كيا",
        "aliases": ["كيا", "kia"],
        "models": [
            ("سبورتاج", ["سبورتاج", "sportage"]),
            ("كادينزا k7", ["k7", "كادينزا", "cadenza"]),
            ("أوبتيما k5", ["k5", "اوبتيما", "أوبتيما", "optima"]),
            ("سيراتو k3", ["k3", "سيراتو", "cerato"]),
            ("فورتي", ["فورتي", "forte"]),
            ("سبكترا", ["سبكترا", "spectra"]),
            ("ريو", ["ريو", "rio"]),
            ("موهافي", ["موهافي", "mohave"]),
            ("سورينتو", ["سورينتو", "sorento"]),
            ("بيكانتو", ["بيكانتو", "picanto"]),
            ("كارنفال", ["كارنفال", "carnival"]),
            ("سول", ["سول", "soul"]),
            ("سيلتوس", ["سيلتوس", "seltos"])
        ]
    },
    {
        "brand": "هيونداي", "category_id": 1144, "category_name": "هيونداي",
        "aliases": ["هيونداي", "هيونداى", "hyundai"],
        "models": [
            ("سنتافي", ["سنتافي", "سنتافيه", "santa fe", "santafe"]),
            ("توسان", ["توسان", "طوسان", "tucson"]),
            ("أفانتي", ["افانتي", "أفانتي", "avante"]),
            ("إلنترا", ["النترا", "إلنترا", "elantra"]),
            ("أكسنت", ["اكسنت", "أكسنت", "accent"]),
            ("فيرنا", ["فيرنا", "verna"]),
            ("سوناتا", ["سوناتا", "sonata"]),
            ("أزيرا", ["ازيرا", "أزيرا", "azera", "غرانديور"]),
            ("كريتا", ["كريتا", "creta"]),
            ("h1", ["h1", "اتش ون", "h-1"]),
            ("ستاريا", ["ستاريا", "staria"]),
            ("باليسيد", ["باليسيد", "palisade"])
        ]
    },
    {
        "brand": "ميتسوبيشي", "category_id": 1219, "category_name": "ميتسوبيشي",
        "aliases": ["ميتسوبيشي", "ميتسوبيشى", "مستوبيشي", "mitsubishi"],
        "models": [
            ("أوتلاندر", ["اوتلاندر", "أوتلاندر", "outlander"]),
            ("لانسر", ["لانسر", "lancer", "قرش"]),
            ("باجيرو", ["باجيرو", "pajero"]),
            ("l200", ["l200"]),
            ("غالنت", ["غالنت", "galant"])
        ]
    },
    {
        "brand": "مازدا", "category_id": 1176, "category_name": "مازدا",
        "aliases": ["مازدا", "ماذدا", "mazda"],
        "models": [
            ("مازدا 3", ["مازدا 3", "mazda 3"]),
            ("مازدا 6", ["مازدا 6", "mazda 6"]),
            ("323", ["323", "مازدا 323", "ماذدا 323"]),
            ("626", ["626", "مازدا 626"]),
            ("929", ["929", "مازدا 929"]),
            ("cx-5", ["cx-5", "cx5"]),
            ("cx-9", ["cx-9", "cx9"])
        ]
    },
    {
        "brand": "شيفروليه", "category_id": 1295, "category_name": "شيفروليه",
        "aliases": ["شيفروليه", "شفروليه", "شفر", "chevrolet", "chevy"],
        "models": [
            ("كروز", ["كروز", "cruze"]),
            ("أفيو", ["افيو", "أفيو", "aveo"]),
            ("أوبترا", ["اوبترا", "أوبترا", "optra"]),
            ("سونيك", ["سونيك", "سونك", "sonic"]),
            ("سبارك", ["سبارك", "spark"]),
            ("كابتيفا", ["كابتيفا", "captiva"]),
            ("ماليبو", ["ماليبو", "malibu"]),
            ("ترايل بليزر", ["ترايل بليزر", "تريل بليزر", "بليزر", "لطاش"])
        ]
    },
    {
        "brand": "تويوتا", "category_id": 1166, "category_name": "تويوتا",
        "aliases": ["تويوتا", "toyota"],
        "models": [
            ("كورولا", ["كورولا", "corolla"]),
            ("يارس", ["يارس", "yaris"]),
            ("كامري", ["كامري", "camry"]),
            ("برادو", ["برادو", "prado"]),
            ("لاند كروزر", ["لاند كروزر", "land cruiser", "لاندكروزر"]),
            ("هايلكس", ["هايلكس", "hilux"]),
            ("راف فور", ["راف فور", "rav4", "rav 4"]),
            ("أفالون", ["افالون", "أفالون", "avalon"]),
            ("فورتشنر", ["فورتشنر", "fortuner"])
        ]
    },
    {
        "brand": "مرسيدس-بنز", "category_id": 1226, "category_name": "مرسيدس-بنز",
        "aliases": ["مرسيدس", "مرسيدس-بنز", "mercedes", "مرسيدس بنز"],
        "models": [
            ("c-class", ["c200", "c180", "c250", "c300", "w202"]),
            ("e-class", ["e200", "e240", "e300", "e350", "w210", "w211"]),
            ("s-class", ["s350", "s500", "s320", "شبح", "فياغرا", "w140", "w220"]),
            ("لف", ["لف", "مرسيدس لف", "w123"]),
            ("بطة", ["بطة", "مرسيدس بطة", "w124"]),
            ("حوت", ["حوت"]),
            ("عيون", ["عيون"])
        ]
    },
    {
        "brand": "بي إم دبليو", "category_id": 1235, "category_name": "بي إم دبليو",
        "aliases": ["بي إم دبليو", "بي ام دبليو", "بي ام", "بي إم", "bmw"],
        "models": [
            ("الفئة الثالثة", ["الفئة الثالثة", "320i", "325i", "330i"]),
            ("الفئة الخامسة", ["الفئة الخامسة", "520i", "525i", "530i"]),
            ("الفئة السابعة", ["الفئة السابعة", "730i", "740i", "750i"]),
            ("x5", ["x5", "اكس فايف"]),
            ("x6", ["x6", "اكس سكس"]),
            ("x3", ["x3"])
        ]
    },
    {
        "brand": "نيسان", "category_id": 1184, "category_name": "نيسان",
        "aliases": ["نيسان", "nissan"],
        "models": [
            ("صني", ["صني", "sunny"]),
            ("تيدا", ["تيدا", "tiida"]),
            ("قشقاي", ["قشقاي", "qashqai"]),
            ("باترول", ["باترول", "patrol"]),
            ("ألتيما", ["التيما", "أتيما", "altima"]),
            ("إكس تريل", ["اكس تريل", "x-trail"])
        ]
    },
    {
        "brand": "فولكس فاجن", "category_id": 1251, "category_name": "فولكس فاجن",
        "aliases": ["فولكس فاجن", "فولكسفاغن", "فولكس", "volkswagen", "vw"],
        "models": [
            ("غولف", ["غولف", "جولف", "golf"]),
            ("جيتا", ["جيتا", "jetta"]),
            ("باسات", ["باسات", "passat"]),
            ("بولو", ["بولو", "polo"]),
            ("تيجوان", ["تيجوان", "tiguan"]),
            ("طوارق", ["طوارق", "touareg"])
        ]
    },
    {
        "brand": "بيجو", "category_id": 1242, "category_name": "بيجو",
        "aliases": ["بيجو", "peugeot"],
        "models": [
            ("206", ["206"]),
            ("207", ["207"]),
            ("307", ["307"]),
            ("308", ["308"]),
            ("405", ["405"]),
            ("406", ["406"]),
            ("407", ["407"]),
            ("بارتنر", ["بارتنر", "partner"])
        ]
    },
    {
        "brand": "فورد", "category_id": 1310, "category_name": "فورد",
        "aliases": ["فورد", "ford"],
        "models": [
            ("فوكس", ["فوكس", "focus"]),
            ("فيستا", ["فيستا", "fiesta"]),
            ("فيوجن", ["فيوجن", "fusion"]),
            ("اكسبلورر", ["اكسبلورر", "explorer"]),
            ("ايدج", ["ايدج", "edge"]),
            ("موستانج", ["موستانج", "mustang"]),
            ("رينجر", ["رينجر", "ranger"])
        ]
    },
    {
        "brand": "جيلي", "category_id": 1274, "category_name": "جيلي",
        "aliases": ["جيلي", "geely"],
        "models": [
            ("GX3 Pro", ["gx3 pro", "gx3", "جي اكس 3"]),
            ("امجراند", ["امجراند", "emgrand", "ec7"]),
            ("كولراي", ["كولراي", "coolray"]),
            ("اوكافانجو", ["اوكافانجو"]),
            ("بندا", ["بندا", "panda"])
        ]
    },
    {
        "brand": "شيري", "category_id": 1282, "category_name": "شيري",
        "aliases": ["شيري", "chery"],
        "models": [
            ("تيجو", ["تيجو", "تيكو", "tiggo"]),
            ("أريزو", ["اريزو", "أريزو", "arrizo"]),
            ("qq", ["qq", "كيو كيو"])
        ]
    },
    {
        "brand": "شانجان", "category_id": 1288, "category_name": "شانجان",
        "aliases": ["شانجان", "changan"],
        "models": [
            ("السفن", ["السفن", "alsvin"]),
            ("cs35", ["cs35"]),
            ("cs75", ["cs75"]),
            ("cs85", ["cs85"]),
            ("uni-t", ["uni-t", "يوني تي"])
        ]
    },
    {
        "brand": "بريليانس", "category_id": 1143, "category_name": "بريليانس",
        "aliases": ["بريليانس", "برلنس", "brilliance"],
        "models": [
            ("FSV", ["fsv"]),
            ("FRV", ["frv"]),
            ("H530", ["h530"]),
            ("V5", ["v5"])
        ]
    },
    {
        "brand": "إيسوزو", "category_id": 1143, "category_name": "إيسوزو",
        "aliases": ["ايسوزو", "إيسوزو", "سوزو", "isuzu"],
        "models": [
            ("سوزو 28", ["سوزو 28", "28"]),
            ("ديمكس", ["ديمكس", "d-max", "dmax"]),
            ("صهريج ماء", ["صهريج", "خزان"])
        ]
    },
    {
        "brand": "جاك", "category_id": 1143, "category_name": "جاك",
        "aliases": ["جاك", "jac"],
        "models": [
            ("1040", ["1040"]),
            ("شاحنة جاك", ["شاحنة", "بيك اب", "مشبكة"])
        ]
    },
    {
        "brand": "كرايسلر", "category_id": 1143, "category_name": "كرايسلر",
        "aliases": ["كرايسلر", "كلايسلر", "chrysler"],
        "models": [
            ("300C", ["300c", "c300"])
        ]
    },
    {
        "brand": "كاديلاك", "category_id": 1143, "category_name": "كاديلاك",
        "aliases": ["كاديلاك", "كديلاك", "cadillac"],
        "models": [
            ("إسكاليد", ["اسكاليد", "سكليد", "escalade"])
        ]
    },
    {
        "brand": "لادا", "category_id": 1143, "category_name": "لادا",
        "aliases": ["لادا", "اوكا", "أوكا", "lada", "oka"],
        "models": [
            ("أوكا", ["اوكا", "أوكا", "oka"]),
            ("نيفا", ["نيفا", "niva"]),
            ("سمارا", ["سمارا", "samara"])
        ]
    },
    {
        "brand": "سايبا", "category_id": 1193, "category_name": "سايبا",
        "aliases": ["سايبا", "saipa", "سابا"],
        "models": [
            ("سايبا", ["سايبا", "saipa", "تيبا", "tiba", "برايد", "pride", "سابا"])
        ]
    },
    {
        "brand": "سيامكو / شام", "category_id": 1199, "category_name": "سيامكو / شام",
        "aliases": ["شام", "سيامكو", "siamco", "sham"],
        "models": [
            ("شام", ["شام", "سيامكو", "siamco", "sham"])
        ]
    },
    {
        "brand": "دايو", "category_id": 1205, "category_name": "دايو",
        "aliases": ["دايو", "daewoo"],
        "models": [
            ("لانوس", ["لانوس", "lanos"]),
            ("نوبيرا", ["نوبيرا", "nubira"]),
            ("ماتيز", ["ماتيز", "matiz"]),
            ("لاكيتي", ["لاكيتي", "lacetti", "لاسيتي"])
        ]
    },
    {
        "brand": "سوزوكي", "category_id": 1212, "category_name": "سوزوكي",
        "aliases": ["سوزوكي", "suzuki"],
        "models": [
            ("سويفت", ["سويفت", "swift"]),
            ("ألتو", ["التو", "ألتو", "alto"]),
            ("ماروتي", ["ماروتي", "maruti"]),
            ("فيتارا", ["فيتارا", "vitara"])
        ]
    },
    {
        "brand": "رينو", "category_id": 1259, "category_name": "رينو",
        "aliases": ["رينو", "renault"],
        "models": [
            ("ميجان", ["ميجان", "megane"]),
            ("كليو", ["كليو", "clio"]),
            ("سيمبول", ["سيمبول", "symbol"]),
            ("لوغان", ["لوغان", "logan"]),
            ("داستر", ["داستر", "duster"])
        ]
    },
    {
        "brand": "سكودا", "category_id": 1343, "category_name": "سكودا",
        "aliases": ["سكودا", "skoda"],
        "models": [
            ("أوكتافيا", ["اوكتافيا", "أوكتافيا", "octavia"]),
            ("فابيا", ["فابيا", "fabia"]),
            ("سوبرب", ["سوبرب", "superb"])
        ]
    },
    {
        "brand": "فيات", "category_id": 1349, "category_name": "فيات",
        "aliases": ["فيات", "fiat"],
        "models": [
            ("بونتو", ["بونتو", "punto"]),
            ("تيبو", ["تيبو", "tipo"]),
            ("سيينا", ["سيينا", "siena"])
        ]
    },
    {
        "brand": "أودي", "category_id": 1336, "category_name": "أودي",
        "aliases": ["أودي", "اودي", "audi"],
        "models": [
            ("a4", ["a4"]),
            ("a6", ["a6"]),
            ("q7", ["q7"]),
            ("q5", ["q5"])
        ]
    },
    {
        "brand": "هوندا", "category_id": 1318, "category_name": "هوندا",
        "aliases": ["هوندا", "honda"],
        "models": [
            ("سيفيك", ["سيفيك", "civic"]),
            ("أكورد", ["اكورد", "أكورد", "accord"]),
            ("cr-v", ["cr-v", "crv"])
        ]
    },
    {
        "brand": "داسيا", "category_id": 1143, "category_name": "داسيا",
        "aliases": ["داسيا", "dacia"],
        "models": [
            ("دبل كبين", ["دبل كبين", "بيك اب", "دبل كابين"]),
            ("داستر", ["داستر", "duster"]),
            ("لوغان", ["لوغان", "logan"])
        ]
    },
    {
        "brand": "بي واي دي", "category_id": 1143, "category_name": "بي واي دي",
        "aliases": ["بي واي دي", "byd"],
        "models": [
            ("f3", ["f3"]),
            ("f0", ["f0"])
        ]
    }
]

# الكلمات الدلالية للسيارات والمركبات في اللهجة السورية
SYRIAN_AUTO_TERMS = [
    "ماتور", "موتور", "محرك", "دوزان", "براوة", "شمعات", "شاسي", "شاصي", "فراغة", "فراغ",
    "نمرة جديدة", "نمرة سورية", "زنار", "فتلات", "برمات", "فخدات", "دواليب", "قصة",
    "غيار عادي", "اوتوماتيك", "تومتيك", "خالية جوا", "خالية برا", "خالية تماما", "خالية العلام",
    "جنط", "جنوط", "غرفة نظيفة", "بخ زنار", "كرت ال", "كرت 20", "فان ركاب", "صهريج", "بيك اب"
]

# الفئات الأخرى (عقارات، طاقة، إلكترونيات، دراجات، مفروشات)
OTHER_CATEGORIES = [
    {"name": "سيارات للإيجار", "id": 1395, "parent": "السيارات", "keywords": ["للإيجار", "للايجار", "إيجار سيارات", "تاجير سيارات"]},
    {"name": "قطع غيار وإكسسوارات السيارات", "id": 1369, "parent": "السيارات", "keywords": ["قطع غيار سيارات", "محرك للبيع", "جنط للبيع", "دوزان للبيع", "فرام"]},
    {"name": "شقق", "id": 3131, "parent": "العقارات", "keywords": ["شقة للبيع", "شقه للبيع", "شقة طابق", "شقه طابق", "غرفتين وصالون", "3 غرف وصالون", "غرف وصالون", "وصالون", "طابو أخضر", "طابو اسهم", "فروغ"]},
    {"name": "فلل وبيوت", "id": 3132, "parent": "العقارات", "keywords": ["فيلا للبيع", "فيلة للبيع", "بيت عربي للبيع", "منزل مستقل للبيع", "بيت للبيع", "منزل للبيع"]},
    {"name": "أراضي ومزارع", "id": 3133, "parent": "العقارات", "keywords": ["أرض للبيع", "ارض للبيع", "مزرعة للبيع", "مزرعه للبيع", "دونم للبيع", "مشجر للبيع"]},
    {"name": "محلات وعقارات تجارية", "id": 3134, "parent": "العقارات", "keywords": ["محل للبيع", "مستودع للبيع", "مكتب تجاري للبيع", "صالة تجارية للبيع"]},
    {"name": "شاليهات واستراحات", "id": 3135, "parent": "العقارات", "keywords": ["شاليه للبيع", "شاليهات للبيع", "استراحة للبيع"]},
    {"name": "جوالات وهواتف ذكية", "id": 3139, "parent": "الإلكترونيات", "keywords": ["ايفون", "آيفون", "iphone", "سامسونج", "samsung", "شاومي", "xiaomi", "ريدمي", "redmi", "جوال للبيع", "موبايل للبيع"]},
    {"name": "كمبيوتر ولابتوب", "id": 3141, "parent": "الإلكترونيات", "keywords": ["لابتوب", "كمبيوتر", "بي سي", "pc", "core i"]},
    {"name": "أجهزة لوحية وآيباد", "id": 3140, "parent": "الإلكترونيات", "keywords": ["آيباد", "ايباد", "ipad", "تابلت"]},
    {"name": "شاشات وتلفزيونات", "id": 3143, "parent": "الإلكترونيات", "keywords": ["شاشة تلفزيون", "سمارت tv", "شاشة 55", "شاشة 43"]},
    {"name": "ألواح ومنظومات طاقة شمسية", "id": 3136, "parent": "الطاقة والكهرباء", "keywords": ["طاقة شمسية", "لوح طاقة", "الواح شمسية"]},
    {"name": "إنفيرترات وبطاريات", "id": 3137, "parent": "الطاقة والكهرباء", "keywords": ["إنفيرتر", "انفرتر", "بطارية ليثيوم", "بطاريات جل"]},
    {"name": "مولدات ومستلزمات كهرباء", "id": 3138, "parent": "الطاقة والكهرباء", "keywords": ["مولدة كهرباء", "مولد ديزل"]},
    {"name": "دراجات نارية (ميتورات)", "id": 3091, "parent": "الدراجات", "keywords": ["ميتور", "دراجة نارية", "سوزوكي 100", "بارت", "سيدو"]},
    {"name": "دراجات هوائية (بسكليتات)", "id": 3117, "parent": "الدراجات", "keywords": ["بسكليت", "بسكليتة", "دراجة هوائية"]},
    {"name": "أثاث وغرف منزلية", "id": 3148, "parent": "المنزل والمفروشات", "keywords": ["غرفة نوم", "طقم كنبايات", "طاولة سفرة"]},
    {"name": "أجهزة كهربائية ومنزلية", "id": 3149, "parent": "المنزل والمفروشات", "keywords": ["براد للبيع", "غسالة للبيع", "فرن غاز للبيع"]}
]

def clean_raw_text(text: str) -> str:
    """تنظيف النص من شوائب الفيسبوك والرموز المزعجة والروابط مع الحفاظ على الكلمات الدلالية"""
    if not text:
        return ""
    t = text
    # إزالة الروابط
    t = re.sub(r'https?://\S+', '', t)
    # إزالة الهاشتاغات وتحويلها لكلمات عادية
    t = re.sub(r'#([^\s#]+)', r'\1', t)
    # إزالة علامات الأندر سكور المتكررة
    t = re.sub(r'[_]{2,}', ' ', t)
    t = t.replace('_', ' ')
    # إزالة عبارات تسويق الفيسبوك الشائعة
    junk_patterns = [
        r'للتواصل\s+اضغط\s+الرابط.*',
        r'للمزيد\s+انضم\s+للمجموعة.*',
        r'علق\s+بنقطة\s+ليصلك\s+السعر.*',
        r'لايك\s+ومتابعة.*',
        r'نقطة\s+منك\s+و\s*السعر\s+عندك.*',
        r'\(?\s*نقطة\s+للمنشور\s+بيوصلك\s+السعر\s*\)?.*',
        r'ضع\s+لايك\s+و\s*نقطة.*',
        r'بسم\s+الله\s+توكلنا\s+على\s+الله.*',
        r'بسم\s+الله\s+الرحمن\s+الرحيم.*',
        r'عشاق\s+الوحش\s+الكوري.*',
        r'لسا\s+ما\s+كرجت.*',
        r'من\s+أجمل\s+ما\s+أنتجت.*',
        r'إذا\s+كنت\s+تبحث\s+عن.*'
    ]
    for p in junk_patterns:
        t = re.sub(p, '', t, flags=re.IGNORECASE)
    # تنظيف الفراغات المتعددة
    t = re.sub(r'[ \t]+', ' ', t)
    return t.strip()

def detect_car_info(text: str) -> Dict[str, Any]:
    """استخراج ماركة وطراز وسنة ومواصفات السيارة بدقة استثنائية مع حتمية التصنيف في أصغر فئة فرعية (Leaf)"""
    t_clean = clean_raw_text(text).lower()
    arabic_to_western = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
    t_digits = t_clean.translate(arabic_to_western)

    info = {
        "brand": None,
        "model": None,
        "year": None,
        "category_id": 1832,
        "category_name": "ماركات أخرى",
        "parent_name": "سيارات للبيع",
        "category_hierarchy": "السيارات > سيارات للبيع > ماركات أخرى"
    }

    # 1. فحص سيارة "قصة" السورية (مثل قصة 98، قصة 97، إلخ) - تصنف حصراً تحت ماركات أخرى 1832
    story_m = re.search(r'\bقصة\s*(9\d|199\d|20[0-2]\d|\d{2})\b', t_digits)
    if story_m:
        raw_yr = story_m.group(1)
        yr_val = ("19" + raw_yr) if len(raw_yr) == 2 and raw_yr.startswith("9") else (raw_yr if len(raw_yr) == 4 else ("20" + raw_yr))
        info["brand"] = "سيارة قصة"
        info["model"] = "قصة"
        info["year"] = yr_val
        info["category_id"] = 1832
        info["category_name"] = "ماركات أخرى"
        info["parent_name"] = "سيارات للبيع"
        info["category_hierarchy"] = build_category_hierarchy(1832)
        return info

    # 2. فحص مطابقة ماركات السيارات الـ 30 في قاعدة البيانات وموديلاتها الفرعية
    matched_bid = None
    for bid, aliases in BRAND_ALIASES.items():
        for a in aliases:
            if re.search(rf'(?:^|\W){re.escape(a)}(?:$|\W)', t_clean):
                matched_bid = bid
                break
        if matched_bid:
            break

    if matched_bid:
        bdata = BRAND_LEAF_MAPPING.get(str(matched_bid), {})
        brand_name = bdata.get("name") or get_category_name_by_id(matched_bid)
        info["brand"] = brand_name
        info["parent_name"] = brand_name

        matched_model_id = None
        matched_model_name = None

        models = bdata.get("models", [])
        for m in models:
            mid = m["id"]
            # فحص الأسماء المستعارة الإضافية الشائعة
            if mid in EXTRA_MODEL_ALIASES:
                for ex in EXTRA_MODEL_ALIASES[mid]:
                    if re.search(rf'(?:^|\W){re.escape(ex)}(?:$|\W)', t_clean):
                        matched_model_id = mid
                        matched_model_name = m["name"]
                        break
            if matched_model_id:
                break

            # فحص الكلمات المفتاحية لاسم الموديل وسلاغه
            mname = m["name"].lower()
            tokens = [tok.strip() for tok in mname.replace('/', ' ').replace('(', ' ').replace(')', ' ').split() if len(tok.strip()) > 2]
            for tok in tokens:
                if tok in ['الفئة', 'جيبات', 'موديل', 'سيري', 'الكلاسيكية']:
                    continue
                if re.search(rf'(?:^|\W){re.escape(tok)}(?:$|\W)', t_clean):
                    matched_model_id = mid
                    matched_model_name = m["name"]
                    break
            if matched_model_id:
                break

        if matched_model_id:
            info["category_id"] = matched_model_id
            info["category_name"] = matched_model_name
            info["model"] = matched_model_name
        else:
            # موديلات أخرى خاصة بتلك الماركة (Leaf)
            fallback_id = bdata.get("other_id") or 1832
            info["category_id"] = fallback_id
            info["category_name"] = get_category_name_by_id(fallback_id)
            info["model"] = None

        info["category_hierarchy"] = build_category_hierarchy(info["category_id"])

    # 3. فحص مصطلحات المركبات السورية في حال عدم ذكر الماركة صراحة (ماتور، دوزان، شمعات، فراغة، إلخ)
    auto_matches = sum(1 for term in SYRIAN_AUTO_TERMS if term in t_clean)
    if auto_matches >= 2:
        if not info["brand"]:
            info["brand"] = "سيارة للبيع"
            info["category_id"] = 1832
            info["category_name"] = "ماركات أخرى"
            info["parent_name"] = "سيارات للبيع"
            info["category_hierarchy"] = build_category_hierarchy(1832)

    # 4. فحص سنة الصنع (موديل YYYY أو سنة YYYY أو كرت YYYY أو 98)
    year_match = re.search(r'(?:موديل|سنة|عام|صنع|كرت|سيري)?\s*(20[0-2]\d|199\d)\b', t_digits)
    if year_match:
        info["year"] = year_match.group(1)
    elif not info["year"]:
        yr_short = re.search(r'\b(9\d)\b', t_digits)
        if yr_short and info["brand"]:
            info["year"] = "19" + yr_short.group(1)

    return info

def detect_smart_category(text: str) -> Dict[str, Any]:
    """تصنيف الإعلان بأعلى دقة في أصغر فئة فرعية ممكنة وفق شجرة تصنيفات Lelbai مع ضمان Leaf 100%"""
    t_clean = clean_raw_text(text).lower()

    # 1. فحص الدراجات النارية والهوائية (لتجنب الخلط بين ميتور سوزوكي وسيارات سوزوكي)
    if any(k in t_clean for k in ["دراجة نارية", "دراجة", "ميتور", "ماطور", "بسكليت", "بسكليتة", "دراجة هوائية"]):
        if any(k in t_clean for k in ["بسكليت", "بسكليتة", "دراجة هوائية"]):
            cid = 3117
        elif any(k in t_clean for k in ["قطع ميتور", "قطع دراجة"]):
            cid = 3124
        else:
            cid = 3091
        return {
            "category_id": cid,
            "category_name": get_category_name_by_id(cid),
            "parent_name": "الدراجات النارية",
            "category_hierarchy": build_category_hierarchy(cid),
            "is_leaf": True
        }

    # 2. سيارات للإيجار (Leaf مباشرة تحت السيارات 1)
    if any(k in t_clean for k in ["للإيجار", "للايجار", "تأجير", "تاجير", "أجار"]) and any(k in t_clean for k in ["سيارة", "سياره", "سياحي"]):
        cid = 1395
        return {
            "category_id": cid,
            "category_name": get_category_name_by_id(cid),
            "parent_name": "السيارات",
            "category_hierarchy": build_category_hierarchy(cid),
            "is_leaf": True
        }

    # 2. قطع غيار وإكسسوارات السيارات (Leaf مباشرة تحت السيارات 1)
    if any(k in t_clean for k in ["قطع غيار", "محرك للبيع", "دوزان للبيع", "جنط للبيع", "فرام للبيع"]):
        cid = 1369
        return {
            "category_id": cid,
            "category_name": get_category_name_by_id(cid),
            "parent_name": "السيارات",
            "category_hierarchy": build_category_hierarchy(cid),
            "is_leaf": True
        }

    # 3. فحص سيارات للبيع (أدق تصنيف في الموديل أو ماركات أخرى 1832)
    car_info = detect_car_info(text)
    if car_info["brand"]:
        leaf_cid = ensure_leaf_category_id(car_info["category_id"])
        return {
            "category_id": leaf_cid,
            "category_name": car_info["category_name"],
            "parent_name": car_info.get("parent_name") or "سيارات للبيع",
            "category_hierarchy": build_category_hierarchy(leaf_cid),
            "is_leaf": True
        }

    # 4. باقي الأقسام التخصصية (عقارات، طاقة، إلكترونيات، دراجات، مفروشات)
    for cat in OTHER_CATEGORIES:
        for kw in cat["keywords"]:
            if re.search(rf'(?:^|\W){re.escape(kw)}(?:$|\W)', t_clean):
                leaf_cid = ensure_leaf_category_id(cat["id"])
                return {
                    "category_id": leaf_cid,
                    "category_name": get_category_name_by_id(leaf_cid),
                    "parent_name": cat.get("parent", "عام"),
                    "category_hierarchy": build_category_hierarchy(leaf_cid),
                    "is_leaf": True
                }

    # 5. مصطلحات عامة للسيارات في حال عدم تمييزها مسبقاً
    if any(k in t_clean for k in ["سيارة", "سياره", "غيار عادي", "اوتوماتيك", "خالية تماما", "خالية جوا", "شمعات", "دوزان", "ماتور"]):
        cid = 1832  # ماركات أخرى (Leaf مباشرة تحت سيارات للبيع 1143)
        return {
            "category_id": cid,
            "category_name": "ماركات أخرى",
            "parent_name": "سيارات للبيع",
            "category_hierarchy": build_category_hierarchy(cid),
            "is_leaf": True
        }

    # 6. القسم العام الافتراضي (أصناف عامة ومتنوعة 3207 - Leaf بدلاً من أخرى 259)
    cid = 3207
    return {
        "category_id": cid,
        "category_name": get_category_name_by_id(cid),
        "parent_name": "أخرى",
        "category_hierarchy": build_category_hierarchy(cid),
        "is_leaf": True
    }

def extract_smart_price(text: str) -> Optional[Tuple[str, str]]:
    """استخراج السعر والعملة بذكاء من نص الإعلان (دولار أو ليرة سورية)"""
    t_clean = clean_raw_text(text)
    arabic_to_western = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
    t_digits = t_clean.translate(arabic_to_western)

    p_match = re.search(r'(?:السعر|سعر|بـ|ب)\s*[:\-]?\s*(\d{3,8})\s*(?:وبازار|بازار|دولار|\$|الف|ألف|مليون)?', t_digits)
    if p_match:
        val_str = p_match.group(1)
        val = int(val_str)
        currency = "USD" if val <= 50000 else "SYP"
        return str(val), currency
    return None

def generate_smart_title(text: str, ad: Dict[str, Any]) -> str:
    """
    توليد عنوان تجاري جذاب ومتناسق (40 - 75 حرفاً)
    خالٍ تماماً من عبارات الفيسبوك العشوائية أو تقطيع الجمل.
    """
    t_clean = clean_raw_text(text)
    city = ad.get("city_name") or ad.get("location_detected") or ""
    if "(" in city:
        city = city.split("(")[0].strip()

    # 1. سياق سيارات "قصة"
    if "قصة" in t_clean:
        car = detect_car_info(t_clean)
        yr = car.get("year") or "1998"
        loc = f"- {city}" if city else ""
        return f"سيارة قصة موديل {yr} نمرة جديدة فراغة فوراً {loc}".strip()

    # 2. سياق السيارات العامة
    car = detect_car_info(t_clean)
    if car.get("brand") or car.get("model"):
        brand_str = car.get("brand") or ""
        model_str = car.get("model") or ""
        year_str = f"موديل {car.get('year')}" if car.get("year") else ""
        
        # استخراج الحالة الفنية الأبرز
        condition_str = ""
        if any(k in t_clean for k in ["كسر زيرو", "كسر الزيرو", "زيرو 0 كم", "زيرووو"]):
            condition_str = "كسر زيرو"
        elif any(k in t_clean for k in ["خالية تماما", "خالية من الداخل والخارج", "خالية تماماً"]):
            condition_str = "خالية تماماً"
        elif any(k in t_clean for k in ["خالية جوا", "خالية من الداخل"]):
            condition_str = "خالية من الداخل"
        elif any(k in t_clean for k in ["بحالة الوكالة", "وكالة"]):
            condition_str = "بحالة الوكالة"
        elif any(k in t_clean for k in ["بحالة ممتازة", "ممتازة"]):
            condition_str = "بحالة ممتازة"

        # استخراج ميزة إضافية بارزة
        feature_str = ""
        if "بانوراما" in t_clean:
            feature_str = "بانوراما"
        elif "فتحة سقف" in t_clean:
            feature_str = "فتحة سقف"
        elif "ديزل" in t_clean:
            feature_str = "ديزل"
        elif "أوتوماتيك" in t_clean or "اوتوماتيك" in t_clean:
            feature_str = "أوتوماتيك"
        elif "غيار عادي" in t_clean:
            feature_str = "غيار عادي"
        elif "نمرة جديدة" in t_clean:
            feature_str = "نمرة جديدة"

        parts = [brand_str]
        if model_str and model_str not in brand_str and model_str != "سيارة":
            parts.append(model_str)
        if year_str:
            parts.append(year_str)
        if feature_str:
            parts.append(feature_str)
        if condition_str:
            parts.append(condition_str)
        if city:
            parts.append(f"- {city}")

        title_res = " ".join([p for p in parts if p]).strip()
        if len(title_res) >= 15:
            return title_res[:80].strip()

    # 3. سياق العقارات
    if any(k in t_clean for k in ["شقة", "شقه", "بيت", "منزل", "فيلا", "عقار", "مزرعة"]):
        rooms_m = re.search(r'(\d+)\s*(?:غرف|غرفة|وصالون)', t_clean)
        rooms_str = f"{rooms_m.group(0)}" if rooms_m else ""
        type_str = "فيلا للبيع" if "فيلا" in t_clean else ("مزرعة للبيع" if "مزرع" in t_clean else ("منزل مستقل" if "بيت" in t_clean else "شقة للبيع"))
        spec_str = "إكساء سوبر ديلوكس" if ("ديلوكس" in t_clean or "سوبر" in t_clean) else "بحالة ممتازة"
        loc_str = f"في {city}" if city else ""
        
        parts = [type_str, rooms_str, spec_str, loc_str]
        title_res = " ".join([p for p in parts if p]).strip()
        if len(title_res) >= 15:
            return title_res[:80].strip()

    # 4. سياق الإلكترونيات
    phone_m = re.search(r'(آيفون|ايفون|iphone|سامسونج|samsung|شاومي|redmi)\s*([a-zA-Z0-9\s+]+?)(?=\s*(?:نظافة|بحالة|غيغابايت|gb|للبيع|$))', t_clean, re.IGNORECASE)
    if phone_m:
        dev_name = f"{phone_m.group(1)} {phone_m.group(2)}".strip()
        cond_str = "بحالة الوكالة" if "وكالة" in t_clean else "نظيف جداً"
        title_res = f"{dev_name} {cond_str} {('- ' + city) if city else ''}".strip()
        return title_res[:80].strip()

    # 5. معالجة ذكية عامة
    lines = [l.strip() for l in t_clean.split("\n") if len(l.strip()) > 6]
    valid_lines = []
    for l in lines:
        if any(j in l for j in ["نقطة", "علق", "السعر", "للتواصل", "رابط", "لايك", "واتساب", "السلام"]):
            continue
        valid_lines.append(l)

    if valid_lines:
        base_title = valid_lines[0]
        base_title = re.sub(r'^(للبيع|مطلوب|عرض خاص|إعلان)\s*[:\-]?\s*', '', base_title)
        if city and city not in base_title:
            base_title = f"{base_title} - {city}"
        return base_title[:80].strip()

    return f"إعلان مميز للبيع بحالة ممتازة {('- ' + city) if city else ''}".strip()

def generate_smart_description(raw_desc: str, ad: Dict[str, Any]) -> str:
    """
    توليد وصف مهيكل ومنسق باحترافية تسويقية فائقة (أقسام، نقاط، إيموجي)
    يبرز المواصفات، الحالة الفنية، الكماليات، ومعلومات التواصل الواضحة حتى لو كُتب الإعلان في سطر واحد.
    """
    t_clean = clean_raw_text(raw_desc)
    specs = ad.get("specifications") or {}
    phone = ad.get("phone_number") or ""
    city = ad.get("city_name") or ad.get("location_detected") or ""

    # فصل قسم التواصل عن صلب الإعلان لتجنب حذف بيانات الإعلان
    contact_m = re.search(r'(?:للتواصل|للاتصال|واتس|واتساب|اتصال|رقم|تواصل)\s*[:\-]?\s*.*$', t_clean, re.DOTALL | re.IGNORECASE)
    if contact_m:
        body_text = t_clean[:contact_m.start()].strip()
    else:
        body_text = t_clean

    # تقسيم الإعلان إلى نقاط ذكية سواء كان مقسماً بأسطر أو بكلمات مفتاحية أو نقاط
    split_pattern = r'(?=\b(?:نمرة جديدة|فراغة|شمعات|دوزان|ماتور|موتور|محرك|غرفة|دواليب|السعر|بخ|خالية|جنط|فرش|بطاريات|خزان)\b)|[\r\n]+|\.{2,}|…+|،|,|\s*-\s*|\s{2,}'
    raw_tokens = [t.strip() for t in re.split(split_pattern, body_text) if t and len(t.strip()) > 2]

    bullets = []
    notes = []
    for tok in raw_tokens:
        if any(w in tok for w in ["السلام", "توكلنا", "نقطة", "علق", "لايك"]):
            continue
        if any(w in tok for w in ["خالية", "بخ", "محرك", "ماتور", "دوزان", "سنة", "موديل", "شمعات", "شاسي", "فراغة", "نمرة", "دواليب", "زنار"]):
            bullets.append(f"• {tok}")
        else:
            notes.append(f"• {tok}")

    out_sections = []
    
    # 1. رأس المواصفات الفنية المهيكلة
    out_sections.append("📋 التفاصيل والمواصفات الفنية:")
    if specs.get("make"): out_sections.append(f"• الماركة: {specs['make']}")
    if specs.get("model"): out_sections.append(f"• الطراز: {specs['model']}")
    if specs.get("year"): out_sections.append(f"• سنة الصنع: {specs['year']}")
    if specs.get("transmission"): out_sections.append(f"• ناقل الحركة: {specs['transmission']}")
    if specs.get("fuel_type"): out_sections.append(f"• نوع الوقود: {specs['fuel_type']}")
    if specs.get("condition"): out_sections.append(f"• الحالة الفنية: {specs['condition']}")
    if specs.get("color"): out_sections.append(f"• اللون: {specs['color']}")

    # 2. الحالة الفنية والملاحظات المستخلصة من النص
    if bullets:
        out_sections.append("\n✨ الحالة الفنية والملاحظات الأساسية:")
        out_sections.extend(bullets[:8])

    # 3. ميزات إضافية وتجهيزات
    if notes and len(notes) > 0:
        out_sections.append("\n⭐ ميزات إضافية وتجهيزات:")
        out_sections.extend(notes[:6])

    # 4. المعاينة والتواصل
    out_sections.append("\n📍 معلومات المعاينة والتواصل:")
    if city:
        out_sections.append(f"• التواجد والمعاينة: {city}")
    
    price_info = ad.get("price_info", {})
    if price_info.get("amount"):
        curr_str = "$" if price_info.get("currency") == "USD" else (price_info.get("currency") or "ل.س")
        out_sections.append(f"• السعر المطلوب: {price_info['amount']} {curr_str} (وبازار)")
    else:
        out_sections.append("• السعر: قابل للتفاوض المناسب عند الجدية")
    if phone:
        out_sections.append(f"• هاتف التواصل والاستفسار: {phone}")

    final_desc = "\n".join(out_sections).strip()
    return final_desc if len(final_desc) >= 30 else raw_desc

def enhance_ad_with_super_ai(ad: Dict[str, Any]) -> Dict[str, Any]:
    """
    الواجهة المركزية الشاملة لتعزيز الإعلان بالذكاء الاصطناعي الفائق:
    1. تحسين العنوان لعنوان تجاري نخبوي.
    2. تحسين وتنسيق الوصف لهيكل احترافي بالأقسام والنقاط.
    3. تصنيف فائق الدقة في أصغر فئة (Deep Leaf Category).
    4. استخراج المواصفات والأسعار والاسم المستقل.
    """
    ad_copy = ad.copy()
    raw_desc = ad_copy.get("description") or ad_copy.get("clean_description") or ""

    # 1. استخراج السعر بذكاء إن لم يكن موجوداً
    if not ad_copy.get("price_info") or not ad_copy["price_info"].get("amount"):
        extracted_price = extract_smart_price(raw_desc)
        if extracted_price:
            ad_copy["price_info"] = {
                "amount": extracted_price[0],
                "currency": extracted_price[1],
                "is_negotiable": True
            }

    # 2. التصنيف في أصغر فئة
    cat_info = detect_smart_category(raw_desc)
    ad_copy["leaf_category_id"] = cat_info["category_id"]
    ad_copy["leaf_category_name"] = cat_info["category_name"]
    ad_copy["category_hierarchy"] = cat_info.get("category_hierarchy") or f"{cat_info['parent_name']} > {cat_info['category_name']}"
    ad_copy["category"] = cat_info["category_name"]

    # 3. استخراج مواصفات السيارة إن وجدت
    car_info = detect_car_info(raw_desc)
    specs = dict(ad_copy.get("specifications") or {})
    if car_info.get("brand") and not specs.get("make"):
        specs["make"] = car_info["brand"]
    if car_info.get("model") and not specs.get("model"):
        specs["model"] = car_info["model"]
    if car_info.get("year") and not specs.get("year"):
        specs["year"] = car_info["year"]
    ad_copy["specifications"] = specs

    # 4. توليد العنوان الاحترافي
    smart_title = generate_smart_title(raw_desc, ad_copy)
    ad_copy["clean_title"] = smart_title

    # 5. توليد الوصف المهيكل
    smart_desc = generate_smart_description(raw_desc, ad_copy)
    ad_copy["clean_description"] = smart_desc

    return ad_copy
