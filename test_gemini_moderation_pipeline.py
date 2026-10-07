# -*- coding: utf-8 -*-
"""
اختبار وحدة الرقابة والهيكلة ولوحة المراجعة والنشر
"""

import os
import sys
import json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from gemini_processor import GeminiProcessor
from publisher import publish_ad_to_website
from config import load_config, save_config

def run_test():
    print("=== اختبار منظومة الذكاء الاصطناعي والمراجعة والنشر 🇸🇾 ===")
    
    # 1. اختبار معالج Gemini بدون مفتاح (Fallback Mode)
    processor = GeminiProcessor(api_key="")
    dummy_ad = {
        "ad_url": "https://facebook.com/groups/test/123",
        "phone_number": "0933123456",
        "description": "شقة للبيع في دمشق المزة 3 غرف وصالون إكساء سوبر ديلوكس بسعر 450 مليون",
        "nimages": ["test_image.webp"],
        "images dowlod": ["https://fb.com/img1.jpg"],
        "location_detected": "دمشق (المزة)"
    }
    
    res = processor.process_and_clean_ad(dummy_ad, "./asstes/imgs")
    print(f"\n[+] اختبار Fallback Mode بدون مفتاح API:")
    print(f"    is_safe: {res.get('is_safe')} | status: {res.get('moderation_status')}")
    print(f"    العنوان المهيكل: {res.get('clean_title')}")
    assert res.get("is_safe") is True, "يجب أن يعمل بمرونة في وضع Fallback"
    
    # 2. اختبار النشر
    success, msg = publish_ad_to_website(res)
    print(f"\n[+] اختبار النشر والاعتماد:")
    print(f"    النتيجة: {success} | الرسالة: {msg}")
    assert success is True, "يجب أن تنجح عملية النشر والاعتماد"
    
    # 3. اختبار قراءة وحفظ الإعدادات
    cfg = load_config()
    print(f"\n[+] اختبار ملف الإعدادات config.json:")
    print(f"    الموديل الافتراضي: {cfg.get('gemini_model')}")
    assert cfg.get("gemini_model") is not None
    
    print("\n" + "="*65)
    print("🎉 جميع اختبارات منظومة الذكاء الاصطناعي والمراجعة نجحت 100%!")
    print("="*65)

if __name__ == "__main__":
    run_test()
