# -*- coding: utf-8 -*-
"""
اختبار شامل لمنظومة الفحص البصري والرقابة الشرعية الذكية
"""
import os
import sys
from PIL import Image, ImageDraw

def test_safety_pipeline():
    print("==================================================")
    print("بدء اختبار منظومة الرقابة البصرية والأمان (YOLO + Skin)")
    print("==================================================")

    from image_safety_filter import inspect_single_image_locally, analyze_skin_ratio, moderate_images_locally
    from gemini_processor import GeminiProcessor

    # مجلد الصور الحقيقي
    imgs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "asstes", "imgs"))
    os.makedirs(imgs_dir, exist_ok=True)

    # 1. اختبار صورة صغيرة جداً (أيقونة)
    tiny_path = os.path.join(imgs_dir, "test_tiny.jpg")
    img_tiny = Image.new("RGB", (64, 64), color=(200, 200, 200))
    img_tiny.save(tiny_path)

    is_safe_tiny, reason_tiny = inspect_single_image_locally(tiny_path)
    print(f"1. صورة مصغرة (64x64): is_safe={is_safe_tiny}, reason={reason_tiny}")
    assert not is_safe_tiny, "فشل استبعاد الصورة المصغرة!"

    # 2. اختبار صورة بنسبة أبعاد مشوهة (شريط)
    distorted_path = os.path.join(imgs_dir, "test_strip.jpg")
    img_strip = Image.new("RGB", (800, 50), color=(100, 100, 100))
    img_strip.save(distorted_path)

    is_safe_strip, reason_strip = inspect_single_image_locally(distorted_path)
    print(f"2. صورة شريط مشوهة (800x50): is_safe={is_safe_strip}, reason={reason_strip}")
    assert not is_safe_strip, "فشل استبعاد الصورة المشوهة!"

    # 3. اختبار صورة عادية لسيارة أو منتج نظيف
    clean_path = os.path.join(imgs_dir, "test_clean_car.jpg")
    img_clean = Image.new("RGB", (600, 400), color=(30, 40, 50))
    # رسم شكل سيارة افتراضي
    draw = ImageDraw.Draw(img_clean)
    draw.rectangle([100, 150, 500, 300], fill=(70, 80, 90))
    img_clean.save(clean_path)

    is_safe_clean, reason_clean = inspect_single_image_locally(clean_path)
    print(f"3. صورة منتج نظيف (600x400): is_safe={is_safe_clean}, reason={reason_clean}")
    assert is_safe_clean, "فشل اعتماد الصورة النظيفة!"

    # 4. اختبار فحص قائمة صور متكاملة
    test_filenames = ["test_tiny.jpg", "test_strip.jpg", "test_clean_car.jpg"]
    appr, rej, reasons = moderate_images_locally(test_filenames, imgs_dir)
    print(f"4. نتائج فحص القائمة: المعتمد={appr}, المستبعد={rej}")
    assert 2 in appr, "يجب اعتماد الصورة النظيفة (فهرس 2)"
    assert 0 in rej and 1 in rej, "يجب استبعاد الصور المخالفة (فهرس 0 و 1)"

    # 5. اختبار GeminiProcessor بدون مفتاح (الوضع التلقائي للمستخدم)
    print("\n5. اختبار معالجة إعلان عبر GeminiProcessor (بدون مفتاح API):")
    processor = GeminiProcessor(api_key="")
    sample_ad = {
        "title": "كيا سيراتو للبيع في دمشق",
        "description": "كيا سيراتو 2012 خالية من الداخل بحالة ممتازة في دمشق السعر 120 مليون للتواصل 0944123456",
        "phone_number": "0944123456",
        "location_detected": "دمشق",
        "nimages": ["test_tiny.jpg", "test_clean_car.jpg"],
        "images dowlod": ["http://fake.com/tiny.jpg", "http://fake.com/car.jpg"]
    }

    processed = processor.process_and_clean_ad(sample_ad, imgs_dir)
    print(f"حالة الإعلان: is_safe={processed.get('is_safe')}")
    print(f"ملخص الرقابة: {processed.get('moderation_summary')}")
    print(f"الصور المتبقية في الإعلان: {processed.get('nimages')}")
    assert len(processed.get("nimages")) == 1, "يجب أن يتبقى فقط الصورة النظيفة!"
    assert processed.get("nimages")[0] == "test_clean_car.jpg", "يجب أن تكون الصورة المتبقية هي test_clean_car.jpg"
    assert not os.path.exists(tiny_path), "يجب حذف ملف الصورة المخالفة من القرص!"

    # تنظيف ملفات الاختبار
    for p in [tiny_path, distorted_path, clean_path]:
        if os.path.exists(p):
            try:
                os.remove(p)
            except Exception:
                pass

    print("\n✅ كافة اختبارات الرقابة البصرية والأمان نجحت بنسبة 100%!")

if __name__ == "__main__":
    test_safety_pipeline()
