# -*- coding: utf-8 -*-
import sys
import json
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from ai_ad_enhancer import enhance_ad_with_super_ai, extract_smart_price, detect_car_info
from category_classifier import extract_detailed_specifications
from syria_filter import classify_location

def test_cars():
    test_cases = [
        {
            "name": "Mercedes E350 4matic Damascus",
            "text": """#للبيع_في_دمشق\nE350 4matic 2013\nأكمل وصف فتحة سقف\nخالية برا جوا عدا قطعتين\nوارد عمان\nماشية ٣٣٠ الف\nجاهزية عالية\nنقطة ليصلك السعر\nللتواصل ٠٩٤٤٥٥٠٥٣٩""",
            "expected_brand": "مرسيدس-بنز",
            "expected_cat_id": 1227,
            "expected_price": None,
            "expected_city_id": 1
        },
        {
            "name": "Hyundai Tucson Aleppo",
            "text": """توسان 2019 فتحة سقف وبانوراما\nبحالة الوكالة خالية تماما\nالموقع حلب الشهباء\nالسعر 14500 دولار\n0933112233""",
            "expected_brand": "هيونداي",
            "expected_cat_id": 1148,
            "expected_price": ("14500", "USD"),
            "expected_city_id": 3
        },
        {
            "name": "Kia Cerato Homs",
            "text": """سيراتو 2011 خالية جوا بخ زنار\nحمص الوعر\nالسعر 6800$\n0955667788""",
            "expected_brand": "كيا",
            "expected_cat_id": 1157,
            "expected_price": ("6800", "USD"),
            "expected_city_id": 6
        },
        {
            "name": "Toyota Camry Tartus",
            "text": """كامري 2015 كرت 2015 وارد خليجي\nطرطوس\nالسعر 160 ورقة وبازار\n0944889900""",
            "expected_brand": "تويوتا",
            "expected_cat_id": 1169,
            "expected_price": ("16000", "USD"),
            "expected_city_id": 12
        }
    ]

    all_passed = True
    for idx, tc in enumerate(test_cases, 1):
        loc = classify_location(tc["text"])
        price = extract_smart_price(tc["text"])
        car = detect_car_info(tc["text"])
        
        c_ok = (loc.get("id-citie") == tc["expected_city_id"])
        p_ok = (price == tc["expected_price"])
        b_ok = (car.get("brand") == tc["expected_brand"])
        cat_ok = (car.get("category_id") == tc["expected_cat_id"])

        if c_ok and p_ok and b_ok and cat_ok:
            print(f"✅ [{idx}] {tc['name']}: نجح بالكامل (المدينة: {loc.get('city_name')}, السعر: {price}, الفئة: {car.get('category_name')} ID: {car.get('category_id')})")
        else:
            print(f"❌ [{idx}] {tc['name']}: فشل! c_ok={c_ok}, p_ok={p_ok}, b_ok={b_ok}, cat_ok={cat_ok}")
            all_passed = False

    return all_passed

if __name__ == "__main__":
    success = test_cars()
    if success:
        print("\n🎉 جميع اختبارات موديلات السيارات والمدن والأسعار نجحت 100%!")
        sys.exit(0)
    else:
        sys.exit(1)
