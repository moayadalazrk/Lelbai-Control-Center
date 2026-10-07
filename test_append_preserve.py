# -*- coding: utf-8 -*-
"""
اختبار التأكد من أن البوت لا يمسح أي بيانات سابقة أبداً، ويقوم بالإضافة والتراكم التلقائي.
"""

import os
import sys
import json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from scraper import SyrianAdScraper

def run_test():
    print("=== اختبار نظام الحفظ التراكمي (Append-Only) ومنع المسح نهائياً ===")
    
    test_json = "test_cumulative_ads.json"
    if os.path.exists(test_json):
        os.remove(test_json)
        
    scraper = SyrianAdScraper(user_data_dir="./test_browser_session", headless=True)
    
    # 1. محاكاة سحب 3 إعلانات من المجموعة الأولى
    print("\n[+] محاكاة المجموعة الأولى: إضافة 3 إعلانات...")
    ad1 = {"ad_url": "https://fb.com/1", "phone_number": "0933111111", "description": "إعلان سيارة 1", "images dowlod": [], "nimages": [], "id-citie": 1, "id-sub_districts": 1}
    ad2 = {"ad_url": "https://fb.com/2", "phone_number": "0933222222", "description": "إعلان شقة 2", "images dowlod": [], "nimages": [], "id-citie": 1, "id-sub_districts": 2}
    ad3 = {"ad_url": "https://fb.com/3", "phone_number": "0933333333", "description": "إعلان محل 3", "images dowlod": [], "nimages": [], "id-citie": 2, "id-sub_districts": 29}
    
    scraper.append_ad_to_file(test_json, ad1)
    scraper.append_ad_to_file(test_json, ad2)
    scraper.append_ad_to_file(test_json, ad3)
    
    with open(test_json, "r", encoding="utf-8") as f:
        data1 = json.load(f)
    print(f"    عدد الإعلانات في الملف بعد المجموعة الأولى: {len(data1)} (متوقع: 3)")
    assert len(data1) == 3
    
    # 2. محاكاة الانتقال إلى المجموعة الثانية وإضافة إعلانين
    print("\n[+] محاكاة الانتقال للمجموعة الثانية: إضافة إعلانين جديدين...")
    ad4 = {"ad_url": "https://fb.com/4", "phone_number": "0944444444", "description": "إعلان هاتف 4", "images dowlod": [], "nimages": [], "id-citie": 3, "id-sub_districts": None}
    ad5 = {"ad_url": "https://fb.com/5", "phone_number": "0955555555", "description": "إعلان مزرعة 5", "images dowlod": [], "nimages": [], "id-citie": 8, "id-sub_districts": 224}
    
    scraper.append_ad_to_file(test_json, ad4)
    scraper.append_ad_to_file(test_json, ad5)
    
    with open(test_json, "r", encoding="utf-8") as f:
        data2 = json.load(f)
    print(f"    عدد الإعلانات في الملف بعد المجموعة الثانية: {len(data2)} (متوقع: 5 - لم يُمسح أي شيء من المجموعة الأولى)")
    assert len(data2) == 5
    assert data2[0]["phone_number"] == "0933111111"
    assert data2[4]["phone_number"] == "0955555555"
    
    # 3. محاكاة إغلاق البوت وإعادة تشغيله من جديد تماماً في جلسة جديدة
    print("\n[+] محاكاة إغلاق وتشغيل البوت في جلسة جديدة وإضافة المجموعة الثالثة...")
    new_scraper = SyrianAdScraper(user_data_dir="./test_browser_session", headless=True)
    new_scraper.load_existing_ads(test_json)
    
    ad6 = {"ad_url": "https://fb.com/6", "phone_number": "0966666666", "description": "إعلان طاقة شمسية 6", "images dowlod": [], "nimages": [], "id-citie": 6, "id-sub_districts": None}
    new_scraper.append_ad_to_file(test_json, ad6)
    
    with open(test_json, "r", encoding="utf-8") as f:
        data3 = json.load(f)
    print(f"    عدد الإعلانات في الملف بعد الجلسة الجديدة: {len(data3)} (متوقع: 6)")
    assert len(data3) == 6
    
    # تنظيف ملف الاختبار
    if os.path.exists(test_json):
        os.remove(test_json)
        
    print("\n" + "="*65)
    print("✅ نظام الحفظ التراكمي الدائم نجح 100%! من المستحيل مسح أي إعلان سابق.")
    print("="*65)

if __name__ == "__main__":
    run_test()
