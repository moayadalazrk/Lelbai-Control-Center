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

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from config import load_config

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
    "category": "سيارات",
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
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.0-flash"):
        cfg = load_config()
        self.api_key = api_key.strip() if api_key else cfg.get("gemini_api_key", "").strip()
        self.model = model or cfg.get("gemini_model", "gemini-2.0-flash")
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
        فحص الإعلان بالكامل (نص + صور) وتصنيفه وهيكلته عبر Gemini API في طلب واحد فائق السرعة
        """
        from image_safety_filter import moderate_images_locally
        nimages = ad.get("nimages", [])

        # الفحص البصري المحلي الفوري كخط دفاع أساسي (YOLO + تحليل لون البشرة والتعري والأبعاد)
        local_appr, local_rej, local_reasons = moderate_images_locally(nimages, imgs_dir)

        if not self.api_key:
            from ai_ad_enhancer import enhance_ad_with_super_ai
            enhanced = enhance_ad_with_super_ai(ad)
            
            flags = []
            if local_rej:
                flags.append("local_safety_rejected_images")
                if len(local_appr) == 0 and len(nimages) > 0:
                    is_safe = False
                    summary = f"🚫 تم استبعاد الإعلان: رصد صور أشخاص/تعري مخالفة ({len(local_rej)} صورة)"
                    rejection_reason = "صور مخالفة للضوابط الرقابية (أشخاص أو سيلفي أو تعري)"
                else:
                    is_safe = True
                    summary = f"🛡️ تم فحص الصور بنموذج الرؤية المحلي (YOLO): استبعاد {len(local_rej)} صورة مخالفة، ومطابقة {len(local_appr)} صورة نظيفة"
                    rejection_reason = None
            else:
                is_safe = True
                summary = "🛡️ مفحوص بالرؤية الحاسوبية المدمجة (YOLO) | خالي من صور الأشخاص والتعري"
                rejection_reason = None

            return {
                "is_safe": is_safe,
                "status": "safe" if is_safe else "flagged",
                "flags": flags,
                "summary": summary,
                "suggested_rejection_reason": rejection_reason,
                "approved_image_indices": local_appr,
                "rejected_image_indices": local_rej,
                "structured_ad": {
                    "category": enhanced.get("leaf_category_name", "عام"),
                    "clean_title": enhanced.get("clean_title", ""),
                    "price": enhanced.get("price_info", {"amount": None, "currency": "SYP", "is_negotiable": True}),
                    "specifications": enhanced.get("specifications", {}),
                    "clean_description": enhanced.get("clean_description", ad.get("description", ""))
                }
            }

        # التحكم بمعدل الطلبات لتجنب حد الـ 15 RPM
        elapsed_since_last = time.time() - self.last_call_time
        if elapsed_since_last < 2.0:
            time.sleep(2.0 - elapsed_since_last)

        # تجهيز محتوى الرسالة - نرسل فقط الصور التي اجتازت الفحص المحلي لتوفير التوكنز والوقت
        parts: List[Dict[str, Any]] = []

        # 1. نص الإعلان
        ad_text_prompt = f"""بيانات الإعلان للمراجعة والتدقيق:
- الوصف الأصلي:
{ad.get('description', '')}

- رقم الهاتف: {ad.get('phone_number', '')}
- المدينة والمنطقة المكتشفة: {ad.get('location_detected', '')}
- عدد الصور المرفقة: {len(nimages)}

الصور مرفقة بالتتابع (الصورة 0، الصورة 1، الصورة 2...). يرجى فحصها بدقة وكتابة النتائج بصيغة JSON فقط:"""

        parts.append({"text": ad_text_prompt})

        # 2. إرفاق الصور المصغرة التي اجتازت الفحص المحلي
        valid_indices = []
        for idx in local_appr:
            if idx < len(nimages):
                img_filename = nimages[idx]
                full_img_path = os.path.join(imgs_dir, img_filename)
                img_part = self._prepare_image_part(full_img_path)
                if img_part:
                    parts.append({"text": f"--- صورة رقم [{idx}] ---"})
                    parts.append(img_part)
                    valid_indices.append(idx)

        # 3. إرسال الطلب إلى Gemini REST API
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        
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

        try:
            self.last_call_time = time.time()
            response = requests.post(url, json=payload, timeout=25)
            
            if response.status_code == 200:
                resp_json = response.json()
                raw_text = resp_json["candidates"][0]["content"]["parts"][0]["text"].strip()
                result = json.loads(raw_text)
                
                # دمج الصور المستبعدة محلياً مع ما استبعده Gemini
                gemini_appr = result.get("approved_image_indices", [])
                gemini_rej = result.get("rejected_image_indices", [])
                
                # الصور المعتمدة النهائية هي فقط المعتمدة من الطرفين
                final_appr = [i for i in gemini_appr if i in local_appr]
                final_rej = sorted(list(set(local_rej + gemini_rej + [i for i in range(len(nimages)) if i not in final_appr])))
                
                result["approved_image_indices"] = final_appr
                result["rejected_image_indices"] = final_rej
                if len(final_appr) == 0 and len(nimages) > 0:
                    result["is_safe"] = False
                    result["suggested_rejection_reason"] = result.get("suggested_rejection_reason") or "جميع الصور مخالفة للضوابط الشرعية أو الرقابية"
                return result
            else:
                error_msg = response.text[:200]
                print(f"[!] تنبيه من Gemini API ({response.status_code}): {error_msg}")
                # محاولة احتياطية مع gemini-1.5-flash إذا كان 2.0 غير متاح
                if self.model != "gemini-1.5-flash":
                    self.model = "gemini-1.5-flash"
                    return self.moderate_and_structure_ad(ad, imgs_dir)
        except Exception as e:
            print(f"[!] خطأ في معالجة الذكاء الاصطناعي: {e}")

        # كائن افتراضي آمن محلياً في حال انقطاع الشبكة
        fallback_safe = (len(local_appr) > 0 or len(nimages) == 0)
        return {
            "is_safe": fallback_safe,
            "status": "safe" if fallback_safe else "flagged",
            "flags": ["network_fallback"] + (["local_safety_rejected_images"] if local_rej else []),
            "summary": f"🛡️ تم الفحص بالرؤية المحلية (YOLO) - تعذر اتصال Gemini: {len(local_appr)} صورة صالحة",
            "suggested_rejection_reason": "صور مخالفة للضوابط الرقابية" if not fallback_safe else None,
            "approved_image_indices": local_appr,
            "rejected_image_indices": local_rej,
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

        # إذا لم يتبق أي صورة صالحة وكان في الأصل هناك صور مرفقة، نعتبر الإعلان مرفوضاً
        if len(filtered_nimages) == 0 and len(original_nimages) > 0:
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

        processed_ad["category"] = structured.get("category", "عام")
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
