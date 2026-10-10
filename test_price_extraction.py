# -*- coding: utf-8 -*-
"""
اختبارات شاملة لوحدة استخراج وتدقيق أسعار الإعلانات السورية (extract_smart_price):
يختبر كافة العملات (دولار أمريكي وليرة سورية) ومصطلحات السوق الشائعة:
- الملايين والمليارات (150 مليون، 450 م، 2 مليار، مليون ونص، مليونين)
- آلاف الدولارات (12 الف دولار، 8.5 الف $)
- الدولار المباشر (8200$، $8200، 8200 دولار، 8200 أمريكي)
- مصطلح الورقة (82 ورقة = 8200$)
- مصطلحات السكرا والبازار (10500 وسكرا، 8500 وبازار خفيف)
- آلاف الليرات (75 الف، 500000 ليرة)
- عزل أرقام الهواتف والموديلات والمساحات من التداخل
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from ai_ad_enhancer import extract_smart_price, enhance_ad_with_super_ai

def run_price_tests():
    print("=== بدء اختبارات استخراج وتدقيق الأسعار في السوق السوري ===")

    test_cases = [
        {"text": "السعر 150 مليون ل.س وبازار", "expected_amount": "150000000", "expected_currency": "SYP"},
        {"text": "السعر 450 م وبازار خفيف", "expected_amount": "450000000", "expected_currency": "SYP"},
        {"text": "مطلوب 1.5 مليون", "expected_amount": "1500000", "expected_currency": "SYP"},
        {"text": "السعر 2 مليار ليرة سورية", "expected_amount": "2000000000", "expected_currency": "SYP"},
        {"text": "السعر مليون ونص نهائي", "expected_amount": "1500000", "expected_currency": "SYP"},
        {"text": "السعر مليونين وبازار", "expected_amount": "2000000", "expected_currency": "SYP"},
        {"text": "السعر 12 الف دولار للتواصل", "expected_amount": "12000", "expected_currency": "USD"},
        {"text": "مطلوب 12 ألف $ وبازار", "expected_amount": "12000", "expected_currency": "USD"},
        {"text": "مطلوب 8200 دولار كاش", "expected_amount": "8200", "expected_currency": "USD"},
        {"text": "كيا ريو 2011 السعر 8500$", "expected_amount": "8500", "expected_currency": "USD"},
        {"text": "هيونداي 8500 $ وبازار خفيف", "expected_amount": "8500", "expected_currency": "USD"},
        {"text": "فيرنا 2009 جاهزية تامة 10500 وسكرا", "expected_amount": "10500", "expected_currency": "USD"},
        {"text": "10,500 $ وسكرة صغيرة عند المعاينة", "expected_amount": "10500", "expected_currency": "USD"},
        {"text": "السعر 82 ورقة منهي", "expected_amount": "8200", "expected_currency": "USD"},
        {"text": "السعر 75 الف", "expected_amount": "75000", "expected_currency": "SYP"},
        {"text": "السعر 500000 ليرة", "expected_amount": "500000", "expected_currency": "SYP"},
        {"text": "السعر المطلوب 8500 وبازار", "expected_amount": "8500", "expected_currency": "USD"},
        {"text": "كيا ريو 2011 خالية جوة السعر 6800$ هاتف 0933123456", "expected_amount": "6800", "expected_currency": "USD"},
        {"text": "شقة مساحة 150 متر مربع السعر 350 مليون", "expected_amount": "350000000", "expected_currency": "SYP"},
        {"text": "سيارة ماشية 120 ألف كم السعر 7500 دولار", "expected_amount": "7500", "expected_currency": "USD"},
        {"text": "السعر على السوم بعد المعاينة", "expected_amount": None, "expected_currency": None},
        {"text": "للتفاوض بنور الله والبيع عالخاص", "expected_amount": None, "expected_currency": None}
    ]

    passed = 0
    for idx, tc in enumerate(test_cases, 1):
        res = extract_smart_price(tc["text"])
        val = res[0] if res else None
        curr = res[1] if res else None

        val_ok = (val == tc["expected_amount"])
        curr_ok = (curr == tc["expected_currency"])

        if val_ok and curr_ok:
            print(f"✅ [{idx}] نجح: '{tc['text'][:35]}...' => {val} {curr}")
            passed += 1
        else:
            print(f"❌ [{idx}] فشل: '{tc['text']}'")
            print(f"    المتوقع: {tc['expected_amount']} {tc['expected_currency']}")
            print(f"    الفعلي:  {val} {curr}")

    print(f"\nالنتيجة النهائية: {passed}/{len(test_cases)} اختبارات ناجحة.")
    assert passed == len(test_cases), "هناك اختبارات أسعار لم تنجح!"

if __name__ == "__main__":
    run_price_tests()
