# -*- coding: utf-8 -*-
"""
إدارة إعدادات ومفاتيح المنظومة (Gemini API & Website Publishing)
"""

import os
import json
from typing import Dict, Any

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

MASTER_WEBSITE_API_URL = "https://api.lelbai.com/public/api/listings"
MASTER_WEBSITE_API_KEY = "67|5181926855ca52522dec3990517f272b027b745f"

DEFAULT_CONFIG = {
    "gemini_api_key": "",
    "gemini_model": "gemini-2.0-flash",
    "website_api_url": MASTER_WEBSITE_API_URL,
    "website_api_key": MASTER_WEBSITE_API_KEY,
    "min_images_required": 1,
    "max_images_per_ad": 5,
    "auto_publish_safe_ads": False,
    "dashboard_port": 5000,
    "manager_shortcut": os.path.join(os.path.expanduser("~"), "Desktop", "لوحة تحكم المنجر.lnk"),
    "manager_servers_dir": r"C:\xampp\htdocs\projects\AZ",
    "manager_url": "http://localhost:8002",
    "github_repo": "https://github.com/moayadalazrk/Lelbai-Control-Center.git"
}

def load_config() -> Dict[str, Any]:
    """تحميل الإعدادات من ملف config.json مع دعم متغيرات البيئة والقيم الافتراضية الموثوقة"""
    config = DEFAULT_CONFIG.copy()
    
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                saved = json.load(f)
                if isinstance(saved, dict):
                    config.update(saved)
        except Exception:
            pass

    # ضمان عدم فقدان توكن الموقع الأساسي إذا تم حفظ حقل فارغ بالخطأ
    if not config.get("website_api_key", "").strip():
        config["website_api_key"] = MASTER_WEBSITE_API_KEY
    if not config.get("website_api_url", "").strip():
        config["website_api_url"] = MASTER_WEBSITE_API_URL

    # إذا كان مفتاح الـ API متاحاً في متغيرات البيئة
    env_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if env_key:
        config["gemini_api_key"] = env_key

    return config

def save_config(config: Dict[str, Any]):
    """حفظ الإعدادات في ملف config.json"""
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[!] خطأ أثناء حفظ config.json: {e}")

def get_gemini_api_key() -> str:
    """الحصول على مفتاح Gemini API"""
    cfg = load_config()
    return cfg.get("gemini_api_key", "").strip()
