# -*- coding: utf-8 -*-
"""
وحدة تحميل ومعالجة الصور:
1. تحميل الصور من روابط فيسبوك (مع استبعاد الفيديوهات وأي مصغرات فيديو).
2. ضغط الصورة وتصغير أبعادها (الحد الأقصى 1280px).
3. تحويل صيغة الصورة إلى WebP بجودة 80%.
4. حفظها في مجلد asstes/imgs/ وتسميتها بنظام UUID4 فريد.
"""

import os
import io
import uuid
import requests
from PIL import Image
from typing import List, Tuple, Optional

DEFAULT_IMGS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "asstes", "imgs"))

# كلمات مفتاحية لاستبعاد الفيديوهات ومصغرات الفيديو
VIDEO_FILTER_KEYWORDS = [
    "video", "v/t15.", "reel", "story_video", ".mp4", "blob:",
    "video_thumbnail", "videoplayer", "audio", "mini_video"
]

def is_valid_photo_url(url: str) -> bool:
    """التحقق من أن الرابط لصورة أصلية وليس فيديو أو رمز تعبيري"""
    if not url or not url.startswith("http"):
        return False
    url_lower = url.lower()
    for bad in VIDEO_FILTER_KEYWORDS:
        if bad in url_lower:
            return False
    return True

def download_and_convert_to_webp(
    image_url: str,
    output_dir: str = DEFAULT_IMGS_DIR,
    max_dimension: int = 1280,
    quality: int = 80
) -> Optional[str]:
    """
    تحميل صورة وضغطها وتصغيرها وحفظها بصيغة WebP باسم UUID
    :param image_url: رابط الصورة الأصلي
    :param output_dir: مجلد الحفظ (asstes/imgs)
    :param max_dimension: أقصى عرض أو ارتفاع (1280px)
    :param quality: جودة الضغط (80%)
    :return: اسم الملف المحفوظ (مثل: 1a6d4f15-f5f9-45b2-ac9a-2eefdeec887a.webp)
    """
    if not is_valid_photo_url(image_url):
        return None

    os.makedirs(output_dir, exist_ok=True)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
    }

    try:
        response = requests.get(image_url, headers=headers, timeout=12)
        if response.status_code != 200 or len(response.content) < 500:
            return None

        # فتح الصورة والتحقق من سلامتها
        image = Image.open(io.BytesIO(response.content))
        
        # تحويل الألوان إذا لزم الأمر
        if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
            # الإبقاء على الشفافية بصيغة RGBA
            image = image.convert("RGBA")
        elif image.mode != "RGB":
            image = image.convert("RGB")

        # تصغير الأبعاد مع الحفاظ على النسبة الأصلية إذا تجاوزت 1280px
        orig_width, orig_height = image.size
        if orig_width > max_dimension or orig_height > max_dimension:
            image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

        # توليد اسم فريد UUID4
        filename = f"{uuid.uuid4()}.webp"
        save_path = os.path.join(output_dir, filename)

        # حفظ الصورة بصيغة WebP بجودة 80%
        image.save(save_path, format="WEBP", quality=quality, optimize=True)
        return filename

    except Exception as e:
        # print(f"[!] خطأ أثناء معالجة الصورة: {e}")
        return None

def process_ad_images(
    image_urls: List[str],
    max_count: int = 5,
    output_dir: str = DEFAULT_IMGS_DIR
) -> Tuple[List[str], List[str]]:
    """
    معالجة صور الإعلان:
    - أخذ ماكس 5 صور فقط
    - استبعاد أي فيديوهات
    - إرجاع قائمتين: (قائمة الروابط الأصلية، قائمة أسماء ملفات الـ WebP)
    """
    download_urls = []
    webp_filenames = []

    for url in image_urls:
        if len(download_urls) >= max_count:
            break
            
        if not is_valid_photo_url(url):
            continue

        webp_name = download_and_convert_to_webp(url, output_dir=output_dir)
        if webp_name:
            download_urls.append(url)
            webp_filenames.append(webp_name)

    return download_urls, webp_filenames
