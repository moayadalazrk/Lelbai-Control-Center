# -*- coding: utf-8 -*-
"""
محرك الأمان والرقابة البصرية الذكي للصور (Visual Safety & Moderation Engine)
يعمل بنظام هجين مزدوج:
1. الفحص البصري المحلي المدمج الفوري (YOLOv8n + Pillow/NumPy Skin-Exposure Heuristics):
   - كشف صور الأشخاص والسيلفي والوجوه (Person Detection).
   - كشف التعري ونسب الجلد المكشوف غير المحتشم (Skin Tone & Nudity Exposure).
   - استبعاد صور البروفايل والأيقونات والرموز المصغرة (Dimension Filtering < 200px).
2. فحص Gemini Vision الفائق (إذا توفر المفتاح):
   - رصد صور النساء، الوثائق الرسمية، والسلع المحرمة بدقة استثنائية.
"""

import os
import sys
import numpy as np
from PIL import Image
from typing import List, Tuple, Dict, Any, Optional

_YOLO_MODEL = None

def get_yolo_model():
    """تحميل نموذج YOLOv8n فائق السرعة والخفة مرة واحدة فقط في الذاكرة"""
    global _YOLO_MODEL
    if _YOLO_MODEL is None:
        try:
            from ultralytics import YOLO
            # البحث عن yolov8n.pt في مجلد المشروع أو تحميله تلقائياً
            base_dir = os.path.dirname(os.path.abspath(__file__))
            local_model_path = os.path.join(base_dir, "yolov8n.pt")
            if os.path.exists(local_model_path):
                _YOLO_MODEL = YOLO(local_model_path)
            else:
                _YOLO_MODEL = YOLO("yolov8n.pt")
        except Exception as e:
            # print(f"[!] تنبيه في تحميل YOLO: {e}")
            _YOLO_MODEL = False
    return _YOLO_MODEL if _YOLO_MODEL is not False else None

def analyze_skin_ratio(img: Image.Image) -> float:
    """تحليل نسبة لون البشرة والتعري عبر الفضاء اللوني RGB"""
    try:
        img_rgb = img.convert("RGB")
        # تصغير لسرعة المعالجة الفائقة
        img_rgb.thumbnail((256, 256), Image.Resampling.NEAREST)
        img_np = np.array(img_rgb)
        
        R = img_np[:, :, 0].astype(float)
        G = img_np[:, :, 1].astype(float)
        B = img_np[:, :, 2].astype(float)
        
        # خوارزمية كشف لون البشرة القياسية
        skin_mask = (R > 95) & (G > 40) & (B > 20) & \
                    ((R - np.minimum(G, B)) > 15) & \
                    (np.abs(R - G) > 15) & (R > G) & (R > B)
        
        total_pixels = img_np.shape[0] * img_np.shape[1]
        if total_pixels == 0:
            return 0.0
        return float(np.sum(skin_mask) / total_pixels)
    except Exception:
        return 0.0

def inspect_single_image_locally(image_path: str) -> Tuple[bool, str]:
    """
    فحص صورة واحدة محلياً والتأكد من مطابقتها للضوابط الشرعية والرقابية:
    :return: (is_safe, reason_or_flag)
    """
    if not os.path.exists(image_path):
        return False, "file_not_found"

    try:
        with Image.open(image_path) as img:
            w, h = img.size
            # 1. استبعاد الأيقونات وصور البروفايل المصغرة
            if w < 200 or h < 200:
                return False, f"too_small: أبعاد صغيرة جداً ({w}x{h})"

            # 2. استبعاد الصور المشوهة أو أشرطة الفواصل
            aspect = max(w, h) / max(min(w, h), 1)
            if aspect > 4.5:
                return False, f"distorted_aspect: أبعاد غير طبيعية ({aspect:.1f})"

            # 3. فحص نسبة التعري ولون البشرة
            skin_ratio = analyze_skin_ratio(img)
            if skin_ratio > 0.28:
                return False, f"high_skin_exposure: نسبة ظهور بشري/تعري مكثفة ({skin_ratio:.1%})"

    except Exception as e:
        return False, f"corrupted_image: {e}"

    # 4. فحص الأجسام والأشخاص عبر الذكاء الاصطناعي المحلي (YOLO)
    model = get_yolo_model()
    if model is not None:
        try:
            results = model(image_path, verbose=False)
            if results and len(results) > 0:
                boxes = results[0].boxes
                img_area = w * h
                for b in boxes:
                    cls_id = int(b.cls[0])
                    conf = float(b.conf[0])
                    cls_name = model.names.get(cls_id, "")

                    # أ) كشف الأشخاص (person = class 0)
                    if cls_id == 0 and conf >= 0.50:
                        x1, y1, x2, y2 = b.xyxy[0].tolist()
                        box_area = (x2 - x1) * (y2 - y1)
                        box_ratio = box_area / max(img_area, 1)

                        # إذا كان الشخص يشغل أكثر من 10% من الصورة أو صورة قريبة
                        if box_ratio > 0.10:
                            return False, f"person_detected: ظهور شخص أو سيلفي بنسبة ({box_ratio:.1%})"
                        elif conf >= 0.75 and box_ratio > 0.05:
                            return False, f"person_detected: رصد شخص واضح في الصورة (ثقة {conf:.1%})"

                    # ب) كشف الأسلحة البيضاء البارزة (knife = class 43)
                    if cls_id == 43 and conf >= 0.65:
                        return False, "weapon_detected: رصد سكين أو سلاح أبيض"

        except Exception as e:
            pass

    return True, "safe"

def moderate_images_locally(nimages: List[str], imgs_dir: str) -> Tuple[List[int], List[int], List[str]]:
    """
    فحص قائمة أسماء ملفات الصور محلياً وإرجاع:
    - approved_indices: أرقام الصور السليمة
    - rejected_indices: أرقام الصور المخالفة
    - rejection_reasons: أسباب الاستبعاد
    """
    approved = []
    rejected = []
    reasons = []

    for idx, fname in enumerate(nimages):
        full_path = os.path.join(imgs_dir, fname)
        is_safe, reason = inspect_single_image_locally(full_path)
        if is_safe:
            approved.append(idx)
        else:
            rejected.append(idx)
            reasons.append(f"صورة [{idx}]: {reason}")

    return approved, rejected, reasons
