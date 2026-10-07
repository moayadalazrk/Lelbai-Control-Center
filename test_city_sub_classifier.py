# -*- coding: utf-8 -*-
"""
اختبار دقة تصنيف المدن والمناطق الفرعية وفقاً لملفات CSV:
- id-citie
- id-sub_districts
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from syria_filter import validate_ad, CITIES_BY_ID, SUB_DISTRICTS_BY_ID

def run_classification_tests():
    print("=== اختبار تصنيف المدن والمناطق بالأرقام (IDs) ===")
    print(f"قاعدة البيانات: {len(CITIES_BY_ID)} مدن رئيسية | {len(SUB_DISTRICTS_BY_ID)} منطقة فرعية.\n")

    test_cases = [
        {
            "name": "إعلان في المزة (دمشق)",
            "text": "شقة للإيجار في المزة فيلات غربية للتواصل 0933123456",
            "group": "",
            "expected_city_id": 1,
            "expected_sub_id": 1,
            "expected_sub_name": "المزة"
        },
        {
            "name": "إعلان في كفرسوسة (دمشق)",
            "text": "محل للبيع في كفرسوسة تنظيم هاتف 0944112233",
            "group": "",
            "expected_city_id": 1,
            "expected_sub_id": 2,
            "expected_sub_name": "كفرسوسة"
        },
        {
            "name": "إعلان في صحنايا (ريف دمشق)",
            "text": "بيت للبيع في صحنايا طابو اسهم 0988112233",
            "group": "",
            "expected_city_id": 2,
            "expected_sub_id": 38,
            "expected_sub_name": "صحنايا"
        },
        {
            "name": "إعلان في جرمانا (ريف دمشق)",
            "text": "شقة في جرمانا كشكول للتواصل 0933887766",
            "group": "",
            "expected_city_id": 2,
            "expected_sub_id": 29,
            "expected_sub_name": "جرمانا"
        },
        {
            "name": "إعلان في حلب فقط دون تحديد منطقة فرعية",
            "text": "سيارة كيا سيراتو للبيع في حلب للتواصل 0966554433",
            "group": "",
            "expected_city_id": 3,
            "expected_sub_id": None,
            "expected_sub_name": None
        },
        {
            "name": "إعلان في حي الشهباء بحلب",
            "text": "محل للبيع في حلب حي الشهباء للتواصل 0966554433",
            "group": "",
            "expected_city_id": 3,
            "expected_sub_id": 81,
            "expected_sub_name": "الشهباء"
        },
        {
            "name": "إعلان في حمص فقط دون تحديد منطقة فرعية",
            "text": "مطلوب موظف في حمص للتواصل 0955667788",
            "group": "",
            "expected_city_id": 6,
            "expected_sub_id": None,
            "expected_sub_name": None
        },
        {
            "name": "إعلان في مجموعة سيارات دمشق بدون ذكر المدينة في النص",
            "text": "هوندا اكورد 2011 بحالة الوكالة للتواصل 0933827057",
            "group": "سيارات للبيع في دمشق",
            "expected_city_id": 1,
            "expected_sub_id": None,
            "expected_sub_name": None
        }
    ]

    all_passed = True
    for idx, tc in enumerate(test_cases, 1):
        res = validate_ad(tc["text"], group_context=tc["group"])
        city_match = (res["id-citie"] == tc["expected_city_id"])
        sub_match = (res["id-sub_districts"] == tc["expected_sub_id"])

        if city_match and sub_match:
            print(f"✅ [{idx}] {tc['name']}")
            print(f"    id-citie: {res['id-citie']} ({res['city_name']}) | id-sub_districts: {res['id-sub_districts']} ({res['sub_district_name']})")
        else:
            all_passed = False
            print(f"❌ [{idx}] {tc['name']} - فشل!")
            print(f"    المتوقع: id-citie={tc['expected_city_id']}, id-sub_districts={tc['expected_sub_id']}")
            print(f"    الفعلي:  id-citie={res['id-citie']}, id-sub_districts={res['id-sub_districts']}")
        print("-" * 60)

    if all_passed:
        print("🎉 جميع اختبارات التصنيف بالـ IDs نجحت 100%!")
    else:
        print("❌ هناك اختبارات لم تنجح.")

if __name__ == "__main__":
    run_classification_tests()
