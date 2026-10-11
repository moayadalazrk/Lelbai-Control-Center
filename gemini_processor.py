# -*- coding: utf-8 -*-
"""
محرك الرقابة الذكية والهيكلة عبر Gemini AI (Vision & Moderation)
يقوم بفحص الصور والنصوص وكشف الممنوعات، وتنقية الصور، وهيكلة الإعلان.
"""

import os
import sys
import json
import time
import base64
import requests
from io import BytesIO
from typing import Dict, Any, List, Optional
from PIL import Image

from config import load_config

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USAGE_FILE = os.path.join(BASE_DIR, "gemini_usage.json")
DEFAULT_MODEL = "gemini-3.5-flash"
MODEL_CANDIDATES = ["gemini-3.5-flash", "gemini-3.6-flash", "gemini-flash-lite-latest", "gemini-3.8-flash"]

def record_gemini_call(model_name: str = DEFAULT_MODEL) -> Dict[str, Any]:
    """تسجيل طلب ذكاء اصطناعي جديد وحفظ العداد اليومي"""
    today_str = time.strftime("%Y-%m-%d")
    data = {"date": today_str, "calls_today": 0, "daily_limit": 1500, "rpm_limit": 15, "model": model_name}
    if os.path.exists(USAGE_FILE):
        try:
            with open(USAGE_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                if isinstance(saved, dict) and saved.get("date") == today_str:
                    data = saved
        except Exception:
            pass
    data["calls_today"] = data.get("calls_today", 0) + 1
    data["model"] = model_name
    data["last_call_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(USAGE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    return data

def get_gemini_usage_info(api_key: str = "", model_name: str = DEFAULT_MODEL) -> Dict[str, Any]:
    """استرجاع بيانات ورصيد الاستهلاك اليومي المتبقي"""
    if not api_key:
        api_key = load_config().get("gemini_api_key", "").strip()
    today_str = time.strftime("%Y-%m-%d")
    data = {"date": today_str, "calls_today": 0, "daily_limit": 1500, "rpm_limit": 15, "model": model_name}
    if os.path.exists(USAGE_FILE):
        try:
            with open(USAGE_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                if isinstance(saved, dict) and saved.get("date") == today_str:
                    data = saved
        except Exception:
            pass
    calls = data.get("calls_today", 0)
    limit = data.get("daily_limit", 1500)
    is_conn = bool(api_key.strip())
    return {
        "date": today_str,
        "calls_today": calls,
        "daily_limit": limit,
        "remaining_today": max(0, limit - calls),
        "rpm_limit": 15,
        "model": model_name,
        "is_connected": is_conn,
        "status_label": "متصل وجاهز للعمل 🟢" if is_conn else "غير متصل (المفتاح مفقود) ⚠️"
    }

SYSTEM_PROMPT = """أنت نظام رقابة وتدقيق آلي صارم ومحدد، بالإضافة لكونك منسق بيانات لمنصة إعلانات مبوبة في سوريا (للبيع - lelbai).
مهمتك تنحصر فقط في فحص محتوى الإعلان (النصوص والصور المرفقة) للتأكد من خلوه من المحظورات المنصوص عليها أدناه حصراً، وتحديد أرقام الصور المخالفة واستبعادها، واستخراج بيانات الإعلان المهيكلة.

قواعد الرقابة والضوابط الإلزامية:
1. 📸 ضوابط الصور وخصوصية الأشخاص والوثائق:
   - 🚫 النساء (Women): تشديد قاطع وممنوع تماماً؛ يُحظر أي ظهور للنساء أو وجوههن أو أجسادهن أو عارضات الأزياء (مخالفة: woman_in_photos).
   - 🚫 الرجال (Men): تشديد خفيف؛ إذا كان شخص عابر أو بعيد أو غير مقصود في الخلفية (أثناء تصوير سيارة أو شارع أو عقار) يُقبل وعادي، أما إذا كانت صورة سيلفي مقصودة أو شخصية واضحة جداً لصاحب الإعلان فتُرفض الصورة (مخالفة: man_selfie_in_photos).
   - 🔒 الوثائق الرسمية وجوازات السفر والهويات: ممنوع منعاً باتاً نشر صور جوازات السفر أو البطاقات الشخصية أو الهويات أو المستندات الحساسة حفظاً للأمان والخصوصية (مخالفة: official_documents_or_passports).

2. 🚫 ضوابط السلع المحظورة وأحكام الشريعة الإسلامية:
   - 🚫 الأسلحة الحقيقية: ممنوعة تماماً وتشمل البنادق والمسدسات والذخائر الحية (ألعاب الأطفال ومجسمات البلاستيك مسموحة).
   - 🚫 المحرمات: الخنزير ولحومه ومشتقاته، المشروبات الكحولية والمسكرات (ممنوعة تماماً).
   - 🚫 الأدوات والآلات الموسيقية: ممنوعة تماماً (تشمل العود، الغيتار، البيانو، الكمان، الطبول، الدفوف، الميكروفونات الغنائية، إلخ).
   - 🚫 الألعاب الإلكترونية: أسطوانات وأكواد وحسابات الألعاب مثل حسابات ببجي وبلايستيشن ألعاب (ممنوعة).
   - 🚫 المحتوى الإجرامي والاتجار بالبشر: أي إعلان صريح لـ (عرض أشخاص، أطفال للتبني/البيع، مخدرات، روابط احتيالية، ألفاظ مخلة) = مخالفة صارمة (مخالفة: prohibited_goods_or_human_trafficking).

3. 💰 ضوابط استخراج الأسعار والعملات في السوق السوري:
   - العملات المقبولة: "USD" أو "SYP".
   - أسعار السيارات في سوريا عادة بالدولار (مثل 8200$, 10500 وسكرا، 82 ورقة) أو بمئات الملايين بالليرة السورية.
   - إذا ذُكر السعر بالملايين (مثل: "150 مليون" أو "450 م"): اكتب الرقم كاملاً في amount (مثلاً 150000000) والعملة "SYP".
   - إذا ذُكر بآلاف الدولارات (مثل: "12 الف دولار" أو "8.5 الف $"): اكتب الرقم كاملاً (مثلاً 12000) والعملة "USD".
   - إذا ذُكر بالورقة (مثل: "82 ورقة"): الورقة تعني 100 دولار، فيكون amount = 8200 و currency = "USD".
   - إذا كان السعر غير محدد أو على السوم أو خاص: يكون amount = null و is_negotiable = true.

4. 📍 ضوابط استخراج المدينة والمنطقة:
   - حدد المدينة السورية الأساسية (دمشق، ريف دمشق، حلب، ريف حلب، حمص، حماة، إدلب، اللاذقية، طرطوس، درعا، السويداء، القنيطرة، دير الزور، الحسكة، الرقة).
   - إذا ذُكرت منطقة فرعية (مثل: المزة، كفرسوسة، جرمانا، صحنايا، جبلة، سلمية، سرمدا)، اذكرها في sub_district.

5. 📂 ضوابط تصنيف الإعلان في أقسام المنصة الرسمية (Lelbai Taxonomy):
يجب تصنيف الإعلان بدقة متناهية واختيار الـ category_id والقسم المناسب من الشجرة الرسمية التالية حصراً:
- 👗 الأزياء والعناية الشخصية:
  * ملابس نسائية وفساتين ولانجري: {"id": 3167, "name": "ملابس نسائية وفساتين", "parent_name": "الأزياء والعناية الشخصية"}
  * ملابس رجالية وألبسة شبابية: {"id": 3166, "name": "ملابس رجالية", "parent_name": "الأزياء والعناية الشخصية"}
  * ملابس أطفال ومواليد: {"id": 3168, "name": "ملابس أطفال ومواليد", "parent_name": "الأزياء والعناية الشخصية"}
  * ساعات ومجوهرات وإكسسوارات: {"id": 3169, "name": "ساعات ومجوهرات وإكسسوارات", "parent_name": "الأزياء والعناية الشخصية"}
  * عطور ومستحضرات تجميل: {"id": 3170, "name": "عطور ومستحضرات تجميل", "parent_name": "الأزياء والعناية الشخصية"}
- 🏢 العقارات:
  * شقق (للبيع أو للإيجار أو رهن): {"id": 3131, "name": "شقق", "parent_name": "العقارات"}
  * فلل وبيوت ومنازل: {"id": 3132, "name": "فلل وبيوت", "parent_name": "العقارات"}
  * أراضي ومزارع وعقارات زراعية: {"id": 3133, "name": "أراضي ومزارع", "parent_name": "العقارات"}
  * محلات ومكاتب ومستودعات تجارية: {"id": 3134, "name": "محلات وعقارات تجارية", "parent_name": "العقارات"}
  * شاليهات واستراحات: {"id": 3135, "name": "شاليهات واستراحات", "parent_name": "العقارات"}
- 🚗 السيارات:
  * سيارات للبيع (حدد الماركة المناسبة):
    - هيونداي [1144]، كيا [1155]، تويوتا [1166]، مرسيدس-بنز [1226]، بي إم دبليو [1235]، مازدا [1176]، نيسان [1184]، سايبا [1193]، شام [1199]، دايو [1205]، سوزوكي [1212]، ميتسوبيشي [1219]، بيجو [1242]، فولكس فاجن [1251]، رينو [1259]، شيفروليه [1295]، أوبل [1303]، فورد [1310]، هوندا [1318]، أودي [1336]، سكودا [1343]، فيات [1349]، لاند روفر [1356]، ماركات أخرى [1832]
  * قطع غيار وإكسسوارات السيارات: {"id": 1369, "name": "قطع غيار وإكسسوارات السيارات", "parent_name": "السيارات"}
  * سيارات للإيجار: {"id": 1395, "name": "سيارات للإيجار", "parent_name": "السيارات"}
- 📱 الإلكترونيات والشبكات:
  * جوالات وهواتف ذكية (تشمل آيفون، سامسونج، شاومي، ريدمي، هونر Honor، هواوي، ريلمي، أوبو، انفينكس، تكنو، بوكو، فيفو، نوكيا، ومواصفات الرام والذاكرة): {"id": 3139, "name": "جوالات وهواتف ذكية", "parent_name": "الإلكترونيات والشبكات"}
  * كمبيوتر ولابتوب: {"id": 3141, "name": "كمبيوتر ولابتوب", "parent_name": "الإلكترونيات والشبكات"}
  * أجهزة لوحية وآيباد: {"id": 3140, "name": "أجهزة لوحية وآيباد", "parent_name": "الإلكترونيات والشبكات"}
  * شاشات وتلفزيونات: {"id": 3143, "name": "شاشات وتلفزيونات", "parent_name": "الإلكترونيات والشبكات"}
  * ساعات ذكية وسماعات وإكسسوارات: {"id": 3144, "name": "ساعات ذكية وسماعات وإكسسوارات", "parent_name": "الإلكترونيات والشبكات"}
- ☀️ الطاقة البديلة والكهرباء:
  * ألواح ومنظومات طاقة شمسية: {"id": 3136, "name": "ألواح ومنظومات طاقة شمسية", "parent_name": "الطاقة البديلة والكهرباء"}
  * إنفيرترات وبطاريات: {"id": 3137, "name": "إنفيرترات وبطاريات", "parent_name": "الطاقة البديلة والكهرباء"}
  * مولدات ومستلزمات كهرباء: {"id": 3138, "name": "مولدات ومستلزمات كهرباء", "parent_name": "الطاقة البديلة والكهرباء"}
- 🛋️ المنزل والأثاث:
  * أثاث منزلي وغرف: {"id": 3148, "name": "أثاث منزلي وغرف", "parent_name": "المنزل والأثاث"}
  * أجهزة كهربائية ومنزلية (غسالات، برادات، أفران): {"id": 3149, "name": "أجهزة كهربائية ومنزلية", "parent_name": "المنزل والأثاث"}
  * مطابخ وأواني: {"id": 3150, "name": "مطابخ وأواني", "parent_name": "المنزل والأثاث"}
  * سجاد ومفروشات وستائر: {"id": 3151, "name": "سجاد ومفروشات وستائر", "parent_name": "المنزل والأثاث"}
- 🏍️ الدراجات النارية:
  * دراجات نارية (ميتورات): {"id": 3091, "name": "دراجات نارية (ميتورات)", "parent_name": "الدراجات النارية"}
  * دراجات هوائية (بسكليتات): {"id": 3117, "name": "دراجات هوائية (بسكليتات)", "parent_name": "الدراجات النارية"}
- 🐑 الحيوان ومواشي:
  * غنم وماعز وأبقار وخيول: {"id": 3179, "name": "غنم وماعز وإبل", "parent_name": "الحيوان ومواشي"}
  * طيور ودواجن وحمام: {"id": 3181, "name": "طيور ودواجن وحمام", "parent_name": "الحيوان ومواشي"}
  * قطط وحيوانات أليفة: {"id": 3182, "name": "قطط وحيوانات أليفة ومستلزماتها", "parent_name": "الحيوان ومواشي"}
- 🧱 مواد البناء والزراعة والخدمات:
  * مواد بناء ومعدات مهنية: {"id": 3185, "name": "مواد بناء وأسمنت وحديد", "parent_name": "مواد البناء والمعدات"}
  * زراعة وبذور ومضخات: {"id": 3190, "name": "أشجار وأشتال وبذور", "parent_name": "الزراعة ومستلزمات الإنتاج"}
  * وظائف وأعمال: {"id": 3154, "name": "وظائف شاغرة", "parent_name": "الوظائف والأعمال"}
  * خدمات ومقاولات: {"id": 3158, "name": "خدمات مقاولات", "parent_name": "الخدمات"}
  * أصناف عامة ومتنوعة: {"id": 3207, "name": "أصناف عامة ومتنوعة", "parent_name": "أخرى"}

⛔ أشياء مسموحة تماماً ويُمنع رفض الإعلان بسببها (DO NOT REJECT FOR THESE):
- ✅ عدم تطابق الصور مع العنوان أو الوصف: مسموح ومقبول ولا يعتبر مخالفة إطلاقاً.
- ✅ الأطفال: ظهور الأطفال في الصور مسموح وتمريره عادي.
- ✅ الأجهزة الإلكترونية: أجهزة البلايستيشن والإكسبوكس والكمبيوترات والهواتف والشاشات مسموحة ومقبولة 100%.
- ✅ ألعاب الأطفال العادية والدمى والمجسمات البلاستيكية: مسموحة تماماً.

⚠️ تنبيه حاسم بخصوص الصور والمخالفات المتعددة:
- حدد في مصفوفة approved_image_indices أرقام الصور السليمة (0-indexed)، وفي rejected_image_indices أرقام الصور المخالفة.
- إذا كانت كل الصور مخالفة أو كانت السلعة نفسها محظورة بالكامل (مثل سلاح أو كحول أو حسابات ألعاب): تكون is_safe = false.
- إذا تم استبعاد صورة مخالفة وبقيت صور سليمة وكان أصل الإعلان مسموحاً: تكون is_safe = true مع الإبقاء على الصور السليمة فقط في approved_image_indices.

المطلوب:
أرجع إجابتك حصراً بصيغة JSON بدون أي نصوص خارج الـ JSON بالشكل التالي:

{
  "is_safe": true,
  "status": "safe",
  "flags": [],
  "summary": "الإعلان سليم ومطابق للشروط",
  "suggested_rejection_reason": null,
  "approved_image_indices": [0, 1, 2],
  "rejected_image_indices": [],
  "structured_ad": {
    "category": {
      "id": 3167,
      "name": "ملابس نسائية وفساتين",
      "parent_name": "الأزياء والعناية الشخصية"
    },
    "clean_title": "عنوان جذاب ومختصر من 5-8 كلمات",
    "location": {
      "city_name": "دمشق",
      "sub_district": null
    },
    "price": {
      "amount": null,
      "currency": "SYP",
      "is_negotiable": true
    },
    "specifications": {
      "make": null,
      "model": null,
      "year": null,
      "transmission": null
    },
    "clean_description": "• تفاصيل الإعلان منسقة في نقاط واضحة واحترافية وبدون حشو"
  }
}
"""

class GeminiProcessor:
    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_MODEL):
        cfg = load_config()
        if api_key is not None:
            self.api_key = api_key.strip()
        else:
            self.api_key = cfg.get("gemini_api_key", "").strip()
        self.model = model or cfg.get("gemini_model", DEFAULT_MODEL)
        self.last_call_time = 0.0

    def _prepare_image_part(self, image_path: str) -> Optional[Dict[str, Any]]:
        """تحويل الصورة إلى Base64 مصغرة لتوفير التوكنز والسرعة الفائقة في الرؤية البصرية"""
        try:
            if not os.path.exists(image_path):
                return None
            
            with Image.open(image_path) as img:
                # تصغير الصورة للمعاينة الذكية (أقصى بُعد 512px)
                img = img.convert("RGB")
                img.thumbnail((512, 512), Image.Resampling.LANCZOS)
                
                buffer = BytesIO()
                img.save(buffer, format="JPEG", quality=80)
                img_bytes = buffer.getvalue()
                
                b64_str = base64.b64encode(img_bytes).decode("utf-8")
                return {
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": b64_str
                    }
                }
        except Exception as e:
            return None

    def moderate_and_structure_ad(self, ad: Dict[str, Any], imgs_dir: str) -> Dict[str, Any]:
        """
        فحص الإعلان بالكامل (نص + صور) وتصنيفه وهيكلته عبر Gemini Vision Cloud API في طلب واحد فائق السرعة
        """
        from image_safety_filter import moderate_images_locally
        nimages = ad.get("nimages", [])

        # التحقق الأولي السريع من سلامة وأبعاد ملفات الصور الفيزيائية
        valid_indices, invalid_indices, invalid_reasons = moderate_images_locally(nimages, imgs_dir)

        if not self.api_key:
            from ai_ad_enhancer import enhance_ad_with_super_ai
            enhanced = enhance_ad_with_super_ai(ad)
            
            approved_imgs = valid_indices if (valid_indices or not nimages) else list(range(len(nimages)))
            rejected_imgs = invalid_indices if valid_indices else []
            return {
                "is_safe": True,
                "status": "pending",
                "flags": ["no_api_key_for_vision"],
                "summary": "⚠️ الرقابة البصرية متوقفة: يرجى إضافة مفتاح Gemini API في الإعدادات لفحص الصور بالذكاء الاصطناعي",
                "suggested_rejection_reason": None,
                "approved_image_indices": approved_imgs,
                "rejected_image_indices": rejected_imgs,
                "structured_ad": {
                    "category": enhanced.get("leaf_category_name", "عام"),
                    "clean_title": enhanced.get("clean_title", ""),
                    "price": enhanced.get("price_info", {"amount": None, "currency": "SYP", "is_negotiable": True}),
                    "specifications": enhanced.get("specifications", {}),
                    "clean_description": enhanced.get("clean_description", ad.get("description", ""))
                }
            }

        # التحكم بمعدل الطلبات لتجنب تجاوز حد الـ 15 RPM
        elapsed_since_last = time.time() - self.last_call_time
        if elapsed_since_last < 2.0:
            time.sleep(2.0 - elapsed_since_last)

        # تجهيز محتوى الرسالة - إرسال كافة الصور المرفقة الصالحة إلى Gemini Vision API
        parts: List[Dict[str, Any]] = []

        ad_text_prompt = f"""بيانات الإعلان المطلوب فحصها وتدقيق صورها بالكامل:
- الوصف الأصلي للإعلان:
{ad.get('description', '')}

- رقم الهاتف: {ad.get('phone_number', '')}
- المدينة والمنطقة المكتشفة: {ad.get('location_detected', '')}
- عدد الصور المرفقة: {len(nimages)}

يرجى فحص النصوص والصور المرفقة عبر الرؤية البصرية بدقة شديدة واستبعاد الصور المخالفة فقط:"""

        parts.append({"text": ad_text_prompt})

        # إرفاق الصور المصغرة بدقة Base64 JPEG للفحص البصري الفائق
        active_slots = []
        for orig_idx in valid_indices:
            if orig_idx < len(nimages):
                img_filename = nimages[orig_idx]
                full_img_path = os.path.join(imgs_dir, img_filename)
                img_part = self._prepare_image_part(full_img_path)
                if img_part:
                    slot = len(active_slots)
                    parts.append({"text": f"--- صورة رقم [{slot}] ---"})
                    parts.append(img_part)
                    active_slots.append(orig_idx)

        payload = {
            "system_instruction": {
                "parts": [{"text": SYSTEM_PROMPT}]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": parts
                }
            ],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.1
            }
        }

        models_to_try = [self.model] if self.model in MODEL_CANDIDATES else [DEFAULT_MODEL]
        for m in MODEL_CANDIDATES:
            if m not in models_to_try:
                models_to_try.append(m)

        for current_model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{current_model}:generateContent?key={self.api_key}"
            try:
                self.last_call_time = time.time()
                response = requests.post(url, json=payload, timeout=20)
                
                if response.status_code == 200:
                    self.model = current_model
                    record_gemini_call(current_model)
                    resp_json = response.json()
                    raw_text = resp_json["candidates"][0]["content"]["parts"][0]["text"].strip()
                    result = json.loads(raw_text)
                    
                    # ترجمة فهارس الصور التي وافق عليها Gemini إلى الفهارس الأصلية
                    gemini_appr = result.get("approved_image_indices", [])
                    final_appr = []
                    for i in gemini_appr:
                        if isinstance(i, int) and 0 <= i < len(active_slots):
                            orig_i = active_slots[i]
                            if orig_i not in final_appr:
                                final_appr.append(orig_i)
                    
                    final_rej = sorted([i for i in range(len(nimages)) if i not in final_appr])
                    
                    result["approved_image_indices"] = final_appr
                    result["rejected_image_indices"] = final_rej

                    if len(final_appr) == 0 and len(nimages) > 0:
                        result["is_safe"] = False
                        result["suggested_rejection_reason"] = result.get("suggested_rejection_reason") or "جميع الصور المرفقة مخالفة للضوابط الشرعية أو الرقابية"
                        result["summary"] = f"🚫 تم رفض الإعلان عبر Gemini Vision API: استبعاد كافة الصور ({len(final_rej)} صورة مخالفة)"
                    elif final_rej:
                        result["summary"] = f"🤖 تم فحص وتدقيق الصور عبر Gemini Vision API: اعتماد {len(final_appr)} صورة نظيفة، واستبعاد {len(final_rej)} صورة مخالفة"
                    else:
                        result["summary"] = f"🤖 تم اعتماد الإعلان والصور بنجاح عبر Gemini Vision API ({len(final_appr)} صورة سليمة)"

                    return result
                else:
                    error_msg = response.text[:200]
                    print(f"[!] تنبيه من Gemini API للنموذج {current_model} ({response.status_code}): {error_msg}")
                    continue
            except Exception as e:
                print(f"[!] استثناء في معالجة النموذج {current_model}: {e}")
                continue

        # كائن افتراضي آمن في حال انقطاع الشبكة
        fallback_safe = (len(valid_indices) > 0 or len(nimages) == 0)
        return {
            "is_safe": fallback_safe,
            "status": "safe" if fallback_safe else "flagged",
            "flags": ["network_fallback"],
            "summary": "⚠️ تعذر اتصال الذكاء الاصطناعي السحابي (Gemini Vision API) مؤقتاً - الإعلان بانتظار المراجعة",
            "suggested_rejection_reason": None,
            "approved_image_indices": valid_indices,
            "rejected_image_indices": invalid_indices,
            "structured_ad": {
                "category": "عام",
                "clean_title": ad.get("description", "")[:60].replace("\n", " ").strip(),
                "price": {"amount": None, "currency": "SYP", "is_negotiable": True},
                "specifications": {},
                "clean_description": ad.get("description", "")
            }
        }

    def process_and_clean_ad(self, ad: Dict[str, Any], imgs_dir: str) -> Dict[str, Any]:
        """
        معالجة الإعلان بالكامل وتحديث بياناته وتنقية الصور المخالفة
        """
        ai_res = self.moderate_and_structure_ad(ad, imgs_dir)
        
        is_safe = ai_res.get("is_safe", True)
        flags = ai_res.get("flags", [])
        summary = ai_res.get("summary", "")
        rejection_reason = ai_res.get("suggested_rejection_reason")
        approved_indices = ai_res.get("approved_image_indices", [])
        rejected_indices = ai_res.get("rejected_image_indices", [])
        structured = ai_res.get("structured_ad", {})

        original_nimages = ad.get("nimages", [])
        original_urls = ad.get("images dowlod", [])

        # تصفية الصور وحذف المخالفة منها
        filtered_nimages = []
        filtered_urls = []
        for idx in approved_indices:
            if idx < len(original_nimages):
                filtered_nimages.append(original_nimages[idx])
            if idx < len(original_urls):
                filtered_urls.append(original_urls[idx])

        # حذف ملفات الصور المخالفة فعلياً من القرص لحماية المنصة وتوفير المساحة
        for idx in rejected_indices:
            if idx < len(original_nimages):
                bad_img_path = os.path.join(imgs_dir, original_nimages[idx])
                if os.path.exists(bad_img_path):
                    try:
                        os.remove(bad_img_path)
                    except Exception:
                        pass

        # إذا لم يتبق أي صورة صالحة وكان في الأصل هناك صور مرفقة، نعتبر الإعلان مرفوضاً فقط إذا كان الفحص بالذكاء الاصطناعي قد استبعدها
        if len(filtered_nimages) == 0 and len(original_nimages) > 0 and bool(self.api_key):
            is_safe = False
            if "no_valid_images_left" not in flags:
                flags.append("no_valid_images_left")

        processed_ad = ad.copy()
        processed_ad["nimages"] = filtered_nimages
        processed_ad["images dowlod"] = filtered_urls
        processed_ad["is_safe"] = is_safe
        processed_ad["moderation_status"] = "safe" if is_safe else "flagged"
        processed_ad["flags"] = flags
        processed_ad["moderation_summary"] = summary
        processed_ad["rejection_reason"] = rejection_reason
        
        # دمج البيانات المهيكلة وتدقيق السعر بدقة فائقة
        from ai_ad_enhancer import extract_smart_price
        gemini_price = structured.get("price", {})
        price_amt = gemini_price.get("amount") if isinstance(gemini_price, dict) else None
        price_curr = gemini_price.get("currency", "SYP") if isinstance(gemini_price, dict) else "SYP"
        is_neg = gemini_price.get("is_negotiable", True) if isinstance(gemini_price, dict) else True

        # استخراج وتدقيق السعر المحلي فائق الدقة
        extracted = extract_smart_price(ad.get("description", ""))
        if not price_amt or str(price_amt) == "0":
            if extracted:
                price_amt = extracted[0]
                price_curr = extracted[1]
        elif extracted:
            try:
                g_val = float(str(price_amt).replace(",", ""))
                e_val = float(extracted[0])
                # إذا أعاد الذكاء الاصطناعي رقماً صغيراً بالخطأ بينما النص يذكر الملايين
                if e_val >= 1000000 and g_val < 10000:
                    price_amt = extracted[0]
                    price_curr = extracted[1]
            except Exception:
                pass

        # استخراج وتدقيق التصنيف الدقيق من الذكاء الاصطناعي وربطه بشجرة المنصة الرسمية
        from ai_ad_enhancer import get_category_name_by_id, build_category_hierarchy, ensure_leaf_category_id, CAT_BY_ID
        
        cat_data = structured.get("category")
        category_id = None
        category_name = None
        
        if isinstance(cat_data, dict):
            category_id = cat_data.get("id")
            category_name = cat_data.get("name")
        elif isinstance(cat_data, (int, str)) and str(cat_data).isdigit():
            category_id = int(cat_data)
        elif isinstance(cat_data, str) and cat_data.strip():
            c_str = cat_data.strip().lower()
            for c in CAT_BY_ID.values():
                if c.get("name_ar", "").strip().lower() == c_str:
                    category_id = c["id"]
                    break

        if not category_id or int(category_id) not in CAT_BY_ID:
            from ai_ad_enhancer import detect_smart_category
            detected = detect_smart_category(f"{structured.get('clean_title', '')} {ad.get('description', '')}")
            category_id = detected["category_id"]
            category_name = detected["category_name"]
            category_hierarchy = detected["category_hierarchy"]
        else:
            category_id = ensure_leaf_category_id(int(category_id))
            category_name = get_category_name_by_id(category_id)
            category_hierarchy = build_category_hierarchy(category_id)

        processed_ad["leaf_category_id"] = category_id
        processed_ad["leaf_category_name"] = category_name
        processed_ad["category_hierarchy"] = category_hierarchy
        processed_ad["category"] = category_name
        processed_ad["id-categorie"] = category_id
        processed_ad["clean_title"] = structured.get("clean_title") or ad.get("description", "")[:60]
        processed_ad["price_info"] = {
            "amount": price_amt,
            "currency": price_curr,
            "is_negotiable": is_neg
        }
        processed_ad["specifications"] = structured.get("specifications", {})
        processed_ad["clean_description"] = structured.get("clean_description") or ad.get("description", "")

        # التأكد من عدم فقدان المدينة والمنطقة
        if not processed_ad.get("id-citie") or not processed_ad.get("city_name"):
            from syria_filter import classify_location
            loc = classify_location(ad.get("description", ""))
            if loc.get("id-citie"):
                processed_ad["id-citie"] = loc.get("id-citie")
                processed_ad["id-sub_districts"] = loc.get("id-sub_districts")
                processed_ad["city_name"] = loc.get("city_name")
                processed_ad["sub_district_name"] = loc.get("sub_district_name")
                processed_ad["location_detected"] = loc.get("location_detected")

        return processed_ad
