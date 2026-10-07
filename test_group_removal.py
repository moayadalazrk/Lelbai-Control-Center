# -*- coding: utf-8 -*-
"""
اختبار حذف المجموعة المكتملة من ملف groups.txt
"""

import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from main import remove_group_from_file

def run_test():
    print("=== اختبار حذف المجموعة المكتملة من الملف ===")
    test_file = "test_groups_dummy.txt"
    
    sample_content = """# ================================================================
# 🚗 مجموعات السيارات
# ================================================================
# 1. سوق سيارات سوريا
https://www.facebook.com/groups/5259742280745703/
# 2. سوق السيارات في إدلب
https://www.facebook.com/groups/616337179824577/
# 3. أضخم سوق السيارات
https://www.facebook.com/groups/357304532514339/
"""
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(sample_content)
        
    print("[+] الملف قبل الحذف:")
    print(sample_content)
    
    # حذف المجموعة الأولى
    url_to_remove = "https://www.facebook.com/groups/5259742280745703/"
    print(f"\n[+] جاري حذف: {url_to_remove}")
    remove_group_from_file(test_file, url_to_remove)
    
    with open(test_file, "r", encoding="utf-8") as f:
        new_content = f.read()
        
    print("\n[+] الملف بعد الحذف:")
    print(new_content)
    
    assert "5259742280745703" not in new_content, "يجب أن يتم حذف الرابط"
    assert "616337179824577" in new_content, "المجموعات الأخرى يجب أن تبقى"
    assert "357304532514339" in new_content, "المجموعات الأخرى يجب أن تبقى"
    
    if os.path.exists(test_file):
        os.remove(test_file)
        
    print("\n🎉 اختبار حذف المجموعة المكتملة نجح 100%!")

if __name__ == "__main__":
    run_test()
