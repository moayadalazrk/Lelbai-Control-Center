# -*- coding: utf-8 -*-
"""
اختبار تدفق عمل المتصفح المرئي وسحب الإعلانات وحفظ ملف JSON
يقوم بإنشاء صفحة إعلانات محلية تحاكي مجموعة فيسبوك، وفتح المتصفح وسحب الإعلانات وفحص ملف JSON الناتج.
"""

import os
import sys
import json
import time

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from scraper import SyrianAdScraper

MOCK_HTML_CONTENT = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>مجموعة سوق دمشق وسوريا للإعلانات</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f0f2f5; padding: 20px; }
        .post { background: white; border-radius: 8px; padding: 15px; margin-bottom: 20px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); max-width: 600px; margin-left: auto; margin-right: auto; }
        .post img { max-width: 100%; border-radius: 6px; margin-top: 10px; }
        .more-btn { color: #1877f2; cursor: pointer; font-weight: bold; }
    </style>
</head>
<body>
    <h1>مجموعة إعلانات سوريا المباشرة</h1>
    <div role="feed">
        <!-- إعلان 1: مطابق في دمشق برقم سوري وصورة -->
        <div role="article" class="post">
            <a href="https://facebook.com/groups/syriagroup/posts/1010101">المنشور الأول</a>
            <p>
                شقة مفروشة للإيجار في دمشق حي المزة فيلات غربية، 3 غرف وصالون إكساء سوبر ديلوكس، طابق ثاني مع مصعد وكهرباء 24 ساعة.
                السعر: 3 مليون ل.س شهرياً.
                للتواصل والاستفسار يرجى الاتصال على الرقم: 0933123456
            </p>
            <img src="https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=500" alt="صورة الشقة" />
        </div>

        <!-- إعلان 2: غير مطابق (في السعودية وبرقم سعودي) -> يجب استبعاده -->
        <div role="article" class="post">
            <a href="https://facebook.com/groups/syriagroup/posts/2020202">المنشور الثاني</a>
            <p>
                سيارة هيونداي النترا للبيع في الرياض حي الملز بحالة ممتازة، التواصل واتساب على 0551234567
            </p>
            <img src="https://images.unsplash.com/photo-1549399542-7e3f8b79c341?w=500" alt="صورة السيارة" />
        </div>

        <!-- إعلان 3: مطابق في حلب برقم مكتوب بأرقام عربية/مشرقية وصور -->
        <div role="article" class="post">
            <a href="https://facebook.com/groups/syriagroup/posts/3030303">المنشور الثالث</a>
            <p>
                محل تجاري للبيع في حلب - الفرقان شارع المشفى العمالي مساحة 40 متر جاهز مع سند تمليك.
                للتواصل اتصال أو واتس: ٠٩٤٤٨٨٩٩٠٠
            </p>
            <img src="https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=500" alt="صورة المحل" />
        </div>

        <!-- إعلان 4: في سوريا لكن بدون رقم هاتف -> يجب استبعاده لأنه يفتقد لرقم هاتف -->
        <div role="article" class="post">
            <a href="https://facebook.com/groups/syriagroup/posts/4040404">المنشور الرابع</a>
            <p>
                مطلوب مندوبي مبيعات في حمص حي الإنشاءات برواتب وحوافز ممتازة، للتفاصيل تواصلوا معنا عبر الخاص فقط.
            </p>
        </div>

        <!-- إعلان 5: مطابق في اللاذقية برقم دولي +963 -->
        <div role="article" class="post">
            <a href="https://facebook.com/groups/syriagroup/posts/5050505">المنشور الخامس</a>
            <p>
                مزرعة للإيجار السياحي في اللاذقية - مشقيتا مطلة على البحيرة مع مسبح خاص.
                للحجز والاستفسار: +963 988 223 344
            </p>
            <img src="https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=500" alt="صورة المزرعة" />
        </div>
    </div>
</body>
</html>
"""

def test_scraper_pipeline():
    print("=== اختبار محاكاة السحب الفعلي بالمتصفح المرئي ===")
    
    mock_file = os.path.abspath("mock_group_page.html")
    with open(mock_file, "w", encoding="utf-8") as f:
        f.write(MOCK_HTML_CONTENT)

    mock_url = f"file:///{mock_file.replace(os.sep, '/')}"
    output_json = "test_output_ads.json"
    
    if os.path.exists(output_json):
        os.remove(output_json)

    # تشغيل السكرابر في وضع بدون هيدلس أو هيدلس للاختبار الآلي
    scraper = SyrianAdScraper(user_data_dir="./test_browser_session", headless=True)
    results = scraper.scrape_group(
        group_url=mock_url,
        max_ads=10,
        max_scroll_attempts=2,
        output_file=output_json
    )

    print(f"\n[+] عدد الإعلانات المسحوبة: {len(results)}")
    
    # فحص النتائج
    assert os.path.exists(output_json), "ملف JSON لم يتم إنشاؤه!"
    with open(output_json, "r", encoding="utf-8") as f:
        saved_data = json.load(f)

    print(f"[+] محتوى ملف JSON يحتوي على {len(saved_data)} إعلانات.")
    
    # يجب أن يطابق 3 إعلانات فقط (الإعلان 1، 3، 5)
    # ويستبعد الإعلان 2 (سعودي) والإعلان 4 (بدون رقم)
    assert len(saved_data) == 3, f"المتوقع 3 إعلانات صالحة، الفعلي: {len(saved_data)}"
    
    # فحص الإعلان 1
    assert saved_data[0]["phone_number"] == "0933123456"
    assert len(saved_data[0]["images dowlod"]) > 0
    assert len(saved_data[0]["nimages"]) > 0
    assert "دمشق" in saved_data[0]["description"]
    
    # فحص الإعلان 2 (المحول من أرقام مشرقية)
    assert saved_data[1]["phone_number"] == "0944889900"
    assert len(saved_data[1]["nimages"]) > 0
    assert "حلب" in saved_data[1]["description"]

    # فحص الإعلان 3 (المحول من دولي +963)
    assert saved_data[2]["phone_number"] == "0988223344"
    assert len(saved_data[2]["nimages"]) > 0
    assert "اللاذقية" in saved_data[2]["description"]

    print("\n" + "="*50)
    print("✅ جميع اختبارات سحب الإعلانات وتطبيق الشروط وحفظ الـ JSON تمت بنجاح 100%!")
    print("="*50)

if __name__ == "__main__":
    test_scraper_pipeline()
