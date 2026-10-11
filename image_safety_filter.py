# -*- coding: utf-8 -*-
"""
محرك التحقق الأولي من ملفات الصور (Image File Validator)
يقوم بفحص سلامة ملفات الصور واستبعاد الملفات التالفة أو الأيقونات المصغرة
قبل إرسالها إلى محرك الرؤية الذكي (Gemini Vision API) للفحص والرقابة البصرية.
"""

import os
import sys
from PIL import Image
from typing import List, Tuple, Dict, Any, Optional

def inspect_single_image_basic(image_path: str) -> Tuple[bool, str]:
    """
    التحقق الأولي من سلامة ملف الصورة:
    - التأكد من وجود الملف وعدم تلفه.
    - استبعاد الأيقونات المصغرة جداً (أقل من 150 بكسل).
    - استبعاد الصور ذات الأبعاد الشاذة جداً (أشرطة الفواصل).
    """
    if not os.path.exists(image_path):
        return False, "file_not_found"

    try:
        if os.path.getsize(image_path) < 1000:
            return False, "file_too_small: حجم الملف صغير جداً"

        with Image.open(image_path) as img:
            w, h = img.size
            if w < 120 or h < 120:
                return False, f"too_small: أبعاد مصغرة جداً ({w}x{h})"

            aspect = max(w, h) / max(min(w, h), 1)
            if aspect > 5.0:
                return False, f"distorted_aspect: أبعاد غير طبيعية ({aspect:.1f})"

        return True, "valid"
    except Exception as e:
        return False, f"corrupted_image: {e}"

def moderate_images_locally(nimages: List[str], imgs_dir: str) -> Tuple[List[int], List[int], List[str]]:
    """
    تجهيز وفرز ملفات الصور الصالحة للإرسال إلى Gemini Vision API:
    - approved: الصور السليمة فيزيائياً الجاهزة لفحص الرؤية بالذكاء الاصطناعي
    - rejected: الملفات التالفة أو المصغرة جداً
    - reasons: أسباب الاستبعاد الأولي
    """
    valid_indices = []
    invalid_indices = []
    reasons = []

    for idx, fname in enumerate(nimages):
        full_path = os.path.join(imgs_dir, fname)
        is_ok, reason = inspect_single_image_basic(full_path)
        if is_ok:
            valid_indices.append(idx)
        else:
            invalid_indices.append(idx)
            reasons.append(f"صورة [{idx}]: {reason}")

    return valid_indices, invalid_indices, reasons
