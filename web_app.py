# -*- coding: utf-8 -*-
"""
المنظومة المركزية المتكاملة وإدارة الروابط والمراجعة الشرعية (Lelbai Master Control Center)
سيرفر متكامل لإدارة الروابط وحفظها مع تاريخ آخر سحب، وعرض حالة الإعلانات بالمعايير الثلاثة (المواصفات، الشريعة، الجاهزية للنشر).
"""

import os
import sys
import json
import time
import queue
import random
import re
import shutil
import base64
import threading
import subprocess
import webbrowser
import urllib.parse
import socket
from http.server import HTTPServer, ThreadingHTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, List, Optional

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import asyncio
from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright
from syria_filter import validate_ad, normalize_text
from image_processor import process_ad_images
from gemini_processor import GeminiProcessor
from config import load_config, save_config
from publisher import publish_ad_to_website, export_ad_to_import_folder, detect_category_id, PUBLISHED_FILE
from category_classifier import (
    classify_leaf_category,
    extract_detailed_specifications,
    extract_or_generate_account_name,
    check_if_ad_already_exists,
    generate_ai_review_report
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PENDING_FILE = os.path.join(BASE_DIR, "pending_review.json")
FLAGGED_FILE = os.path.join(BASE_DIR, "flagged_ads.json")
ALL_ADS_FILE = os.path.join(BASE_DIR, "ads_syria.json")
GROUPS_DATA_FILE = os.path.join(BASE_DIR, "groups_data.json")
GROUPS_FILE = os.path.join(BASE_DIR, "groups.txt")
IMGS_DIR = os.path.join(BASE_DIR, "asstes", "imgs")

os.makedirs(IMGS_DIR, exist_ok=True)

def read_json_file(file_path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content:
                data = json.loads(content)
                if isinstance(data, list):
                    return data
    except Exception:
        pass
    return []

def write_json_file(file_path: str, data: List[Dict[str, Any]]):
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
    except Exception as e:
        print(f"[!] خطأ أثناء كتابة {file_path}: {e}")

# تقييم الإعلان بالمراحل الشاملة (الذكاء الاصطناعي الفائق، التصنيف في أصغر ابن، المواصفات، الشريعة، حساب وهمي، عدم التكرار)
def enrich_ad_status(ad: Dict[str, Any]) -> Dict[str, Any]:
    from ai_ad_enhancer import enhance_ad_with_super_ai
    # 1. تعزيز الإعلان بالذكاء الاصطناعي (عنوان نخبوي، وصف مهيكل، وأدق تصنيف أصغر فئة)
    ad_copy = enhance_ad_with_super_ai(ad)
    
    # دمج نص الإعلان الكامل للتحليل الدقيق
    full_text = f"{ad_copy.get('clean_title', '')} {ad_copy.get('clean_description') or ad_copy.get('description', '')}"

    leaf_info = {
        "category_id": ad_copy.get("leaf_category_id", 1832),
        "category_name": ad_copy.get("leaf_category_name", "ماركات أخرى"),
        "parent_name": ad_copy.get("category_hierarchy", "").split(">")[-2].strip() if ">" in ad_copy.get("category_hierarchy", "") else "سيارات للبيع",
        "category_hierarchy": ad_copy.get("category_hierarchy")
    }

    # 2. استخراج أكبر قدر ممكن من المواصفات المهيكلة
    extracted_specs = extract_detailed_specifications(full_text, leaf_info)
    current_specs = ad_copy.get("specifications") or {}
    ad_copy["specifications"] = {**extracted_specs, **current_specs}

    # 3. وضع اسم حساب معلن وهمي سوري واقعي
    if not ad_copy.get("publisher_name"):
        ad_copy["publisher_name"] = extract_or_generate_account_name(full_text)

    # 4. التحقق الصارم من عدم وجود الإعلان على الموقع من قبل
    published_db = read_json_file(PUBLISHED_FILE)
    is_duplicate, dup_reason = check_if_ad_already_exists(ad_copy, published_db, [])
    ad_copy["is_duplicate"] = is_duplicate
    ad_copy["duplicate_reason"] = dup_reason

    # 5. اكتمال المواصفات
    has_images = len(ad.get("nimages", [])) > 0
    has_desc = bool(ad.get("clean_description") or ad.get("description"))
    has_title = bool(ad.get("clean_title"))
    has_phone = bool(ad.get("phone_number"))
    has_city = bool(ad.get("id-citie") or ad.get("city_name") or ad.get("location_detected"))
    has_price = ad.get("price_info", {}).get("amount") is not None
    
    is_specs_complete = has_images and has_desc and has_title and has_phone and has_city
    
    # 6. الفحص الشرعي والرقابي
    raw_flags = ad.get("flags", [])
    flags = [f for f in raw_flags if f != "no_api_key_provided"]
    is_safe = ad.get("is_safe", True) and len(flags) == 0
    
    # 7. الجاهزية للنشر (مكتمل + سليم شرعياً + غير مكرر على الموقع)
    is_ready_to_publish = is_specs_complete and is_safe and not is_duplicate
    
    summary_text = ad.get("moderation_summary")
    if not summary_text or summary_text == "بانتظار إضافة مفتاح Gemini API للمراجعة الآلية":
        summary_text = "مطابق للشريعة وضوابط المنصة بالكامل 🟢" if is_safe else "تم رصد ملاحظات تحتاج لمراجعة"

    # 8. توليد رد وتقرير الذكاء الاصطناعي الشامل
    ai_report = generate_ai_review_report(
        ad_copy,
        leaf_info,
        ad_copy["specifications"],
        ad_copy["publisher_name"],
        is_duplicate,
        dup_reason,
        summary_text
    )
    ad_copy["ai_review"] = ai_report

    ad_copy["evaluation"] = {
        "is_specs_complete": is_specs_complete,
        "specs_details": {
            "has_images": has_images,
            "images_count": len(ad.get("nimages", [])),
            "has_desc": has_desc,
            "has_title": has_title,
            "has_phone": has_phone,
            "has_city": has_city,
            "has_price": has_price,
            "city_name": ad.get("city_name") or ad.get("location_detected") or "غير محدد",
            "sub_district_name": ad.get("sub_district_name") or "عام"
        },
        "is_sharia_compliant": is_safe,
        "sharia_details": {
            "is_safe": is_safe,
            "flags": flags,
            "summary": summary_text
        },
        "is_duplicate": is_duplicate,
        "duplicate_reason": dup_reason,
        "is_ready_to_publish": is_ready_to_publish,
        "ready_status_label": "جاهز للنشر الفوري 🚀" if is_ready_to_publish else ("مكرر على الموقع ⚠️" if is_duplicate else ("بحاجة لمراجعة أو تنقية" if is_specs_complete else "بيانات غير مكتملة"))
    }
    return ad_copy

# ==============================================================================
# محرك إدارة السحب المتوازي وتحديث تواريخ الروابط
# ==============================================================================
class ScrapingTaskManager:
    def __init__(self):
        self.is_running = False
        self.stop_requested = False
        self.start_time = 0.0
        self.total_target_ads = 0
        self.total_groups_count = 0
        self.completed_groups_count = 0
        self.total_ads_collected = 0
        self.active_tabs: Dict[int, Dict[str, Any]] = {}
        self.logs: List[str] = []
        self.lock = threading.Lock()
        self.gemini_processor = GeminiProcessor()

    def log(self, message: str):
        with self.lock:
            ts = time.strftime("%H:%M:%S")
            log_line = f"[{ts}] {message}"
            self.logs.append(log_line)
            if len(self.logs) > 200:
                self.logs.pop(0)
            print(log_line)

    def start_scraping_job(self, params: Dict[str, Any]):
        if self.is_running:
            return False, "السحب قيد التشغيل بالفعل!"

        self.is_running = True
        self.stop_requested = False
        self.start_time = time.time()
        self.active_tabs.clear()
        self.logs.clear()

        t = threading.Thread(target=self._run_parallel_scraper, args=(params,), daemon=True)
        t.start()
        return True, "تم بدء السحب بنجاح!"

    def stop_scraping_job(self):
        if not self.is_running:
            return False, "لا توجد عملية سحب نشطة."
        self.stop_requested = True
        self.log("⏹️ تم إرسال طلب إيقاف السحب...")
        return True, "جاري إيقاف السحب..."

    def _update_group_scrape_history(self, group_url: str, ads_found_count: int):
        """تحديث تاريخ وعدد الإعلانات المسحوبة للمجموعة في groups_data.json"""
        with self.lock:
            groups = read_json_file(GROUPS_DATA_FILE)
            for g in groups:
                norm_g = g.get("url", "").rstrip("/").lower()
                norm_u = group_url.rstrip("/").lower()
                if norm_g == norm_u or norm_g in norm_u or norm_u in norm_g:
                    g["last_scraped_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                    g["last_ads_count"] = ads_found_count
                    g["total_ads_count"] = g.get("total_ads_count", 0) + ads_found_count
                    g["status"] = "مكتمل"
                    break
            write_json_file(GROUPS_DATA_FILE, groups)

    def _run_parallel_scraper(self, params: Dict[str, Any]):
        try:
            asyncio.run(self._async_parallel_scraper(params))
        except Exception as e:
            self.log(f"❌ خطأ عام أثناء السحب: {e}")
        finally:
            self.is_running = False
            self.active_tabs.clear()

    async def _async_parallel_scraper(self, params: Dict[str, Any]):
        urls = params.get("groups", [])
        if not urls:
            self.log("❌ لم يتم تحديد أي روابط مجموعات للسحب!")
            return

        concurrent_tabs = int(params.get("concurrent_tabs", 4))
        concurrent_tabs = max(1, min(concurrent_tabs, 6))
        max_ads_per_group = int(params.get("max_ads_per_group", 100))
        timeout_seconds = int(params.get("timeout_seconds", 60))

        self.total_groups_count = len(urls)
        self.completed_groups_count = 0
        self.total_target_ads = self.total_groups_count * max_ads_per_group

        existing_ads = read_json_file(ALL_ADS_FILE)
        self.total_ads_collected = len(existing_ads)
        seen_signatures = {f"{a.get('phone_number')}_{a.get('description', '')[:50]}" for a in existing_ads}

        self.log(f"🚀 بدء محرك السحب المتوازي: {len(urls)} مجموعات | {concurrent_tabs} صفحات متزامنة حقيقية ⚡")

        user_data_dir = os.path.join(BASE_DIR, "browser_session")
        os.makedirs(user_data_dir, exist_ok=True)

        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=False,
                viewport={"width": 1280, "height": 850},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                locale="ar-SY",
                timezone_id="Asia/Damascus",
                args=[
                    "--start-maximized",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-infobars",
                    "--no-sandbox",
                    "--disable-background-timer-throttling",
                    "--disable-backgrounding-occluded-windows",
                    "--disable-renderer-backgrounding",
                    "--disable-features=CalculateNativeWinOcclusion",
                    "--disable-features=IntensiveWakeUpThrottling"
                ]
            )

            await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")

            q = asyncio.Queue()
            for idx, u in enumerate(urls, 1):
                q.put_nowait((idx, u))

            async def tab_worker(tab_id: int):
                # إذا كانت الصفحة الأولى مفتوحة نستخدمها، عدا ذلك نفتح تبويب جديد
                if tab_id == 0 and context.pages:
                    page = context.pages[0]
                else:
                    page = await context.new_page()

                while not q.empty() and not self.stop_requested:
                    try:
                        group_idx, group_url = q.get_nowait()
                    except asyncio.QueueEmpty:
                        break

                    with self.lock:
                        self.active_tabs[tab_id] = {
                            "group_idx": group_idx,
                            "url": group_url,
                            "ads_collected": 0,
                            "status": "جاري التحميل..."
                        }

                    self.log(f"[تبويب {tab_id+1}] 🔗 فتح المجموعة [{group_idx}/{self.total_groups_count}]: {group_url}")

                    try:
                        await page.goto(group_url, wait_until="domcontentloaded", timeout=45000)
                    except Exception:
                        pass

                    await asyncio.sleep(2.5)

                    cur_url = page.url
                    group_match = re.search(r'(https?://(?:www\.)?facebook\.com/groups/[0-9a-zA-Z._-]+)', cur_url)
                    if group_match and ("/permalink/" in cur_url or "/posts/" in cur_url):
                        try:
                            await page.goto(group_match.group(1) + "/", wait_until="domcontentloaded", timeout=25000)
                            await asyncio.sleep(2)
                        except Exception:
                            pass

                    scroll_attempts = 0
                    group_ads_count = 0
                    last_ad_time = time.time()

                    while scroll_attempts < 250 and group_ads_count < max_ads_per_group and not self.stop_requested:
                        scroll_attempts += 1

                        # تحديث حالة التبويب الحية ليراها المستخدم بالثواني
                        with self.lock:
                            if group_ads_count > 0:
                                self.active_tabs[tab_id]["status"] = f"سحب ({group_ads_count}/{max_ads_per_group})"
                            else:
                                self.active_tabs[tab_id]["status"] = f"فحص المنشورات... ({scroll_attempts})"

                        # فحص إذا تم فتح صفحة منشور منفصلة (Permalink) والعودة فوراً لخلاصة المجموعة
                        try:
                            cur_tab_url = page.url
                            if "/permalink/" in cur_tab_url or "/posts/" in cur_tab_url:
                                m = re.search(r'(https?://(?:www\.)?facebook\.com/groups/[0-9a-zA-Z._-]+)', cur_tab_url)
                                clean_target = (m.group(1) + "/") if m else group_url
                                await page.goto(clean_target, wait_until="domcontentloaded", timeout=20000)
                                await asyncio.sleep(2)
                        except Exception:
                            pass

                        # 1. إغلاق النوافذ المنبثقة ومربعات تسجيل الدخول ومنشورات الـ Dialog المعيقة للتمرير
                        try:
                            await page.keyboard.press("Escape")
                            await page.evaluate("""() => {
                                const closeSelectors = [
                                    "div[aria-label='إغلاق']", "div[aria-label='Close']",
                                    "div[aria-label='Close post']", "div[aria-label='إغلاق المنشور']",
                                    "div[role='dialog'] div[aria-label='إغلاق']", "div[role='dialog'] div[aria-label='Close']",
                                    "div[role='dialog'] div[role='button']", "div[aria-label='X']",
                                    "div[role='dialog'] button"
                                ];
                                for (const sel of closeSelectors) {
                                    document.querySelectorAll(sel).forEach(b => {
                                        try { b.click(); } catch(e){}
                                    });
                                }
                            }""")
                        except Exception:
                            pass

                        # 2. توسيع أزرار 'عرض المزيد' في نص المنشور فقط وتخطي الروابط التي تفتح النوافذ
                        try:
                            await page.evaluate("""() => {
                                const elements = document.querySelectorAll("div[role='button'], span, strong");
                                for (const el of elements) {
                                    if (el.closest("a")) continue; // تخطي الروابط تماماً لتجنب فتح المنشور بنافذة منبثقة
                                    const txt = (el.textContent || '').trim();
                                    if (txt === 'عرض المزيد' || txt === 'See more' || txt === 'See More' || txt === '...عرض المزيد') {
                                        if (el.children.length <= 1) {
                                            try { el.click(); } catch(e){}
                                        }
                                    }
                                }
                            }""")
                        except Exception:
                            pass

                        # 3. استخراج المنشورات من الصفحة
                        try:
                            raw_posts = await page.evaluate("""() => {
                                let containers = document.querySelectorAll("div[role='feed'] > div, div[data-pagelet*='FeedUnit'], div[role='article']");
                                if (!containers || containers.length === 0) {
                                    containers = document.querySelectorAll("div[dir='auto']");
                                }
                                const extracted = [];
                                for (const c of containers) {
                                    let text = '';
                                    const msgEl = c.querySelector("div[data-ad-preview='message'], div[data-ad-comet-preview='message']");
                                    if (msgEl) {
                                        text = (msgEl.innerText || msgEl.textContent || '').trim();
                                    } else {
                                        const candidates = Array.from(c.querySelectorAll("div[dir='auto']")).filter(el => {
                                            if (el.closest("h2, h3, h4, [role='button'], a[role='link']")) return false;
                                            return (el.innerText || '').length > 20;
                                        });
                                        if (candidates.length > 0) {
                                            candidates.sort((a, b) => (b.innerText || '').length - (a.innerText || '').length);
                                            text = (candidates[0].innerText || candidates[0].textContent || '').trim();
                                        } else {
                                            text = (c.innerText || c.textContent || '').trim();
                                        }
                                    }

                                    if (!text || text.length < 15) continue;

                                    const images = [];
                                    const imgEls = c.querySelectorAll("img");
                                    for (const img of imgEls) {
                                        const src = img.src || img.getAttribute('src');
                                        if (src && src.startsWith('http')) {
                                            const sLow = src.toLowerCase();
                                            if (!sLow.includes('emoji') && !sLow.includes('rsrc.php') && !sLow.includes('icon') && !sLow.includes('static') && !sLow.includes('avatar') && !sLow.includes('profile_pic') && !sLow.includes('spacer.gif')) {
                                                if (!images.includes(src)) images.push(src);
                                            }
                                        }
                                    }

                                    let link = '';
                                    const aTags = c.querySelectorAll("a[href]");
                                    for (const a of aTags) {
                                        const href = a.href || a.getAttribute('href') || '';
                                        if (href.includes('/posts/') || href.includes('/permalink/') || href.includes('story_fbid')) {
                                            link = href.split('?')[0];
                                            break;
                                        }
                                    }

                                    extracted.push({ text, images, link });
                                }
                                return extracted;
                            }""")
                        except Exception:
                            raw_posts = []

                        # فحص وتدقيق كل إعلان مسحوب
                        for p_data in raw_posts:
                            if self.stop_requested:
                                break

                            text_content = p_data.get("text", "")
                            if not text_content or len(text_content) < 15:
                                continue

                            raw_images = p_data.get("images", [])
                            if not raw_images or len(raw_images) == 0:
                                continue

                            validation = validate_ad(text_content)
                            if not validation["is_valid"]:
                                continue

                            clean_desc = validation.get("cleaned_description", text_content)
                            primary_phone = validation["phones"][0] if validation["phones"] else ""
                            sig = f"{primary_phone}_{clean_desc[:50]}"

                            with self.lock:
                                if sig in seen_signatures:
                                    continue
                                seen_signatures.add(sig)

                                # التحقق الحاسم من عدم وجود الإعلان مسبقاً على الموقع
                                published_db = read_json_file(PUBLISHED_FILE)
                                is_dup, dup_msg = check_if_ad_already_exists({"phone_number": primary_phone, "ad_url": p_data.get("link"), "description": clean_desc}, published_db, [])
                                if is_dup:
                                    self.log(f"[🔄 استبعاد إعلان مكرر]: موجود مسبقاً على الموقع ({primary_phone})")
                                    continue

                            # تنزيل الصور ومعالجتها إلى WebP بشكل غير حاجب للمهام الأخرى
                            images_download, nimages = await asyncio.to_thread(process_ad_images, raw_images, 5)
                            if not nimages or len(nimages) == 0:
                                continue

                            ad_dict = {
                                "ad_url": p_data.get("link") or group_url,
                                "phone_number": primary_phone,
                                "description": clean_desc,
                                "images dowlod": images_download,
                                "nimages": nimages,
                                "id-citie": validation.get("id-citie"),
                                "id-sub_districts": validation.get("id-sub_districts"),
                                "city_name": validation.get("city_name"),
                                "sub_district_name": validation.get("sub_district_name"),
                                "location_detected": validation.get("location_detected"),
                                "extracted_at": time.strftime("%Y-%m-%d %H:%M:%S")
                            }

                            # فحص وهيكلة الذكاء الاصطناعي بشكل غير حاجب
                            processed_ad = await asyncio.to_thread(self.gemini_processor.process_and_clean_ad, ad_dict, IMGS_DIR)

                            if not processed_ad.get("is_safe", True):
                                self.log(f"[🚫 استبعاد إعلان مخالف]: {processed_ad.get('moderation_summary')}")
                                with self.lock:
                                    flagged = read_json_file(FLAGGED_FILE)
                                    flagged.append(processed_ad)
                                    write_json_file(FLAGGED_FILE, flagged)
                                continue

                            # إثراء الإعلان بالتصنيف في أصغر فئة، المواصفات، حساب وهمي، وفحص التكرار، وتقرير الذكاء الاصطناعي
                            processed_ad = enrich_ad_status(processed_ad)

                            # حفظ الإعلان المعتمد
                            with self.lock:
                                pending = read_json_file(PENDING_FILE)
                                pending.append(processed_ad)
                                write_json_file(PENDING_FILE, pending)

                                all_ads = read_json_file(ALL_ADS_FILE)
                                all_ads.append(processed_ad)
                                write_json_file(ALL_ADS_FILE, all_ads)

                                group_ads_count += 1
                                self.total_ads_collected += 1
                                last_ad_time = time.time()
                                self.active_tabs[tab_id]["ads_collected"] = group_ads_count
                                self.active_tabs[tab_id]["status"] = f"سحب ({group_ads_count}/{max_ads_per_group})"

                            cat_label = processed_ad.get('category_hierarchy') or processed_ad.get('category')
                            pub_name = processed_ad.get('publisher_name', 'معلن سوري')
                            self.log(f"[تبويب {tab_id+1}] 🟢 إعلان معتمد [{cat_label}]: {processed_ad.get('clean_title')} (المعلن: {pub_name} | هاتف: {primary_phone})")

                            if group_ads_count >= max_ads_per_group:
                                break

                        # فحص مهلة عدم النشاط للتخطي التلقائي
                        if (time.time() - last_ad_time) >= timeout_seconds:
                            self.log(f"[تبويب {tab_id+1}] ⏱️ مهلة عدم النشاط ({timeout_seconds} ثانية) انتهت للمجموعة [{group_idx}]. الانتقال للتالية...")
                            break

                        # التمرير الفعال المضمون (يعمل في كافة التبويبات المتزامنة والخلفية والنشطة)
                        try:
                            await page.evaluate("""() => {
                                window.scrollBy(0, 1600);
                                if (document.scrollingElement) {
                                    document.scrollingElement.scrollTop += 1600;
                                }
                                window.dispatchEvent(new Event('scroll'));
                            }""")
                            await page.mouse.wheel(0, 1600)
                        except Exception:
                            pass
                        await asyncio.sleep(random.uniform(0.8, 1.4))

                    with self.lock:
                        self.completed_groups_count += 1

                    self._update_group_scrape_history(group_url, group_ads_count)
                    self.log(f"[تبويب {tab_id+1}] ✔️ اكتملت المجموعة [{group_idx}]. الإعلانات المستخرجة: {group_ads_count}")
                    q.task_done()

                try:
                    await page.close()
                except Exception:
                    pass

            actual_tabs = min(concurrent_tabs, len(urls))
            self.log(f"⚡ جاري إطلاق {actual_tabs} تبويبات متزامنة في المتصفح...")
            await asyncio.gather(*[tab_worker(i) for i in range(actual_tabs)])

            await context.close()

        self.log(f"🎉 تم الانتهاء من كافة المهام! إجمالي الإعلانات الصالحة: {self.total_ads_collected}")

task_manager = ScrapingTaskManager()

# ==============================================================================
# واجهة الويب الشاملة (Unified 3-Pillar HTML Control Center)
# ==============================================================================
HTML_PAGE = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>لوحة التحكم المركزية وسحب الإعلانات 🇸🇾 | للبيع - Lelbai</title>
  <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800;900&display=swap" rel="stylesheet">
  <style>
    :root {
      --primary: #2563eb;
      --primary-hover: #1d4ed8;
      --success: #10b981;
      --success-dark: #059669;
      --danger: #ef4444;
      --warning: #f59e0b;
      --purple: #8b5cf6;
      --bg: #0b1120;
      --card-bg: #1e293b;
      --card-inner: #0f172a;
      --border: #334155;
      --text: #f8fafc;
      --text-muted: #94a3b8;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Tajawal', sans-serif; }
    body { background: var(--bg); color: var(--text); padding: 20px; line-height: 1.6; }
    
    .navbar {
      display: flex; justify-content: space-between; align-items: center;
      background: var(--card-bg); padding: 16px 28px; border-radius: 16px;
      border: 1px solid var(--border); margin-bottom: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    .brand { font-size: 22px; font-weight: 900; color: #60a5fa; display: flex; align-items: center; gap: 10px; }
    
    .nav-tabs { display: flex; gap: 8px; flex-wrap: wrap; }
    .nav-btn {
      padding: 10px 18px; border-radius: 10px; border: 1px solid transparent;
      background: transparent; color: var(--text-muted); font-weight: 700; font-size: 14px;
      cursor: pointer; transition: all 0.2s; display: flex; align-items: center; gap: 8px;
    }
    .nav-btn.active { background: var(--primary); color: #fff; border-color: var(--primary); box-shadow: 0 4px 12px rgba(37,99,235,0.4); }
    .nav-btn:hover:not(.active) { background: #334155; color: #fff; }

    .tab-content { display: none; }
    .tab-content.active { display: block; }

    .card {
      background: var(--card-bg); border-radius: 16px; border: 1px solid var(--border);
      padding: 22px; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .card-title { font-size: 18px; font-weight: 800; color: #93c5fd; margin-bottom: 16px; display: flex; align-items: center; justify-content: space-between; }

    .form-group { margin-bottom: 14px; }
    .form-group label { display: block; font-size: 13px; font-weight: 700; color: var(--text-muted); margin-bottom: 6px; }
    .form-control {
      width: 100%; padding: 10px 14px; border-radius: 10px; background: var(--card-inner);
      border: 1px solid var(--border); color: #fff; font-size: 14px; outline: none; transition: 0.2s;
    }
    .form-control:focus { border-color: var(--primary); }
    textarea.form-control { resize: vertical; min-height: 90px; }

    .btn {
      padding: 10px 20px; border-radius: 10px; font-weight: 800; font-size: 14px;
      cursor: pointer; border: none; transition: all 0.2s; display: inline-flex; align-items: center; gap: 8px;
    }
    .btn-sm { padding: 6px 12px; font-size: 12px; border-radius: 8px; }
    .btn-primary { background: var(--primary); color: #fff; }
    .btn-primary:hover { background: var(--primary-hover); transform: translateY(-1px); }
    .btn-success { background: var(--success); color: #fff; }
    .btn-success:hover { background: var(--success-dark); transform: translateY(-1px); }
    .btn-danger { background: var(--danger); color: #fff; }
    .btn-danger:hover { background: #dc2626; }
    .btn-purple { background: var(--purple); color: #fff; }
    .btn-purple:hover { background: #7c3aed; }
    .btn-outline { background: transparent; border: 1px solid var(--border); color: #fff; }
    .btn-outline:hover { background: #334155; }

    /* Stats Grid */
    .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px; margin-bottom: 20px; }
    .stat-card {
      background: var(--card-inner); padding: 16px; border-radius: 14px; border: 1px solid var(--border);
      display: flex; align-items: center; gap: 15px;
    }
    .stat-icon {
      width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center;
      font-size: 22px; background: rgba(59, 130, 246, 0.15); color: #60a5fa;
    }
    .stat-info .val { font-size: 24px; font-weight: 900; color: #f8fafc; }
    .stat-info .lbl { font-size: 12px; font-weight: 700; color: var(--text-muted); }

    /* Groups Table */
    .table-container { overflow-x: auto; background: var(--card-inner); border-radius: 12px; border: 1px solid var(--border); }
    table { width: 100%; border-collapse: collapse; text-align: right; font-size: 13px; }
    th { background: #1e293b; color: #94a3b8; padding: 12px 16px; font-weight: 800; border-bottom: 1px solid var(--border); }
    td { padding: 12px 16px; border-bottom: 1px solid var(--border); vertical-align: middle; }
    tr:hover td { background: rgba(255,255,255,0.02); }
    .badge { padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 800; display: inline-flex; align-items: center; gap: 4px; }
    .badge-success { background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
    .badge-warning { background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
    .badge-info { background: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); }

    /* 3-Pillars Ad Card */
    .ads-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(420px, 1fr)); gap: 20px; }
    .ad-card {
      background: var(--card-bg); border-radius: 16px; border: 1px solid var(--border);
      overflow: hidden; display: flex; flex-direction: column; transition: all 0.2s;
    }
    .ad-card:hover { border-color: #60a5fa; box-shadow: 0 8px 25px rgba(0,0,0,0.4); }
    
    .ad-gallery { height: 230px; background: #000; position: relative; display: flex; align-items: center; justify-content: center; }
    .ad-gallery img { max-width: 100%; max-height: 100%; object-fit: contain; }
    .ad-thumbs {
      position: absolute; bottom: 0; left: 0; right: 0; display: flex; gap: 5px;
      padding: 6px; background: rgba(0,0,0,0.7); overflow-x: auto;
    }
    .ad-thumb { width: 42px; height: 42px; border-radius: 6px; object-fit: cover; cursor: pointer; border: 2px solid transparent; opacity: 0.7; }
    .ad-thumb.active { border-color: #38bdf8; opacity: 1; }

    .ad-body { padding: 18px; display: flex; flex-direction: column; gap: 12px; flex: 1; }

    /* 3 Pillars Box */
    .verification-box {
      background: var(--card-inner); border-radius: 12px; border: 1px solid var(--border);
      padding: 12px; display: flex; flex-direction: column; gap: 8px;
    }
    .pillar-row {
      display: flex; justify-content: space-between; align-items: center; font-size: 12px; font-weight: 700;
      padding-bottom: 6px; border-bottom: 1px solid rgba(255,255,255,0.05);
    }
    .pillar-row:last-child { border-bottom: none; padding-bottom: 0; }
    .pillar-label { display: flex; align-items: center; gap: 6px; color: var(--text-muted); }

    .ad-title-input {
      background: var(--card-inner); border: 1px solid var(--border); color: #fff;
      padding: 8px 12px; border-radius: 8px; font-size: 15px; font-weight: 800; width: 100%;
    }
    .ad-desc-box {
      background: var(--card-inner); border: 1px solid var(--border); border-radius: 8px;
      padding: 10px; font-size: 12px; color: #cbd5e1; max-height: 100px; overflow-y: auto; white-space: pre-line;
    }

    .modal {
      display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.75);
      align-items: center; justify-content: center; z-index: 1000; padding: 20px;
    }
    .modal-content {
      background: var(--card-bg); border-radius: 16px; border: 1px solid var(--border);
      padding: 24px; width: 100%; max-width: 550px; display: flex; flex-direction: column; gap: 14px;
    }
  </style>
</head>
<body>

  <div class="navbar">
    <div class="brand">🚀 منصة إعلانات سوريا 🇸🇾 <span style="font-size:13px; color:var(--text-muted); font-weight:400;">(لوحة التحكم وسحب المجموعات والنشر)</span></div>
    <div style="display:flex; align-items:center; gap:12px;">
      <div id="serverStatusBadge" class="badge badge-warning" style="font-size:12px; padding:6px 14px; font-weight:700;">⏳ فحص الاتصال...</div>
      <div class="nav-tabs">
        <button class="nav-btn active" onclick="switchTab('tab-links', this)">🔗 إدارة الروابط وتاريخ السحب</button>
        <button class="nav-btn" onclick="switchTab('tab-scraper', this)">⚡ تشغيل السحب المتوازي</button>
        <button class="nav-btn" onclick="switchTab('tab-review', this)">📦 مراجعة ونشر الإعلانات (<span id="badgePending">0</span>)</button>
        <button class="nav-btn" onclick="switchTab('tab-settings', this)">⚙️ الإعدادات والـ API</button>
      </div>
    </div>
  </div>

  <!-- تنبيه حالة السيرفر في حال فتح الملف كـ file:// أو السيرفر غير متصل -->
  <div id="serverAlertBanner" style="display:none; background:#450a0a; color:#fecaca; border:1px solid #dc2626; border-radius:14px; padding:16px 20px; margin-bottom:20px; box-shadow:0 4px 20px rgba(220,38,38,0.25); align-items:center; justify-content:space-between; flex-wrap:wrap; gap:14px;">
    <div style="display:flex; align-items:center; gap:14px;">
      <span style="font-size:28px;">⚠️</span>
      <div>
        <div style="font-weight:900; font-size:16px; color:#fee2e2;">سيرفر لوحة التحكم المحلي غير متصل (http://localhost:5000)</div>
        <div style="font-size:13px; color:#fca5a5; margin-top:2px;">
          لقد قمت بفتح صفحة الويب مباشرة دون تشغيل السيرفر. لتفعيل سحب الإعلانات وحفظ الروابط والتواصل مع الذكاء الاصطناعي، يرجى تشغيل <b>start_app.bat</b> أو <b>Lelbai_Control_Center.exe</b> أولاً.
        </div>
      </div>
    </div>
    <div style="display:flex; gap:10px; align-items:center; flex-wrap:wrap;">
      <a href="start_app.bat" download class="btn btn-success btn-sm" style="white-space:nowrap; padding:10px 18px; font-weight:800; text-decoration:none; display:inline-flex; align-items:center; gap:6px;">🚀 تشغيل السيرفر الآن (start_app.bat)</a>
      <button class="btn btn-warning btn-sm" onclick="checkServerConnection(true)" style="white-space:nowrap; padding:10px 18px; font-weight:800;">🔄 إعادة فحص الاتصال</button>
    </div>
  </div>

  <!-- الإحصائيات العلوية العامة -->
  <div class="stats-grid">
    <div class="stat-card">
      <div class="stat-icon">🔗</div>
      <div class="stat-info"><div class="val" id="stTotalLinks">0</div><div class="lbl">إجمالي الروابط المحفوظة</div></div>
    </div>
    <div class="stat-card">
      <div class="stat-icon" style="background:rgba(16,185,129,0.15); color:#34d399;">🚀</div>
      <div class="stat-info"><div class="val" id="stReadyAds" style="color:#34d399;">0</div><div class="lbl">إعلانات جاهزة للنشر الفوري</div></div>
    </div>
    <div class="stat-card">
      <div class="stat-icon" style="background:rgba(139,92,246,0.15); color:#a78bfa;">✔️</div>
      <div class="stat-info"><div class="val" id="stPublishedAds" style="color:#a78bfa;">0</div><div class="lbl">إعلانات تم نشرها للموقع</div></div>
    </div>
    <div class="stat-card">
      <div class="stat-icon" style="background:rgba(239,68,68,0.15); color:#f87171;">🚫</div>
      <div class="stat-info"><div class="val" id="stFlaggedAds" style="color:#f87171;">0</div><div class="lbl">إعلانات مخالفة تم استبعادها</div></div>
    </div>
  </div>

  <!-- تبويب 1: إدارة الروابط وتاريخ السحب -->
  <div class="tab-content active" id="tab-links">
    <div class="card">
      <div class="card-title">
        <span>📋 قائمة الروابط المحفوظة ومتابعة آخر عمليات السحب</span>
        <button class="btn btn-primary btn-sm" onclick="openAddGroupModal()">➕ إضافة رابط مجموعة جديد</button>
      </div>

      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>اسم المجموعة / الرابط</th>
              <th>القسم</th>
              <th>🕒 آخر مرة سحبت منه</th>
              <th>📊 آخر سحب</th>
              <th>إجمالي الإعلانات</th>
              <th>الحالة</th>
              <th>إجراءات</th>
            </tr>
          </thead>
          <tbody id="groupsTableBody">
            <!-- يتم الملء عبر JavaScript -->
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- تبويب 2: تشغيل السحب المتوازي والمتابعة -->
  <div class="tab-content" id="tab-scraper">
    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:20px;">
      
      <div class="card">
        <div class="card-title">⚡ بدء السحب المتوازي السريع</div>
        
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:12px;">
          <div class="form-group">
            <label>⚡ عدد التبويبات المتزامنة (1 إلى 5):</label>
            <input type="number" class="form-control" id="inpConcurrent" value="4" min="1" max="5">
          </div>
          <div class="form-group">
            <label>🎯 المطلوب من كل مجموعة:</label>
            <input type="number" class="form-control" id="inpMaxAds" value="100" min="5" max="500">
          </div>
        </div>

        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:12px;">
          <div class="form-group">
            <label>⏱️ مهلة الانتظار قبل التخطي (ثانية):</label>
            <input type="number" class="form-control" id="inpTimeout" value="60" min="20" max="180">
          </div>
          <div class="form-group">
            <label>📁 مجلد استيراد الموقع:</label>
            <input type="text" class="form-control" id="inpImportDir" value="C:\\Users\\mwyda\\Desktop\\إعلانات_للاستيراد">
          </div>
        </div>

        <div style="display:flex; gap:10px; margin-top:15px;">
          <button class="btn btn-success" id="btnStartScraping" onclick="startAllScraping()">🚀 تشغيل السحب لكافة المجموعات</button>
          <button class="btn btn-danger" id="btnStopScraping" onclick="stopAllScraping()" style="display:none;">⏹️ إيقاف السحب</button>
          <button class="btn btn-outline" onclick="openLoginBrowser()">🔐 تسجيل دخول فيسبوك</button>
        </div>
      </div>

      <div class="card">
        <div class="card-title">📊 حالة التبويبات والسجلات الحية</div>
        <div id="activeTabsLiveList" style="display:flex; flex-direction:column; gap:8px; margin-bottom:12px;">
          <div style="font-size:12px; color:var(--text-muted); text-align:center; padding:10px;">لا توجد تبويبات نشطة حالياً</div>
        </div>
        <div id="liveLogsContainer" style="background:#000; color:#4ade80; font-family:monospace; padding:10px; border-radius:8px; height:150px; overflow-y:auto; font-size:11px;">جاهز لبدء السحب...</div>
      </div>

    </div>
  </div>

  <!-- تبويب 3: مراجعة ونشر الإعلانات (المراحل الثلاث) -->
  <div class="tab-content" id="tab-review">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; flex-wrap:wrap; gap:12px;">
      <div style="display:flex; gap:10px; align-items:center;">
        <span style="font-weight:800; color:#60a5fa;">تصفية الإعلانات:</span>
        <button class="btn btn-sm btn-outline active" onclick="filterAds('all', this)">الكل</button>
        <button class="btn btn-sm btn-outline" onclick="filterAds('ready', this)">🚀 الجاهز للنشر فقط</button>
        <button class="btn btn-sm btn-outline" onclick="filterAds('review', this)">⚠️ بحاجة لمراجعة</button>
      </div>
      <div style="display:flex; gap:10px;">
        <button class="btn btn-success" onclick="bulkPublishReady()">⚡ نشر كافة الإعلانات الجاهزة لمجلد الاستيراد</button>
        <button class="btn btn-outline" onclick="loadAllAds()">🔄 تحديث</button>
      </div>
    </div>

    <div class="ads-grid" id="adsCardsGrid">
      <!-- يتم عرض بطاقات الإعلانات بالمراحل الثلاث عبر JavaScript -->
    </div>
  </div>

  <!-- تبويب 4: الإعدادات -->
  <div class="tab-content" id="tab-settings">
    <div class="card" style="max-width:650px; margin:0 auto;">
      <div class="card-title">🔑 إعدادات المفاتيح والربط</div>
      
      <div class="form-group">
        <label>مفتاح Gemini API المجاني (للتدقيق والهيكلة):</label>
        <input type="password" class="form-control" id="setGeminiKey" placeholder="AIzaSy...">
      </div>

      <div class="form-group">
        <label>رابط API الموقع (للنشر المباشر عبر الشبكة إن وُجد):</label>
        <input type="text" class="form-control" id="setWebUrl" placeholder="https://example.com/api/ads">
      </div>

      <div class="form-group">
        <label>مفتاح توثيق الموقع (Authorization Token):</label>
        <input type="password" class="form-control" id="setWebKey" placeholder="Bearer Token...">
      </div>

      <button class="btn btn-primary" onclick="saveSettings()">💾 حفظ الإعدادات</button>
    </div>
  </div>

  <!-- Modal إضافة مجموعة -->
  <div class="modal" id="addGroupModal">
    <div class="modal-content">
      <div style="font-size:18px; font-weight:800; color:#60a5fa;">➕ إضافة رابط سحب جديد</div>
      
      <div class="form-group">
        <label>اسم المجموعة / الصفحة:</label>
        <input type="text" class="form-control" id="mGrpName" placeholder="مثال: سوق سيارات دمشق">
      </div>

      <div class="form-group">
        <label>رابط المجموعة (فيسبوك):</label>
        <input type="text" class="form-control" id="mGrpUrl" placeholder="https://www.facebook.com/groups/...">
      </div>

      <div class="form-group">
        <label>القسم / التصنيف:</label>
        <select class="form-control" id="mGrpCat">
          <option value="السيارات">السيارات والدراجات</option>
          <option value="العقارات">العقارات</option>
          <option value="الموبايلات والإلكترونيات">الموبايلات والإلكترونيات</option>
          <option value="الطاقة البديلة">الطاقة البديلة والكهرباء</option>
          <option value="الأثاث والمنزل">الأثاث والمنزل</option>
          <option value="المواشي والحيوانات">المواشي والحيوانات</option>
          <option value="الوظائف والخدمات">الوظائف والخدمات</option>
          <option value="عام">أخرى / عام</option>
        </select>
      </div>

      <div style="display:flex; justify-content:flex-end; gap:10px; margin-top:10px;">
        <button class="btn btn-outline" onclick="closeAddGroupModal()">إلغاء</button>
        <button class="btn btn-primary" onclick="saveNewGroup()">حفظ الرابط</button>
      </div>
    </div>
  </div>

  <script>
    // تحديد مسار الـ API تلقائياً للعمل المباشر سواء فُتح من السيرفر أو كملف HTML محلي
    const API_BASE = (window.location.protocol === 'file:' || !window.location.port || window.location.port !== '5000') 
      ? 'http://localhost:5000' 
      : '';

    let groupsData = [];
    let adsData = [];
    let currentFilter = 'all';
    let isServerConnected = false;

    function updateServerStatusBadge(online) {
      isServerConnected = online;
      const badge = document.getElementById('serverStatusBadge');
      const banner = document.getElementById('serverAlertBanner');
      if (online) {
        if (badge) {
          badge.className = 'badge badge-success';
          badge.innerHTML = '🟢 السيرفر متصل (5000)';
        }
        if (banner) banner.style.display = 'none';
      } else {
        if (badge) {
          badge.className = 'badge badge-danger';
          badge.innerHTML = '🔴 السيرفر غير متصل';
        }
        if (banner) banner.style.display = 'flex';
      }
    }

    async function apiFetch(endpoint, options = {}) {
      const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;
      try {
        const res = await fetch(url, options);
        updateServerStatusBadge(true);
        return res;
      } catch (err) {
        updateServerStatusBadge(false);
        console.warn(`[Connection Info] Unable to connect to ${url}`);
        throw err;
      }
    }

    function switchTab(tabId, el) {
      document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
      document.getElementById(tabId).classList.add('active');
      el.classList.add('active');
      if (tabId === 'tab-links') loadGroups();
      if (tabId === 'tab-review') loadAllAds();
    }

    async function init() {
      await checkServerConnection(false);
      // فحص دوري تلقائي لإعادة الاتصال ومتابعة السحب
      setInterval(async () => {
        if (!isServerConnected) {
          try {
            const res = await apiFetch('/api/config');
            if (res.ok) {
              await checkServerConnection(false);
            }
          } catch (e) {}
        } else {
          pollScraperStatus();
        }
      }, 2500);
    }

    async function checkServerConnection(isManual = false) {
      try {
        const testRes = await apiFetch('/api/config');
        if (!testRes.ok) throw new Error("Server offline");

        await loadConfig();
        await loadGroups();
        await loadAllAds();
        pollScraperStatus();
        updateServerStatusBadge(true);
        if (isManual) alert("تم الاتصال بالسيرفر بنجاح! 🟢");
      } catch (e) {
        updateServerStatusBadge(false);
        if (isManual) alert("تعذر الاتصال بالسيرفر! يرجى تشغيل start_app.bat أو Lelbai_Control_Center.exe أولاً.");
      }
    }

    async function loadConfig() {
      try {
        const res = await apiFetch('/api/config');
        const cfg = await res.json();
        document.getElementById('setGeminiKey').value = cfg.gemini_api_key || '';
        document.getElementById('setWebUrl').value = cfg.website_api_url || '';
        document.getElementById('setWebKey').value = cfg.website_api_key || '';
      } catch (e) {}
    }

    async function loadGroups() {
      try {
        const res = await apiFetch('/api/groups');
        groupsData = await res.json();
        document.getElementById('stTotalLinks').innerText = groupsData.length;

        const tbody = document.getElementById('groupsTableBody');
        if (groupsData.length === 0) {
          tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:30px; color:var(--text-muted);">لا توجد روابط محفوظة حالياً. اضغط "إضافة رابط جديد" للبدء.</td></tr>`;
          return;
        }

        tbody.innerHTML = groupsData.map((g, idx) => `
          <tr>
            <td style="font-weight:700;">${idx+1}</td>
            <td>
              <div style="font-weight:800; color:#f8fafc;">${g.name}</div>
              <a href="${g.url}" target="_blank" style="font-size:11px; color:#60a5fa; text-decoration:none;">🔗 فتح المجموعة</a>
            </td>
            <td><span class="badge badge-info">${g.category || 'عام'}</span></td>
            <td style="font-weight:700; color:#38bdf8;">🕒 ${g.last_scraped_at || 'لم يُسحب بعد'}</td>
            <td style="font-weight:700; color:#34d399;">${g.last_ads_count || 0} إعلان</td>
            <td style="font-weight:700;">${g.total_ads_count || 0} إعلان</td>
            <td><span class="badge ${g.status==='قيد السحب'?'badge-warning':'badge-success'}">${g.status || 'جاهز'}</span></td>
            <td>
              <div style="display:flex; gap:6px;">
                <button class="btn btn-sm btn-success" onclick="scrapeSingleGroup('${g.url}')">⚡ سحب الآن</button>
                <button class="btn btn-danger btn-sm" onclick="deleteGroup(${g.id})">🗑️</button>
              </div>
            </td>
          </tr>
        `).join('');
      } catch (e) {}
    }

    async function loadAllAds() {
      try {
        const res = await apiFetch('/api/ads');
        const data = await res.json();
        adsData = data.pending || [];
        
        document.getElementById('badgePending').innerText = adsData.length;
        document.getElementById('stPublishedAds').innerText = data.published_count || 0;
        document.getElementById('stFlaggedAds').innerText = data.flagged_count || 0;

        const readyCount = adsData.filter(a => a.evaluation && a.evaluation.is_ready_to_publish).length;
        document.getElementById('stReadyAds').innerText = readyCount;

        renderAdsGrid();
      } catch (e) {}
    }

    function filterAds(type, el) {
      currentFilter = type;
      el.parentElement.querySelectorAll('button').forEach(b => b.classList.remove('active'));
      el.classList.add('active');
      renderAdsGrid();
    }

    function renderAdsGrid() {
      const grid = document.getElementById('adsCardsGrid');
      let filtered = adsData;
      if (currentFilter === 'ready') filtered = adsData.filter(a => a.evaluation && a.evaluation.is_ready_to_publish);
      if (currentFilter === 'review') filtered = adsData.filter(a => a.evaluation && !a.evaluation.is_ready_to_publish);

      if (filtered.length === 0) {
        grid.innerHTML = `<div style="grid-column:1/-1; text-align:center; padding:60px; background:var(--card-bg); border-radius:16px; color:var(--text-muted);">🎉 لا توجد إعلانات مطابقة لفلتر العرض!</div>`;
        return;
      }

      grid.innerHTML = filtered.map((ad, idx) => {
        const ev = ad.evaluation || {};
        const sp = ev.specs_details || {};
        const sh = ev.sharia_details || {};

        const title = ad.clean_title || (ad.description || '').substring(0, 60);
        const city = sp.city_name || (ad.location_detected || 'دمشق');
        const subDist = sp.sub_district_name && sp.sub_district_name !== 'عام' ? ` (${sp.sub_district_name})` : '';
        const cat = ad.category || 'عام';
        const leafId = ad.leaf_category_id || 1832;
        const catHierarchy = ad.category_hierarchy ? `${ad.category_hierarchy} (ID: ${leafId})` : `${cat} (ID: ${leafId})`;
        const accountName = ad.publisher_name || 'أبو محمد الشامي';
        const price = ad.price_info && ad.price_info.amount ? `${Number(ad.price_info.amount).toLocaleString()} ${ad.price_info.currency}` : 'السعر: على السوم';
        
        const images = ad.nimages || [];
        const firstImg = images.length > 0 ? `${API_BASE}/imgs/${images[0]}` : '';

        const thumbsHtml = images.map((img, i) => `
          <img src="${API_BASE}/imgs/${img}" class="ad-thumb ${i===0?'active':''}" onclick="document.getElementById('adMainImg-${idx}').src='${API_BASE}/imgs/${img}'" />
        `).join('');

        // أشرطة الفحص
        const specsStatusHtml = sp.has_images && sp.has_desc && sp.has_phone ? 
          `<span style="color:#34d399;">✔️ مكتمل (${sp.images_count} صور + هاتف + وصف + موقع)</span>` :
          `<span style="color:#f87171;">⚠️ ناقص بعض الحقول</span>`;

        const shariaStatusHtml = sh.is_safe ?
          `<span style="color:#34d399;">🟢 مطابق للشريعة والضوابط الرقابية 100%</span>` :
          `<span style="color:#f87171;">⚠️ مخالف: ${sh.flags.join(', ')}</span>`;

        const dupStatusHtml = ad.is_duplicate ?
          `<span style="color:#ef4444; font-weight:700;">⚠️ مكرر مسبقاً على الموقع</span>` :
          `<span style="color:#34d399; font-weight:700;">✔️ جديد كلياً (غير مكرر)</span>`;

        const readyBadgeHtml = ev.is_ready_to_publish ?
          `<span class="badge badge-success" style="font-size:12px;">🚀 جاهز للنشر الفوري</span>` :
          `<span class="badge badge-warning" style="font-size:12px;">⏳ بحاجة لمراجعة</span>`;

        // استخراج بادجات المواصفات الفنية
        const specsObj = ad.specifications || {};
        const specItems = [];
        if (specsObj.make) specItems.push(`🏢 الشركة: ${specsObj.make}`);
        if (specsObj.model) specItems.push(`🚗 الطراز: ${specsObj.model}`);
        if (specsObj.year) specItems.push(`📅 سنة: ${specsObj.year}`);
        if (specsObj.transmission) specItems.push(`⚙️ الكير: ${specsObj.transmission}`);
        if (specsObj.fuel_type) specItems.push(`⛽ الوقود: ${specsObj.fuel_type}`);
        if (specsObj.condition) specItems.push(`✨ الهيكل: ${specsObj.condition}`);
        if (specsObj.color) specItems.push(`🎨 اللون: ${specsObj.color}`);
        if (specsObj.mileage) specItems.push(`📟 ممشى: ${specsObj.mileage}`);
        if (specsObj.area) specItems.push(`📐 مساحة: ${specsObj.area}`);
        if (specsObj.rooms) specItems.push(`🚪 غرف: ${specsObj.rooms}`);
        if (specsObj.features && specsObj.features.length) specItems.push(`⭐ ميزات: ${specsObj.features.slice(0, 3).join(', ')}`);

        const specsBadgesHtml = specItems.length > 0 ? `
          <div style="display:flex; flex-wrap:wrap; gap:4px; margin:6px 0;">
            ${specItems.map(s => `<span style="background:rgba(56,189,248,0.12); color:#38bdf8; border:1px solid rgba(56,189,248,0.25); border-radius:6px; padding:2px 6px; font-size:10px; font-weight:700;">${s}</span>`).join('')}
          </div>
        ` : '';

        // رد وتقرير الذكاء الاصطناعي
        const aiReviewText = (ad.ai_review && ad.ai_review.full_text) ? 
          ad.ai_review.full_text : 
          (ad.moderation_summary || 'تم فحص وتدقيق الإعلان ومطابقته للضوابط الشرعية والشكلية.');

        return `
          <div class="ad-card" id="adCard-${idx}">
            <div class="ad-gallery">
              <img id="adMainImg-${idx}" src="${firstImg}" onerror="this.src='https://placehold.co/600x400/1e293b/f8fafc?text=No+Image'" />
              <div class="ad-thumbs">${thumbsHtml}</div>
            </div>

            <div class="ad-body">
              
              <!-- التصنيف بأصغر ابن واسم الحساب -->
              <div style="display:flex; justify-content:space-between; align-items:center; font-size:12px; font-weight:800; margin-bottom:6px; flex-wrap:wrap; gap:4px;">
                <span style="background:rgba(37,99,235,0.2); color:#60a5fa; padding:3px 8px; border-radius:6px; border:1px solid rgba(59,130,246,0.3);">🏷️ ${catHierarchy}</span>
                <span style="color:#c084fc; background:rgba(168,85,247,0.15); padding:3px 8px; border-radius:6px; border:1px solid rgba(168,85,247,0.3);">👤 المعلن: ${accountName}</span>
              </div>

              <!-- صندوق المراحل التفصيلي -->
              <div class="verification-box">
                <div class="pillar-row">
                  <span class="pillar-label">1️⃣ المواصفات والبيانات:</span>
                  ${specsStatusHtml}
                </div>
                <div class="pillar-row">
                  <span class="pillar-label">2️⃣ الفحص الشرعي والرقابي:</span>
                  ${shariaStatusHtml}
                </div>
                <div class="pillar-row">
                  <span class="pillar-label">3️⃣ عدم التكرار على الموقع:</span>
                  ${dupStatusHtml}
                </div>
                <div class="pillar-row">
                  <span class="pillar-label">4️⃣ حالة الجاهزية للنشر:</span>
                  ${readyBadgeHtml}
                </div>
              </div>

              <!-- بادجات المواصفات المستخرجة -->
              ${specsBadgesHtml}

              <!-- رد وتقرير الذكاء الاصطناعي الشامل -->
              <div style="background:rgba(99,102,241,0.08); border:1px solid rgba(99,102,241,0.3); border-radius:10px; padding:10px; margin:8px 0;">
                <div style="font-size:11px; font-weight:800; color:#a5b4fc; margin-bottom:5px; display:flex; align-items:center; justify-content:space-between;">
                  <span>🤖 رد وتقرير فحص الذكاء الاصطناعي:</span>
                  <span style="color:#34d399; font-size:10px;">✔️ فحص دقيق</span>
                </div>
                <div style="font-size:11px; color:#cbd5e1; line-height:1.55; white-space:pre-line; background:rgba(15,23,42,0.65); padding:8px 10px; border-radius:6px; font-family:monospace; border:1px solid rgba(255,255,255,0.05);">${aiReviewText}</div>
              </div>

              <div>
                <label style="font-size:11px; color:var(--text-muted); font-weight:700;">العنوان المهيكل:</label>
                <input type="text" class="ad-title-input" id="titleInp-${idx}" value="${title.replace(/"/g, '&quot;')}" />
              </div>

              <div style="display:flex; justify-content:space-between; font-size:12px; font-weight:700;">
                <span style="color:#60a5fa;">📍 ${city}${subDist}</span>
                <span style="color:#fde047;">💰 ${price}</span>
              </div>

              <div class="ad-desc-box">${ad.clean_description || ad.description}</div>

              <div style="display:flex; justify-content:space-between; align-items:center; font-size:13px; font-weight:700; color:#38bdf8;">
                <span>📞 ${ad.phone_number || 'لا يوجد'}</span>
                <a href="${ad.ad_url}" target="_blank" style="font-size:11px; color:var(--text-muted); text-decoration:none;">🔗 رابط فيسبوك</a>
              </div>

              <div style="display:flex; gap:8px; margin-top:auto; padding-top:10px; border-top:1px solid var(--border);">
                <button id="pubBtn-${idx}" class="btn btn-success" style="flex:1;" onclick="publishSingleAd(${idx})">✅ نشر للموقع ومجلد الاستيراد</button>
                <button id="rejBtn-${idx}" class="btn btn-danger btn-sm" onclick="rejectSingleAd(${idx})">❌ حذف</button>
              </div>

            </div>
          </div>
        `;
      }).join('');
    }

    const activePublishing = new Set();

    async function publishSingleAd(idx) {
      if (activePublishing.has(idx)) {
        return;
      }
      activePublishing.add(idx);

      const ad = adsData[idx];
      if (!ad) {
        activePublishing.delete(idx);
        return;
      }

      const btn = document.getElementById(`pubBtn-${idx}`);
      const rejBtn = document.getElementById(`rejBtn-${idx}`);
      const origBtnText = btn ? btn.innerHTML : '';

      if (btn) {
        btn.disabled = true;
        btn.style.opacity = '0.7';
        btn.style.cursor = 'not-allowed';
        btn.innerHTML = '⏳ جاري النشر والرفع للموقع...';
      }
      if (rejBtn) {
        rejBtn.disabled = true;
      }

      const titleInp = document.getElementById(`titleInp-${idx}`);
      if (titleInp) {
        ad.clean_title = titleInp.value;
      }

      try {
        const res = await apiFetch('/api/approve', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ ad })
        });
        const data = await res.json();
        if (data.message) {
          alert(data.message);
        }
        await loadAllAds();
      } catch (e) {
        alert("تعذر الاتصال بالسيرفر! تأكد من تشغيل start_app.bat");
        if (btn) {
          btn.disabled = false;
          btn.style.opacity = '1';
          btn.style.cursor = 'pointer';
          btn.innerHTML = origBtnText;
        }
        if (rejBtn) {
          rejBtn.disabled = false;
        }
      } finally {
        activePublishing.delete(idx);
      }
    }

    async function rejectSingleAd(idx) {
      const ad = adsData[idx];
      const rejBtn = document.getElementById(`rejBtn-${idx}`);
      const pubBtn = document.getElementById(`pubBtn-${idx}`);
      if (rejBtn) rejBtn.disabled = true;
      if (pubBtn) pubBtn.disabled = true;

      try {
        await apiFetch('/api/reject', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ ad })
        });
        loadAllAds();
      } catch (e) {
        alert("تعذر الاتصال بالسيرفر! تأكد من تشغيل start_app.bat");
        if (rejBtn) rejBtn.disabled = false;
        if (pubBtn) pubBtn.disabled = false;
      }
    }

    async function bulkPublishReady() {
      if (!confirm("هل تريد تصدير ونشر كافة الإعلانات الجاهزة للنشر الآن؟")) return;
      try {
        const res = await apiFetch('/api/bulk_approve', { method: 'POST' });
        const data = await res.json();
        alert(data.message);
        loadAllAds();
      } catch (e) {
        alert("تعذر الاتصال بالسيرفر! تأكد من تشغيل start_app.bat");
      }
    }

    async function startAllScraping() {
      const groups = groupsData.map(g => g.url);
      if (groups.length === 0) {
        alert("يرجى إضافة روابط مجموعات أولاً!");
        return;
      }
      const params = {
        groups,
        concurrent_tabs: parseInt(document.getElementById('inpConcurrent').value) || 4,
        max_ads_per_group: parseInt(document.getElementById('inpMaxAds').value) || 100,
        timeout_seconds: parseInt(document.getElementById('inpTimeout').value) || 60,
        import_dir: document.getElementById('inpImportDir').value.trim()
      };
      try {
        await apiFetch('/api/start', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(params)
        });
      } catch (e) {
        alert("تعذر الاتصال بالسيرفر! تأكد من تشغيل start_app.bat");
      }
    }

    async function stopAllScraping() {
      try {
        await apiFetch('/api/stop', { method: 'POST' });
      } catch (e) {}
    }

    async function scrapeSingleGroup(url) {
      const params = {
        groups: [url],
        concurrent_tabs: 1,
        max_ads_per_group: parseInt(document.getElementById('inpMaxAds').value) || 100,
        timeout_seconds: parseInt(document.getElementById('inpTimeout').value) || 60,
        import_dir: document.getElementById('inpImportDir').value.trim()
      };
      try {
        await apiFetch('/api/start', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(params)
        });
        switchTab('tab-scraper', document.querySelectorAll('.nav-btn')[1]);
      } catch (e) {
        alert("تعذر الاتصال بالسيرفر! تأكد من تشغيل start_app.bat");
      }
    }

    async function pollScraperStatus() {
      try {
        const res = await apiFetch('/api/status');
        const st = await res.json();
        
        const btnStart = document.getElementById('btnStartScraping');
        const btnStop = document.getElementById('btnStopScraping');
        if (st.is_running) {
          btnStart.style.display = 'none';
          btnStop.style.display = 'inline-flex';
        } else {
          btnStart.style.display = 'inline-flex';
          btnStop.style.display = 'none';
        }

        const tabsBox = document.getElementById('activeTabsLiveList');
        const keys = Object.keys(st.active_tabs || {});
        if (keys.length === 0) {
          tabsBox.innerHTML = `<div style="font-size:12px; color:var(--text-muted); text-align:center; padding:10px;">لا توجد تبويبات نشطة حالياً</div>`;
        } else {
          tabsBox.innerHTML = keys.map(k => `
            <div style="display:flex; justify-content:space-between; background:var(--card-inner); padding:8px 12px; border-radius:8px; font-size:12px; font-weight:700;">
              <div>⚡ تبويب ${parseInt(k)+1}: <span style="color:#60a5fa;">مجموعة [${st.active_tabs[k].group_idx}]</span></div>
              <div style="color:#34d399;">${st.active_tabs[k].status}</div>
            </div>
          `).join('');
        }

        if (st.pending_count !== undefined) {
          document.getElementById('badgePending').innerText = st.pending_count;
          document.getElementById('stReadyAds').innerText = st.ready_count || 0;
          document.getElementById('stPublishedAds').innerText = st.published_count || 0;
          document.getElementById('stFlaggedAds').innerText = st.flagged_count || 0;
        }

        if (st.logs && st.logs.length > 0) {
          const logBox = document.getElementById('liveLogsContainer');
          logBox.innerHTML = st.logs.join('<br>');
          logBox.scrollTop = logBox.scrollHeight;
        }
      } catch (e) {}
    }

    function openAddGroupModal() {
      document.getElementById('addGroupModal').style.display = 'flex';
    }
    function closeAddGroupModal() {
      document.getElementById('addGroupModal').style.display = 'none';
    }

    async function saveNewGroup() {
      const name = document.getElementById('mGrpName').value.trim();
      const url = document.getElementById('mGrpUrl').value.trim();
      const cat = document.getElementById('mGrpCat').value;
      if (!name || !url) {
        alert("يرجى إدخال اسم ورابط المجموعة!");
        return;
      }
      try {
        await apiFetch('/api/add_group', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ name, url, category: cat })
        });
        closeAddGroupModal();
        loadGroups();
      } catch (e) {
        alert("تعذر الاتصال بالسيرفر! يرجى تشغيل start_app.bat");
      }
    }

    async function deleteGroup(id) {
      if (!confirm("هل أنت متأكد من حذف هذا الرابط؟")) return;
      try {
        await apiFetch('/api/delete_group', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ id })
        });
        loadGroups();
      } catch (e) {
        alert("تعذر الاتصال بالسيرفر! يرجى تشغيل start_app.bat");
      }
    }

    async function saveSettings() {
      const webKeyVal = document.getElementById('setWebKey').value.trim();
      const webUrlVal = document.getElementById('setWebUrl').value.trim();
      const cfg = {
        gemini_api_key: document.getElementById('setGeminiKey').value.trim(),
        website_api_url: webUrlVal || 'https://api.lelbai.com/public/api/listings',
        website_api_key: webKeyVal || '67|5181926855ca52522dec3990517f272b027b745f'
      };
      try {
        await apiFetch('/api/config', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(cfg)
        });
        alert("تم حفظ الإعدادات بنجاح! ✅");
      } catch (e) {
        alert("تعذر الاتصال بالسيرفر! يرجى تشغيل start_app.bat");
      }
    }

    async function openLoginBrowser() {
      try {
        const res = await apiFetch('/api/login', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
          alert("تم فتح نافذة المتصفح لتسجيل الدخول إلى فيسبوك. سجل دخولك وأغلق النافذة عند الانتهاء.");
        } else {
          alert(data.message || "حدث خطأ أثناء فتح المتصفح.");
        }
      } catch (e) {
        alert("تعذر الاتصال بالسيرفر! يرجى تشغيل start_app.bat");
      }
    }

    init();
  </script>
</body>
</html>
"""

# ==============================================================================
# خدمات الربط مع لوحة تحكم المنجر وتحديثات النظام
# ==============================================================================
def is_port_listening(port: int, host: str = "127.0.0.1", timeout: float = 0.4) -> bool:
    """فحص ما إذا كان البورت يعمل ومستمع للاتصالات."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False

def get_manager_system_status() -> dict:
    """التحقق من حالة سيرفر المنجر وبقية خدمات المنصة."""
    manager_running = is_port_listening(8002)
    backend_running = is_port_listening(8000)
    frontend_running = is_port_listening(3000)
    desktop_shortcut = os.path.join(os.path.expanduser("~"), "Desktop", "لوحة تحكم المنجر.lnk")
    
    return {
        "manager_running": manager_running,
        "backend_running": backend_running,
        "frontend_running": frontend_running,
        "shortcut_exists": os.path.exists(desktop_shortcut),
        "manager_url": "http://localhost:8002"
    }

def launch_manager_and_all_servers() -> dict:
    """تشغيل كافة سيرفرات المنجر وفتح لوحة التحكم في المتصفح."""
    desktop_shortcut = os.path.join(os.path.expanduser("~"), "Desktop", "لوحة تحكم المنجر.lnk")
    az_base = r"C:\xampp\htdocs\projects\AZ"
    start_servers_bat = os.path.join(az_base, "start_servers.bat")
    manager_url = "http://localhost:8002"

    manager_running = is_port_listening(8002)
    backend_running = is_port_listening(8000)

    # 1. تشغيل start_servers.bat في نافذة جديدة إذا لم تكن سيرفرات المنصة تعمل
    if not backend_running and os.path.exists(start_servers_bat):
        try:
            subprocess.Popen(["cmd.exe", "/c", "start", "start_servers.bat"], cwd=az_base, shell=True)
        except Exception as e:
            print(f"Error launching start_servers.bat: {e}")

    # 2. تشغيل اختصار سطح المكتب المخصص للمنجر إذا وُجد
    if os.path.exists(desktop_shortcut):
        try:
            os.startfile(desktop_shortcut)
        except Exception as e:
            print(f"Error launching shortcut: {e}")
    else:
        manager_exe = os.path.join(az_base, "لوحة_التحكم_المنجر.exe")
        if os.path.exists(manager_exe) and not manager_running:
            try:
                subprocess.Popen([manager_exe], cwd=os.path.join(az_base, "manager"), shell=True)
            except Exception:
                pass

    # 3. فتح صفحة المنجر في المتصفح تلقائياً
    def open_browser():
        time.sleep(1.2)
        try:
            webbrowser.open(manager_url)
        except Exception:
            pass
    threading.Thread(target=open_browser, daemon=True).start()

    return {
        "success": True,
        "message": "تم إطلاق سيرفرات المنجر وفتح لوحة التحكم بنجاح! 🚀",
        "url": manager_url,
        "manager_running": True
    }

def get_system_update_info() -> dict:
    """جلب معلومات آخر تحديث للنظام وتاريخه من Git أو الملف المخزن."""
    last_update_file = os.path.join(BASE_DIR, "last_update.json")
    info = {
        "last_updated_at": "غير محدد",
        "relative_time": "",
        "commit_sha": "",
        "commit_message": "",
        "status": "up_to_date"
    }
    
    try:
        git_dir = os.path.join(BASE_DIR, ".git")
        if os.path.exists(git_dir):
            out = subprocess.check_output(
                ["git", "log", "-1", "--format=%ci|%cr|%h|%s"],
                cwd=BASE_DIR,
                stderr=subprocess.DEVNULL,
                universal_newlines=True
            ).strip()
            if out and "|" in out:
                parts = out.split("|", 3)
                info["last_updated_at"] = parts[0]
                info["relative_time"] = parts[1]
                info["commit_sha"] = parts[2]
                info["commit_message"] = parts[3] if len(parts) > 3 else ""
                return info
    except Exception:
        pass

    if os.path.exists(last_update_file):
        try:
            with open(last_update_file, "r", encoding="utf-8") as f:
                saved = json.load(f)
                info.update(saved)
                return info
        except Exception:
            pass

    return info

def check_and_apply_updates() -> dict:
    """التحقق من وجود تحديثات من GitHub وسحبها تلقائياً."""
    git_dir = os.path.join(BASE_DIR, ".git")
    if os.path.exists(git_dir):
        try:
            subprocess.run(["git", "fetch", "origin"], cwd=BASE_DIR, capture_output=True, timeout=15)
            res = subprocess.run(["git", "pull", "--rebase"], cwd=BASE_DIR, capture_output=True, text=True, timeout=30)
            info = get_system_update_info()
            
            last_update_file = os.path.join(BASE_DIR, "last_update.json")
            with open(last_update_file, "w", encoding="utf-8") as f:
                json.dump(info, f, ensure_ascii=False, indent=2)

            return {
                "success": True,
                "message": "تم التحقق من GitHub وتحديث النظام بنجاح! ✅",
                "details": res.stdout or res.stderr,
                "info": info
            }
        except Exception as e:
            return {"success": False, "message": f"خطأ أثناء التحديث: {str(e)}"}
    else:
        return {"success": False, "message": "المجلد الحالي لا يحتوي على مستودع Git محلي."}

# ==============================================================================
# معالج الطلبات لـ API وسيرفر الويب
# ==============================================================================
CURRENTLY_PUBLISHING = set()
PUBLISH_LOCK = threading.Lock()

class ControlCenterHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path in ["/", "/index.html"]:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_cors_headers()
            self.end_headers()
            dash_file = os.path.join(BASE_DIR, "control_dashboard.html")
            if os.path.exists(dash_file):
                with open(dash_file, "r", encoding="utf-8") as f:
                    self.wfile.write(f.read().encode("utf-8"))
            else:
                self.wfile.write(HTML_PAGE.encode("utf-8"))
            return

        elif path == "/api/groups":
            groups = read_json_file(GROUPS_DATA_FILE)
            self.send_json(groups)
            return

        elif path == "/api/ads":
            raw_pending = read_json_file(PENDING_FILE)
            published = read_json_file(PUBLISHED_FILE)
            flagged = read_json_file(FLAGGED_FILE)

            enriched_pending = [enrich_ad_status(ad) for ad in raw_pending]
            enriched_published = [enrich_ad_status(ad) for ad in published]

            resp = {
                "pending": enriched_pending,
                "pending_count": len(enriched_pending),
                "published": enriched_published,
                "published_count": len(enriched_published),
                "flagged_count": len(flagged)
            }
            self.send_json(resp)
            return

        elif path == "/api/published_ads":
            published = read_json_file(PUBLISHED_FILE)
            enriched_published = [enrich_ad_status(ad) for ad in published]
            self.send_json({
                "published": enriched_published,
                "count": len(enriched_published)
            })
            return

        elif path == "/api/status":
            with task_manager.lock:
                elapsed = int(time.time() - task_manager.start_time) if task_manager.is_running else 0
                h, m, s = elapsed // 3600, (elapsed % 3600) // 60, elapsed % 60
                time_str = f"{h:02d}:{m:02d}:{s:02d}"

                raw_pending = read_json_file(PENDING_FILE)
                published = read_json_file(PUBLISHED_FILE)
                flagged = read_json_file(FLAGGED_FILE)

                resp = {
                    "is_running": task_manager.is_running,
                    "elapsed_time": time_str,
                    "total_groups": task_manager.total_groups_count,
                    "completed_groups": task_manager.completed_groups_count,
                    "total_ads": task_manager.total_ads_collected,
                    "active_tabs": task_manager.active_tabs,
                    "logs": task_manager.logs[-25:],
                    "pending_count": len(raw_pending),
                    "ready_count": len([p for p in raw_pending if enrich_ad_status(p).get("evaluation", {}).get("is_ready_to_publish")]),
                    "published_count": len(published),
                    "flagged_count": len(flagged)
                }
            self.send_json(resp)
            return

        elif path == "/api/config":
            cfg = load_config()
            self.send_json(cfg)
            return

        elif path.startswith("/imgs/"):
            img_name = os.path.basename(path)
            img_path = os.path.join(IMGS_DIR, img_name)
            if os.path.exists(img_path):
                ext = img_name.split(".")[-1].lower()
                mime = "image/webp" if ext == "webp" else ("image/jpeg" if ext in ["jpg", "jpeg"] else "image/png")
                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_cors_headers()
                self.send_header("Cache-Control", "public, max-age=86400")
                self.end_headers()
                with open(img_path, "rb") as f:
                    self.wfile.write(f.read())
                return
            self.send_response(404)
            self.send_cors_headers()
            self.end_headers()
        elif path == "/api/manager_status":
            self.send_json(get_manager_system_status())
            return

        elif path == "/api/update_info":
            self.send_json(get_system_update_info())
            return

        self.send_response(404)
        self.send_cors_headers()
        self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        
        try:
            req_data = json.loads(body)
        except Exception:
            req_data = {}

        if path == "/api/add_group":
            groups = read_json_file(GROUPS_DATA_FILE)
            new_id = (max([g.get("id", 0) for g in groups]) + 1) if groups else 1
            new_entry = {
                "id": new_id,
                "name": req_data.get("name", f"مجموعة {new_id}"),
                "url": req_data.get("url", ""),
                "category": req_data.get("category", "عام"),
                "last_scraped_at": "لم يُسحب بعد",
                "last_ads_count": 0,
                "total_ads_count": 0,
                "status": "جاهز"
            }
            groups.append(new_entry)
            write_json_file(GROUPS_DATA_FILE, groups)
            self.send_json({"success": True})
            return

        elif path == "/api/delete_group":
            gid = req_data.get("id")
            groups = read_json_file(GROUPS_DATA_FILE)
            groups = [g for g in groups if g.get("id") != gid]
            write_json_file(GROUPS_DATA_FILE, groups)
            self.send_json({"success": True})
            return

        elif path == "/api/start":
            ok, msg = task_manager.start_scraping_job(req_data)
            self.send_json({"success": ok, "message": msg})
            return

        elif path == "/api/stop":
            ok, msg = task_manager.stop_scraping_job()
            self.send_json({"success": ok, "message": msg})
            return

        elif path == "/api/login":
            if task_manager.is_running:
                self.send_json({"success": False, "message": "⚠️ يرجى إيقاف عملية السحب أولاً بالضغط على 'إيقاف السحب' قبل فتح نافذة تسجيل الدخول!"})
                return
            login_script = os.path.join(BASE_DIR, "login.py")
            flags = getattr(subprocess, 'CREATE_NEW_CONSOLE', 0)
            subprocess.Popen([sys.executable, login_script], cwd=BASE_DIR, creationflags=flags)
            self.send_json({"success": True})
            return

        elif path == "/api/approve":
            ad = req_data.get("ad", {})
            ad_url = ad.get("ad_url")
            ad_title = ad.get("clean_title")
            ad_identifier = ad_url or ad_title or f"{ad.get('phone_number')}_{ad.get('description', '')[:30]}"

            with PUBLISH_LOCK:
                if ad_identifier in CURRENTLY_PUBLISHING:
                    self.send_json({"success": False, "message": "⏳ جاري نشر هذا الإعلان حالياً بالفعل، يرجى الانتظار بضع ثوانٍ!"})
                    return

                # التحقق الصارم من عدم وجود الإعلان مسبقاً في سجل الإعلانات المنشورة
                published = read_json_file(PUBLISHED_FILE)
                if any((p.get("ad_url") and p.get("ad_url") == ad_url) or 
                       (p.get("clean_title") and p.get("clean_title") == ad_title) for p in published):
                    # إزالة الإعلان من المسودة لأنه منشور بالفعل
                    pending = read_json_file(PENDING_FILE)
                    pending = [p for p in pending if not ((ad_url and p.get("ad_url") == ad_url) or (ad_title and p.get("clean_title") == ad_title))]
                    write_json_file(PENDING_FILE, pending)
                    self.send_json({"success": True, "message": "⚠️ هذا الإعلان تم نشره بالفعل مسبقاً! تم نقله لقسم المنشورات."})
                    return

                CURRENTLY_PUBLISHING.add(ad_identifier)

            try:
                ok, msg = publish_ad_to_website(ad)
                if ok:
                    pending = read_json_file(PENDING_FILE)
                    pending = [p for p in pending if not ((ad_url and p.get("ad_url") == ad_url) or (not ad_url and p.get("clean_title") == ad_title))]
                    write_json_file(PENDING_FILE, pending)
            finally:
                with PUBLISH_LOCK:
                    CURRENTLY_PUBLISHING.discard(ad_identifier)

            self.send_json({"success": ok, "message": msg, "api_ok": ok})
            return

        elif path == "/api/reject":
            ad = req_data.get("ad", {})
            ad_url = ad.get("ad_url")
            ad_title = ad.get("clean_title")
            pending = read_json_file(PENDING_FILE)
            pending = [p for p in pending if not ((ad_url and p.get("ad_url") == ad_url) or (not ad_url and p.get("clean_title") == ad_title))]
            write_json_file(PENDING_FILE, pending)

            flagged = read_json_file(FLAGGED_FILE)
            flagged.append(ad)
            write_json_file(FLAGGED_FILE, flagged)
            self.send_json({"success": True, "message": "تم استبعاد الإعلان بنجاح"})
            return

        elif path == "/api/bulk_approve":
            pending = read_json_file(PENDING_FILE)
            published_count = 0
            api_count = 0
            cfg = load_config()
            has_api = bool(cfg.get("website_api_url", "").strip())
            remaining = []
            
            for ad in pending:
                ev = enrich_ad_status(ad).get("evaluation", {})
                if ev.get("is_ready_to_publish", True):
                    ok, _ = publish_ad_to_website(ad)
                    published_count += 1
                    if ok:
                        if has_api:
                            api_count += 1
                    else:
                        remaining.append(ad)
                else:
                    remaining.append(ad)
            
            write_json_file(PENDING_FILE, remaining)

            if has_api:
                msg = f"تم نشر {api_count} إعلان بنجاح على سيرفر الموقع! 🚀 وتجهيز {published_count} في مجلد الاستيراد."
            else:
                msg = f"تم تجهيز وتصدير {published_count} إعلان بنجاح إلى مجلد إعلانات_للاستيراد على سطح المكتب! 📁\n(⚠️ ملاحظة: لم يتم الرفع المباشر عبر الإنترنت لأن رابط الـ API غير محدد في الإعدادات)"

            self.send_json({"success": True, "message": msg})
            return

        elif path == "/api/config":
            cfg = load_config()
            cfg["gemini_api_key"] = req_data.get("gemini_api_key", cfg.get("gemini_api_key"))
            cfg["website_api_url"] = req_data.get("website_api_url", cfg.get("website_api_url"))
            cfg["website_api_key"] = req_data.get("website_api_key", cfg.get("website_api_key"))
            save_config(cfg)
            task_manager.gemini_processor = GeminiProcessor()
            self.send_json({"success": True})
            return

        elif path == "/api/open_folder":
            import_base = os.path.join(os.path.expanduser("~"), "Desktop", "إعلانات_للاستيراد")
            if not os.path.exists(import_base):
                os.makedirs(import_base, exist_ok=True)
            try:
                os.startfile(import_base)
                self.send_json({"success": True, "message": "تم فتح مجلد الاستيراد بنجاح"})
            except Exception as e:
                self.send_json({"success": False, "message": str(e)})
            return

        elif path == "/api/revert_ad":
            ad = req_data.get("ad", {})
            ad_url = ad.get("ad_url") or ad.get("clean_title")
            published = read_json_file(PUBLISHED_FILE)
            published = [p for p in published if (p.get("ad_url") or p.get("clean_title")) != ad_url]
            write_json_file(PUBLISHED_FILE, published)

            pending = read_json_file(PENDING_FILE)
            if not any((p.get("ad_url") or p.get("clean_title")) == ad_url for p in pending):
                ad_pending = ad.copy()
                ad_pending.pop("publish_status", None)
                ad_pending.pop("published_at", None)
                pending.insert(0, ad_pending)
                write_json_file(PENDING_FILE, pending)
            self.send_json({"success": True, "message": "تم إعادة الإعلان إلى قائمة المراجعة"})
            return

        elif path == "/api/delete_published":
            ad = req_data.get("ad", {})
            ad_url = ad.get("ad_url") or ad.get("clean_title")
            published = read_json_file(PUBLISHED_FILE)
            published = [p for p in published if (p.get("ad_url") or p.get("clean_title")) != ad_url]
            write_json_file(PUBLISHED_FILE, published)
            self.send_json({"success": True, "message": "تم حذف الإعلان من سجل المنشورات"})
        elif path == "/api/launch_manager":
            self.send_json(launch_manager_and_all_servers())
            return

        elif path == "/api/check_update":
            self.send_json(check_and_apply_updates())
            return

        self.send_response(404)
        self.send_cors_headers()
        self.end_headers()

class ThreadedHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True

def run_app():
    port = 5000
    server_address = ('', port)
    httpd = ThreadedHTTPServer(server_address, ControlCenterHandler)
    
    url = f"http://localhost:{port}"
    print(f"\n" + "="*65)
    print(f"🚀 تم تشغيل سيرفر لوحة التحكم المركزية بنجاح!")
    print(f"👉 جاري فتح صفحة التحكم في المتصفح: {url}")
    print(f"="*65 + "\n")

    threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[+] تم إيقاف السيرفر.")

if __name__ == "__main__":
    run_app()
