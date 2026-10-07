# -*- coding: utf-8 -*-
"""
محرك سحب الإعلانات بالمتصفح المرئي (Playwright Scraper)
يقوم بفتح متصفح مرئي حقيقي أمام المستخدم والتمرير وسحب الإعلانات وفلترتها وحفظها.
"""

import os
import sys
import json
import time
import random
import re
from datetime import datetime
from typing import List, Dict, Any, Callable, Optional
from urllib.parse import urljoin

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from playwright.sync_api import sync_playwright, Page, BrowserContext
from syria_filter import validate_ad, normalize_text
from image_processor import process_ad_images
from gemini_processor import GeminiProcessor

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PENDING_FILE = os.path.join(BASE_DIR, "pending_review.json")
FLAGGED_FILE = os.path.join(BASE_DIR, "flagged_ads.json")
IMGS_DIR = os.path.join(BASE_DIR, "asstes", "imgs")

class SyrianAdScraper:
    def __init__(self, user_data_dir: str = "./browser_session", headless: bool = False):
        """
        تهيئة المتصفح المرئي
        :param user_data_dir: مجلد حفظ ملفات الجلسة والكوكيز لتفادي تسجيل الدخول كل مرة
        :param headless: False ليفتح المتصفح أمام المستخدم مباشرة
        """
        self.user_data_dir = os.path.abspath(user_data_dir)
        self.headless = headless
        self.extracted_ads: List[Dict[str, Any]] = []
        self.seen_signatures = set()
        self.gemini_processor = GeminiProcessor()

    def load_existing_ads(self, file_path: str):
        """تحميل أي إعلانات سابقة موجودة في ملف JSON لتفادي مسحها أو تكرارها"""
        if not file_path or not os.path.exists(file_path):
            return
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    existing = json.loads(content)
                    if isinstance(existing, list):
                        loaded_count = 0
                        for ad in existing:
                            if isinstance(ad, dict):
                                phone = ad.get("phone_number") or ""
                                desc = ad.get("description") or ""
                                sig = f"{phone}_{desc[:50]}"
                                if sig not in self.seen_signatures:
                                    self.extracted_ads.append(ad)
                                    self.seen_signatures.add(sig)
                                    loaded_count += 1
                        if loaded_count > 0:
                            print(f"[+] تم تحميل {loaded_count} إعلانات سابقة من ملف {os.path.basename(file_path)}")
        except Exception as e:
            pass

    def _is_valid_image(self, src: str) -> bool:
        """التحقق من أن رابط الصورة هو صورة إعلان وليس أيقونة أو صورة شخصية صغيرة"""
        if not src or not src.startswith("http"):
            return False
        # استبعاد الرموز التعبيرية والأيقونات الشائعة
        bad_keywords = ["emoji", "rsrc.php", "icon", "static", "profile_pic", "avatar", "spacer.gif"]
        for bad in bad_keywords:
            if bad in src.lower():
                return False
        return True

    def _close_modals_and_popups(self, page: Page):
        """إغلاق أي نافذة منبثقة أو نافذة صور/منشور معتمة قد تعيق التمرير"""
        try:
            # 1. إرسال زر Escape
            page.keyboard.press("Escape")
            time.sleep(0.3)
            # 2. البحث عن أزرار الإغلاق والنقر عليها برمجياً
            page.evaluate("""() => {
                const closeSelectors = [
                    "div[aria-label='إغلاق']",
                    "div[aria-label='Close']",
                    "div[aria-label='Close post']",
                    "div[aria-label='إغلاق المنشور']",
                    "div[role='dialog'] div[role='button']",
                    "div[aria-label='X']"
                ];
                for (const sel of closeSelectors) {
                    const btns = document.querySelectorAll(sel);
                    for (const b of btns) {
                        const label = (b.getAttribute('aria-label') || '').toLowerCase();
                        if (label.includes('close') || label.includes('إغلاق') || b.textContent.trim() === '×') {
                            b.click();
                        }
                    }
                }
            }""")
        except Exception:
            pass

    def _expand_see_more_buttons(self, page: Page):
        """توسيع نصوص 'عرض المزيد' بدقة دون النقر على الصور أو فتح النوافذ المنبثقة"""
        try:
            page.evaluate("""() => {
                const elements = document.querySelectorAll("div[role='button'], span, strong");
                for (const el of elements) {
                    const txt = el.textContent ? el.textContent.trim() : '';
                    if (txt === 'عرض المزيد' || txt === 'See more' || txt === 'See More' || txt === '... عرض المزيد') {
                        // التأكد من أنه عنصر نصي فقط وليس بطاقة إعلان كاملة
                        if (el.children.length <= 1) {
                            try { el.click(); } catch(e){}
                        }
                    }
                }
            }""")
        except Exception:
            pass

    def _extract_posts_from_page(self, page: Page, group_url: str) -> List[Dict[str, Any]]:
        """استخراج فوري وسريع لكافة إعلانات الصفحة في خطوة واحدة مع تنظيف النص تماماً"""
        ads_found = []

        try:
            raw_posts = page.evaluate("""() => {
                // توسيع نصوص 'عرض المزيد'
                const moreBtns = document.querySelectorAll("div[role='button'], span, strong");
                for (const b of moreBtns) {
                    const txt = b.textContent ? b.textContent.trim() : '';
                    if (txt === 'عرض المزيد' || txt === 'See more' || txt === 'See More' || txt === '... عرض المزيد') {
                        if (b.children.length <= 1) {
                            try { b.click(); } catch(e){}
                        }
                    }
                }

                // استهداف الحاويات الرئيسية للمنشورات فقط وتجنب الحاويات الفرعية المكررة
                let containers = document.querySelectorAll("div[role='feed'] > div, div[data-pagelet*='FeedUnit'], div[role='article']");
                if (!containers || containers.length === 0) {
                    containers = document.querySelectorAll("div[dir='auto']");
                }

                const extracted = [];
                for (const c of containers) {
                    // استخراج نص الإعلان الأساسي تحديداً دون أسماء المعلقين أو صندوق التعليقات
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

                    // استخراج الصور
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

                    // استخراج رابط المنشور الثابت
                    let link = '';
                    const aTags = c.querySelectorAll("a[href]");
                    for (const a of aTags) {
                        const href = a.href || a.getAttribute('href') || '';
                        if (href.includes('/posts/') || href.includes('/permalink/') || href.includes('story_fbid') || href.includes('/multi_permalinks/')) {
                            link = href.split('?')[0];
                            break;
                        }
                    }

                    extracted.push({
                        text: text,
                        images: images,
                        link: link
                    });
                }
                return extracted;
            }""")
        except Exception:
            raw_posts = []

        try:
            page_title = page.title()
        except Exception:
            page_title = ""

        for p in raw_posts:
            text_content = p.get("text", "")
            if not text_content or len(text_content) < 15:
                continue

            validation = validate_ad(text_content, group_context=page_title)
            if not validation["is_valid"]:
                continue

            clean_desc = validation.get("cleaned_description", text_content)
            if not clean_desc or len(clean_desc) < 10:
                clean_desc = text_content

            primary_phone = validation["phones"][0] if validation["phones"] else ""
            signature = f"{primary_phone}_{clean_desc[:50]}"
            if signature in self.seen_signatures:
                continue

            post_url = p.get("link") or group_url
            raw_images = p.get("images", [])

            # شرط وجود صور إلزامي: استبعاد أي منشور لا يحتوي على صور
            if not raw_images or len(raw_images) == 0:
                continue

            # تحميل الصور وضغطها وتحويلها إلى WebP وحفظها باسم UUID (ماكس 5 صور)
            images_download, nimages = process_ad_images(raw_images, max_count=5)

            if not nimages or len(nimages) == 0:
                continue

            primary_phone = validation["phones"][0] if validation["phones"] else None

            ad_data = {
                "ad_url": post_url,
                "phone_number": primary_phone,
                "description": clean_desc,
                "images dowlod": images_download,
                "nimages": nimages,
                "id-citie": validation.get("id-citie"),
                "id-sub_districts": validation.get("id-sub_districts"),
                "city_name": validation.get("city_name"),
                "sub_district_name": validation.get("sub_district_name"),
                "location_detected": validation["location_detected"],
                "extracted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            # فحص وهيكلة الإعلان والتحقق من الصور عبر الذكاء الاصطناعي (Gemini Vision)
            processed_ad = self.gemini_processor.process_and_clean_ad(ad_data, IMGS_DIR)

            if not processed_ad.get("is_safe", True):
                print(f"\n[🚫 تم استبعاد إعلان مخالف]: {', '.join(processed_ad.get('flags', []))}")
                print(f"   السبب: {processed_ad.get('moderation_summary')}")
                self.append_ad_to_file(FLAGGED_FILE, processed_ad)
                self.seen_signatures.add(signature)
                continue

            # حفظ الإعلان الصالح في صندوق المراجعة للوحة التحكم
            self.append_ad_to_file(PENDING_FILE, processed_ad)

            self.seen_signatures.add(signature)
            ads_found.append(processed_ad)

        return ads_found

    def scrape_group(
        self,
        group_url: str,
        max_ads: int = 100,
        max_scroll_attempts: int = 250,
        output_file: str = "ads_syria.json",
        progress_callback: Optional[Callable[[Dict[str, Any], int], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        تشغيل سحب الإعلانات من رابط مجموعة
        :param group_url: رابط المجموعة
        :param max_ads: الحد الأقصى للإعلانات الصالحة المطلوب جمعها
        :param max_scroll_attempts: عدد مرات التمرير لأسفل الصفحة
        :param output_file: اسم مسار ملف JSON لحفظ النتائج
        :param progress_callback: دالة إشعار عند التقاط إعلان جديد
        """
        os.makedirs(self.user_data_dir, exist_ok=True)
        output_file = os.path.abspath(output_file)
        
        if not self.extracted_ads:
            self.load_existing_ads(output_file)
        
        print(f"\n[+] جاري تشغيل المتصفح المرئي...")
        print(f"[+] مسار حفظ الجلسة: {self.user_data_dir}")
        print(f"[+] سيتم حفظ الإعلانات في: {output_file}")
        print(f"[+] سيتم فتح الصفحة: {group_url}\n")

        # تنظيف أي أقفال أو عمليات عالقة للمتصفح
        for lock in ["lockfile", "SingletonLock", "SingletonCookie", "SingletonSocket"]:
            lp = os.path.join(self.user_data_dir, lock)
            if os.path.exists(lp):
                try:
                    os.remove(lp)
                except Exception:
                    pass

        with sync_playwright() as p:
            # تشغيل متصفح مرئي مع سياق مستخدم دائم وتفعيل وضع الأمان والحماية التامة
            context = None
            for attempt in range(2):
                try:
                    context = p.chromium.launch_persistent_context(
                        user_data_dir=self.user_data_dir,
                        headless=self.headless,
                        viewport={"width": 1280, "height": 850},
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                        locale="ar-SY",
                        timezone_id="Asia/Damascus",
                        args=[
                            "--start-maximized",
                            "--disable-blink-features=AutomationControlled",
                            "--disable-infobars",
                            "--no-sandbox"
                        ]
                    )
                    break
                except Exception as e:
                    if attempt == 0:
                        import subprocess
                        if sys.platform == "win32":
                            try:
                                cmd = "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*browser_session*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
                                subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, timeout=5)
                            except Exception:
                                pass
                        time.sleep(1)
                    else:
                        raise e

            # إخفاء أي أثر لبرامج الأتمتة وجعل المتصفح يظهر كمتصفح بشري طبيعي 100%
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)

            page = context.pages[0] if context.pages else context.new_page()

            try:
                page.goto(group_url, wait_until="domcontentloaded", timeout=60000)
            except Exception as e:
                print(f"[!] تنبيه أثناء تحميل الصفحة: {e}")

            time.sleep(3)

            # فحص ما إذا كانت الصفحة تطلب تسجيل الدخول
            page_text = page.locator("body").inner_text() if page.locator("body").count() > 0 else ""
            if "Log In" in page_text or "تسجيل الدخول" in page_text or "log in" in page.url.lower():
                print("\n" + "="*65)
                print("🔐 تنبيه: المجموعة أو الصفحة تتطلب تسجيل الدخول.")
                print("👉 يرجى تسجيل الدخول إلى حسابك في نافذة المتصفح المفتوحة الآن.")
                print("⏳ البوت ينتظرك لإتمام تسجيل الدخول...")
                print("="*65)
                
                # انتظار تسجيل الدخول
                for _ in range(120): # مهلة 4 دقائق
                    time.sleep(2)
                    current_text = page.locator("body").inner_text() if page.locator("body").count() > 0 else ""
                    if "Log In" not in current_text and "تسجيل الدخول" not in current_text and "login" not in page.url.lower():
                        print("[✔] تم إتمام تسجيل الدخول بنجاح! جاري حفظ الجلسة ومتابعة السحب...")
                        try:
                            context.storage_state(path=os.path.join(self.user_data_dir, "auth_state.json"))
                        except Exception:
                            pass
            # فحص ما إذا كانت الصفحة غير متوفرة أو الرابط خاطئ
            if "هذا المحتوى غير متوفر" in page_text or "This content isn't available" in page_text or "Page Not Found" in page_text:
                print("\n" + "!"*65)
                print(f"⚠️ تنبيه: صفحة المجموعة غير متوفرة أو خاصة على فيسبوك:")
                print(f"   الرابط: {group_url}")
                print("   السبب: قد يكون الرابط خاطئاً، أو المجموعة خاصة تتطلب انضمام حسابك لها أولاً.")
                print("   يرجى التأكد من رابط المجموعة وفتحها بحسابك.")
                print("!"*65 + "\n")

            # انتظار قليل في حال كان الرابط عبارة عن رابط مشاركة share/g/... لإتمام التحويل للرابط الفعلي
            time.sleep(2)
            current_url = page.url

            # إذا تم التحويل إلى رابط منشور فردي أو نافذة منبثقة، نتوجه فوراً لصفحة المجموعة الرئيسية
            group_match = re.search(r'(https?://(?:www\.)?facebook\.com/groups/[0-9a-zA-Z._-]+)', current_url)
            if group_match and ("/permalink/" in current_url or "/posts/" in current_url or "/multi_permalinks/" in current_url):
                clean_group_url = group_match.group(1) + "/"
                print(f"[+] التوجه إلى خلاصة المجموعة الرئيسية لعرض كل المنشورات: {clean_group_url}")
                try:
                    page.goto(clean_group_url, wait_until="domcontentloaded", timeout=30000)
                    time.sleep(3)
                except Exception:
                    pass

            # إغلاق أي نافذة منبثقة معتمة قد تكون مفتوحة
            self._close_modals_and_popups(page)

            scroll_count = 0
            ads_collected_in_group = 0
            no_new_ads_count = 0
            last_ad_found_time = time.time()

            while scroll_count < max_scroll_attempts and ads_collected_in_group < max_ads:
                scroll_count += 1
                
                # استخراج فوري للإعلانات المطابقة للشروط
                new_ads = self._extract_posts_from_page(page, group_url)
                
                added_in_this_step = 0
                for ad in new_ads:
                    # إضافة وحفظ فوري في ملف JSON دون مسح أي بيانات سابقة
                    self.append_ad_to_file(output_file, ad)
                    ads_collected_in_group += 1
                    added_in_this_step += 1
                    last_ad_found_time = time.time()
                    
                    if progress_callback:
                        progress_callback(ad, len(self.extracted_ads), ads_collected_in_group)
                    else:
                        phone_display = ad.get("phone_number") or ""
                        images_count = len(ad.get("nimages", []))
                        print(f"[{len(self.extracted_ads)}] إعلان سوري جديد! ⚡ (المجموعة: {ads_collected_in_group}/{max_ads}) | رقم: {phone_display} | الموقع: {ad.get('location_detected', '')}")
                        print(f"    رابط: {ad['ad_url']}")
                        print(f"    الصور المعالجة (WebP): {images_count} صور")
                        print("-" * 50)

                    if ads_collected_in_group >= max_ads:
                        print(f"\n[✔] تم الوصول للحد المطلوب من هذه المجموعة ({max_ads} إعلان).")
                        break

                if added_in_this_step == 0:
                    no_new_ads_count += 1
                else:
                    no_new_ads_count = 0

                # فحص مهلة الانتظار: إذا مرت دقيقة كاملة (60 ثانية) دون أي إعلان جديد نخرج من المجموعة
                if (time.time() - last_ad_found_time) >= 60:
                    print(f"\n[⏱️ مهلة الانتظار]: مضت دقيقة كاملة (60 ثانية) دون العثور على أي إعلان جديد في هذه المجموعة.")
                    print(f"👉 جاري إنهاء هذه المجموعة والانتقال فوراً للمجموعة التالية...")
                    break

                # تمرير سريع وسلس لأسفل مع فاصل زمني سريع
                scroll_distance = random.randint(1500, 2400)
                page.evaluate(f"window.scrollBy({{top: {scroll_distance}, behavior: 'smooth'}});")
                time.sleep(random.uniform(0.6, 1.1))

            context.close()

        print(f"\n[✔] اكتمل سحب المجموعة! إجمالي الإعلانات السورية في الملف: {len(self.extracted_ads)}")
        return self.extracted_ads

    def append_ad_to_file(self, file_path: str, ad: Dict[str, Any]):
        """
        إضافة الإعلان الجديد إلى ملف JSON دون مسح أو تعديل أي إعلانات سابقة إطلاقاً:
        - يقرأ الملف الحالي من القرص
        - يدمج الإعلان الجديد ويمنع التكرار
        - يحفظ الملف فوراً مع إجبار الويندوز على المزامنة الفورية مع القرص الصلب
        """
        try:
            abs_path = os.path.abspath(file_path)
            dir_name = os.path.dirname(abs_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)

            all_ads = []
            seen_keys = set()

            # 1. قراءة كافة الإعلانات الموجودة على القرص مسبقاً
            if os.path.exists(abs_path):
                try:
                    with open(abs_path, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        if content:
                            loaded = json.loads(content)
                            if isinstance(loaded, list):
                                for item in loaded:
                                    if isinstance(item, dict):
                                        key = f"{item.get('phone_number')}_{item.get('description', '')[:50]}"
                                        all_ads.append(item)
                                        seen_keys.add(key)
                except Exception:
                    pass

            # 2. إضافة الإعلان الجديد إذا لم يكن موجوداً
            new_key = f"{ad.get('phone_number')}_{ad.get('description', '')[:50]}"
            if new_key not in seen_keys:
                all_ads.append(ad)
                seen_keys.add(new_key)

            # 3. تحديث قائمة الإعلانات في ذاكرة البوت
            self.extracted_ads = all_ads
            self.seen_signatures.update(seen_keys)

            # 4. حفظ فوري على القرص الصلب مع flush و fsync
            with open(abs_path, "w", encoding="utf-8") as f:
                json.dump(all_ads, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())

        except Exception as e:
            print(f"\n[❌ خطأ في حفظ الإعلان بملف JSON]: {e}")

    def save_to_json(self, file_path: str):
        """حفظ فوري لقائمة الإعلانات بصيغة JSON مع إجبار الويندوز على الحفظ الفوري للقرص"""
        try:
            abs_path = os.path.abspath(file_path)
            dir_name = os.path.dirname(abs_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)

            with open(abs_path, "w", encoding="utf-8") as f:
                json.dump(self.extracted_ads, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
        except Exception as e:
            print(f"\n[❌ خطأ في حفظ ملف JSON]: {e}")
