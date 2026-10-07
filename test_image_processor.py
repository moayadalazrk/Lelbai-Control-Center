# -*- coding: utf-8 -*-
"""
اختبار تحميل وضغط وتصغير الصور وتحويلها إلى WebP وحفظها باسم UUID
"""

import os
import sys
from PIL import Image

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from image_processor import download_and_convert_to_webp, DEFAULT_IMGS_DIR

def run_test():
    print("=== بدء اختبار معالجة وتحويل الصور إلى WebP ===")
    test_img_url = "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=1600"
    
    print(f"[+] مسار حفظ الصور: {DEFAULT_IMGS_DIR}")
    print(f"[+] رابط صورة الاختبار: {test_img_url}")
    
    filename = download_and_convert_to_webp(test_img_url)
    
    if not filename:
        print("❌ فشل تحميل أو تحويل الصورة.")
        return False
        
    saved_path = os.path.join(DEFAULT_IMGS_DIR, filename)
    print(f"✅ تم تحميل وتحويل الصورة بنجاح: {filename}")
    print(f"[+] المسار الكامل: {saved_path}")
    
    # فحص أبعاد الصورة المحفوظة وصيغتها
    with Image.open(saved_path) as img:
        print(f"[+] صيغة الملف: {img.format} (متوقع: WEBP)")
        print(f"[+] الأبعاد: {img.size} (العرض: {img.width}px, الارتفاع: {img.height}px)")
        print(f"[+] الحجم على القرص: {os.path.getsize(saved_path) / 1024:.2f} KB")
        
        assert img.format == "WEBP", "يجب أن تكون الصيغة WEBP"
        assert img.width <= 1280 and img.height <= 1280, "يجب ألا تتجاوز الأبعاد 1280px"
        
    print("\n🎉 اختبار تحميل وضغط وتحويل الصور إلى WebP بنظام UUID نجح 100%!")
    return True

if __name__ == "__main__":
    run_test()
