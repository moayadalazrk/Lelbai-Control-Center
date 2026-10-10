# -*- coding: utf-8 -*-
"""
اختبارات التحقق من دقة فلترة الإعلانات السورية واستخراج الأرقام وتطبيق الشروط الإجبارية:
1. شرط وجود رقم هاتف سوري
2. شرط تحديد المدينة الرئيسية
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from syria_filter import extract_syrian_phone_numbers, classify_location, validate_ad

def run_tests():
    print("=== بدء اختبارات وحدة الفلترة وتطبيق الشروط الإجبارية ===")
    
    test_cases = [
        {
            "name": "إعلان شقة في دمشق برقم محلي عادي (صالح: يحتوي رقم + مدينة)",
            "text": "للإيجار شقة في دمشق - المزة فيلات غربية، سوبر ديلوكس. للتواصل: 0933123456",
            "expected_valid": True,
            "expected_phone": "0933123456",
            "expected_city_id": 1
        },
        {
            "name": "إعلان سيارة في حلب برقم مكتوب بأرقام مشرقية (صالح: يحتوي رقم + مدينة)",
            "text": "كيا سيراتو للبيع في حلب الشهباء، السعر 150 مليون ل.س. للاستفسار اتصال أو واتس ٠٩٤٤٥٥٦٦٧٧",
            "expected_valid": True,
            "expected_phone": "0944556677",
            "expected_city_id": 3
        },
        {
            "name": "إعلان في حمص برقم دولي +963 (صالح: يحتوي رقم + مدينة)",
            "text": "مطلوب موظفين لشركة في حمص حي الإنشاءات. رقم التواصل: +963 955 667 788",
            "expected_valid": True,
            "expected_phone": "0955667788",
            "expected_city_id": 6
        },
        {
            "name": "إعلان في ريف دمشق برقم فيه شرطات (صالح: يحتوي رقم + مدينة)",
            "text": "أرض للبيع في ريف دمشق - صحنايا طابو أخضر. هاتف: 0988-112-233",
            "expected_valid": True,
            "expected_phone": "0988112233",
            "expected_city_id": 2
        },
        {
            "name": "إعلان برقم سوري ولكن بدون أي ذكر لمدينة ولا سياق (يجب سكبه وتجاهله)",
            "text": "للبيع شاحنة بحالة ممتازة للتواصل اتصال 0933112233",
            "expected_valid": False,
            "expected_phone": "0933112233",
            "expected_city_id": None
        },
        {
            "name": "إعلان في سوريا بدون رقم هاتف (يجب سكبه لأنه يفتقد للرقم)",
            "text": "فرصة عمل في اللاذقية براتب مغري، التواصل خاص فقط!",
            "expected_valid": False,
            "expected_phone": None,
            "expected_city_id": 8
        },
        {
            "name": "إعلان في السعودية برقم سعودي (غير صالح لأنه خارج سوريا)",
            "text": "سيارة تويوتا كامري للبيع في الرياض، التواصل على الرقم: 0501234567",
            "expected_valid": False,
            "expected_phone": None,
            "expected_city_id": None
        },
        {
            "name": "إعلان بحلب بحرف الجر المتصل (بحلب)",
            "text": "هيونداي فيرنا للبيع بحلب جاهزية عالية للتواصل 0944123456",
            "expected_valid": True,
            "expected_phone": "0944123456",
            "expected_city_id": 3
        },
        {
            "name": "إعلان بريف دمشق بحرف الجر (بريف دمشق) - يجب أن يكون ريف دمشق وليس دمشق",
            "text": "مزرعة للبيع بريف دمشق طابو نظامي 0988112233",
            "expected_valid": True,
            "expected_phone": "0988112233",
            "expected_city_id": 2
        },
        {
            "name": "إعلان بريف حلب بحرف الجر (بريف حلب) - يجب أن يكون ريف حلب وليس حلب",
            "text": "سيارة للبيع بريف حلب فراغة فورية 0966112233",
            "expected_valid": True,
            "expected_phone": "0966112233",
            "expected_city_id": 4
        },
        {
            "name": "إعلان يحتوي عبارة شاملة وورقة دون ذكر مدينة - يجب عدم مطابقته بالخطأ مع دمشق أو الرقة",
            "text": "سيارة ممتازة شاملة الفحص الفني ومعها ورقة طابو نظامي للتواصل 0933112233",
            "expected_valid": False,
            "expected_phone": "0933112233",
            "expected_city_id": None
        },
        {
            "name": "إعلان يحتوي لوحة دمشق لكن التواجد حلب - يجب اعتماد حلب لأنها مكان المعاينة الفعلي",
            "text": "كيا ريو 2011 نمرة دمشق تواجد حلب السعر 8200$ اتصال 0944998877",
            "expected_valid": True,
            "expected_phone": "0944998877",
            "expected_city_id": 3
        }
    ]
    
    passed_count = 0
    for i, tc in enumerate(test_cases, 1):
        result = validate_ad(tc["text"])
        is_valid_match = (result["is_valid"] == tc["expected_valid"])
        city_match = (result["id-citie"] == tc["expected_city_id"])
        
        if is_valid_match and city_match:
            print(f"[SUCCESS] اختبار {i}: {tc['name']} - نجح!")
            print(f"    is_valid={result['is_valid']}, id-citie={result['id-citie']}, phones={result['phones']}")
            passed_count += 1
        else:
            print(f"[FAIL] اختبار {i}: {tc['name']} - فشل!")
            print(f"   النتيجة المتوقعة: valid={tc['expected_valid']}, city_id={tc['expected_city_id']}")
            print(f"   النتيجة الفعلية: valid={result['is_valid']}, id-citie={result['id-citie']}, phones={result['phones']}")
            
    print(f"\nالنتيجة النهائية: {passed_count}/{len(test_cases)} اختبارات ناجحة.")
    assert passed_count == len(test_cases), "هناك اختبارات لم تنجح!"

if __name__ == "__main__":
    run_tests()
