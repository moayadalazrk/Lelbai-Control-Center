# -*- coding: utf-8 -*-
"""
خادم لوحة المراجعة البشرية والنشر بضغطة زر واحدة (Local Review Dashboard Server)
يعمل بشكل مستقل وخفيف 100% دون الحاجة لتثبيت أي فريموورك إضافي.
"""

import os
import sys
import json
import time
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, List

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from config import load_config, save_config
from publisher import publish_ad_to_website, PUBLISHED_FILE

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PENDING_FILE = os.path.join(BASE_DIR, "pending_review.json")
FLAGGED_FILE = os.path.join(BASE_DIR, "flagged_ads.json")
ALL_ADS_FILE = os.path.join(BASE_DIR, "ads_syria.json")
IMGS_DIR = os.path.join(BASE_DIR, "asstes", "imgs")

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

HTML_DASHBOARD = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>لوحة مراجعة ونشر الإعلانات 🇸🇾 | للبيع - Lelbai</title>
  <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap" rel="stylesheet">
  <style>
    :root {
      --primary: #2563eb;
      --primary-hover: #1d4ed8;
      --success: #16a34a;
      --danger: #dc2626;
      --warning: #f59e0b;
      --bg: #0f172a;
      --card-bg: #1e293b;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --border: #334155;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Tajawal', sans-serif; }
    body { background: var(--bg); color: var(--text); padding: 20px; line-height: 1.6; }
    .header {
      display: flex; justify-content: space-between; align-items: center;
      background: var(--card-bg); padding: 20px 30px; border-radius: 16px;
      border: 1px solid var(--border); margin-bottom: 25px; box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    .header h1 { font-size: 24px; font-weight: 800; color: #60a5fa; display: flex; align-items: center; gap: 10px; }
    .stats-bar { display: flex; gap: 15px; }
    .stat-badge {
      background: #0f172a; padding: 8px 18px; border-radius: 12px;
      border: 1px solid var(--border); font-size: 14px; font-weight: 700;
    }
    .stat-badge span { color: #38bdf8; }
    .actions-bar {
      display: flex; justify-content: space-between; align-items: center;
      margin-bottom: 25px; gap: 15px; flex-wrap: wrap;
    }
    .btn {
      padding: 10px 20px; border-radius: 10px; border: none; font-weight: 700;
      cursor: pointer; transition: all 0.2s; font-size: 15px; display: inline-flex; align-items: center; gap: 8px;
    }
    .btn-primary { background: var(--primary); color: #fff; }
    .btn-primary:hover { background: var(--primary-hover); transform: translateY(-1px); }
    .btn-success { background: var(--success); color: #fff; }
    .btn-success:hover { background: #15803d; transform: translateY(-1px); }
    .btn-danger { background: var(--danger); color: #fff; }
    .btn-danger:hover { background: #b91c1c; }
    .btn-outline { background: transparent; border: 1px solid var(--border); color: var(--text); }
    .btn-outline:hover { background: #334155; }
    
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(380px, 1fr)); gap: 25px; }
    .ad-card {
      background: var(--card-bg); border-radius: 16px; border: 1px solid var(--border);
      overflow: hidden; display: flex; flex-direction: column; transition: all 0.3s;
      box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .ad-card:hover { transform: translateY(-4px); border-color: #60a5fa; box-shadow: 0 8px 25px rgba(0,0,0,0.4); }
    
    .gallery {
      position: relative; height: 250px; background: #000; overflow: hidden;
      display: flex; align-items: center; justify-content: center;
    }
    .gallery img { max-width: 100%; max-height: 100%; object-fit: contain; }
    .gallery-thumbs {
      display: flex; gap: 6px; padding: 10px; background: rgba(0,0,0,0.6);
      position: absolute; bottom: 0; width: 100%; overflow-x: auto;
    }
    .gallery-thumb {
      width: 45px; height: 45px; border-radius: 6px; object-fit: cover;
      cursor: pointer; border: 2px solid transparent; opacity: 0.7; transition: 0.2s;
    }
    .gallery-thumb.active { border-color: #38bdf8; opacity: 1; }
    
    .card-body { padding: 20px; display: flex; flex-direction: column; gap: 12px; flex: 1; }
    .tags-row { display: flex; gap: 8px; flex-wrap: wrap; }
    .tag {
      padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 700;
      background: #334155; color: #e2e8f0;
    }
    .tag-category { background: #1e3a8a; color: #93c5fd; }
    .tag-city { background: #065f46; color: #6ee7b7; }
    .tag-price { background: #854d0e; color: #fde047; font-size: 13px; }
    .tag-warning { background: #7f1d1d; color: #fca5a5; }

    .ad-title-input {
      background: #0f172a; border: 1px solid var(--border); color: #f8fafc;
      padding: 8px 12px; border-radius: 8px; font-size: 16px; font-weight: 700;
      width: 100%; outline: none;
    }
    .ad-title-input:focus { border-color: #60a5fa; }

    .desc-box {
      background: #0f172a; border: 1px solid var(--border); border-radius: 8px;
      padding: 10px; font-size: 13px; color: #cbd5e1; max-height: 120px; overflow-y: auto;
      white-space: pre-line;
    }
    .phone-row {
      display: flex; justify-content: space-between; align-items: center;
      font-size: 14px; font-weight: 700; color: #38bdf8;
    }
    .phone-row a { color: inherit; text-decoration: none; }
    .source-link { font-size: 12px; color: var(--text-muted); text-decoration: none; }
    .source-link:hover { text-decoration: underline; color: #60a5fa; }
    
    .card-actions {
      display: flex; gap: 10px; margin-top: auto; padding-top: 15px;
      border-top: 1px solid var(--border);
    }
    .card-actions .btn { flex: 1; justify-content: center; }
    
    .empty-state {
      text-align: center; padding: 80px 20px; background: var(--card-bg);
      border-radius: 16px; border: 1px solid var(--border); grid-column: 1 / -1;
    }
    .empty-state h3 { font-size: 20px; color: #94a3b8; margin-bottom: 10px; }

    /* Modal */
    .modal {
      display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.7);
      align-items: center; justify-content: center; z-index: 100;
    }
    .modal-content {
      background: var(--card-bg); width: 90%; max-width: 500px; border-radius: 16px;
      border: 1px solid var(--border); padding: 25px; display: flex; flex-direction: column; gap: 15px;
    }
    .modal-content input {
      background: #0f172a; border: 1px solid var(--border); color: #fff;
      padding: 10px; border-radius: 8px; width: 100%; outline: none; font-size: 14px;
    }
  </style>
</head>
<body>

  <div class="header">
    <h1>🚀 مراجعة ونشر إعلانات سوريا 🇸🇾 <span style="font-size:14px; color:var(--text-muted);">(للبيع - Lelbai)</span></h1>
    <div class="stats-bar">
      <div class="stat-badge">بانتظار المراجعة: <span id="pendingCount">0</span></div>
      <div class="stat-badge">تم النشر: <span id="publishedCount" style="color:#4ade80;">0</span></div>
      <div class="stat-badge">المستبعدة: <span id="flaggedCount" style="color:#f87171;">0</span></div>
    </div>
  </div>

  <div class="actions-bar">
    <div style="display:flex; gap:10px;">
      <button class="btn btn-success" onclick="bulkApproveAll()">⚡ اعتماد ونشر كافة الإعلانات السليمة</button>
      <button class="btn btn-outline" onclick="loadAds()">🔄 تحديث القائمة</button>
    </div>
    <div>
      <button class="btn btn-outline" onclick="openConfigModal()">⚙️ إعدادات الـ API والربط</button>
    </div>
  </div>

  <div class="grid" id="adsGrid">
    <!-- يتم ملء البطاقات تلقائياً عبر JavaScript -->
  </div>

  <!-- Modal للإعدادات -->
  <div class="modal" id="configModal">
    <div class="modal-content">
      <h2>⚙️ إعدادات المنظومة</h2>
      <div>
        <label style="font-size:13px; color:var(--text-muted);">مفتاح Gemini API المجاني:</label>
        <input type="password" id="cfgGeminiKey" placeholder="AIzaSy...">
      </div>
      <div>
        <label style="font-size:13px; color:var(--text-muted);">رابط API الموقع للنشر المباشر (اختياري):</label>
        <input type="text" id="cfgWebUrl" placeholder="https://example.com/api/ads">
      </div>
      <div>
        <label style="font-size:13px; color:var(--text-muted);">مفتاح API الموقع (إن وُجد):</label>
        <input type="password" id="cfgWebKey" placeholder="Bearer Token...">
      </div>
      <div style="display:flex; justify-content:flex-end; gap:10px; margin-top:10px;">
        <button class="btn btn-outline" onclick="closeConfigModal()">إلغاء</button>
        <button class="btn btn-primary" onclick="saveConfigData()">حفظ الإعدادات</button>
      </div>
    </div>
  </div>

  <script>
    let adsData = [];

    async function loadAds() {
      try {
        const res = await fetch('/api/ads');
        const data = await res.json();
        adsData = data.pending || [];
        
        document.getElementById('pendingCount').innerText = data.pending_count || 0;
        document.getElementById('publishedCount').innerText = data.published_count || 0;
        document.getElementById('flaggedCount').innerText = data.flagged_count || 0;

        renderGrid();
      } catch (err) {
        console.error("Error loading ads:", err);
      }
    }

    function renderGrid() {
      const grid = document.getElementById('adsGrid');
      if (!adsData || adsData.length === 0) {
        grid.innerHTML = `
          <div class="empty-state">
            <h3>🎉 لا توجد إعلانات معلقة بانتظار المراجعة!</h3>
            <p style="color:var(--text-muted)">قم بتشغيل البوت لسحب إعلانات جديدة، وستظهر هنا فوراً للمراجعة والنشر.</p>
          </div>
        `;
        return;
      }

      grid.innerHTML = adsData.map((ad, idx) => {
        const title = ad.clean_title || ad.description.substring(0, 60);
        const city = ad.city_name || (ad.location_detected || 'سوريا');
        const subDist = ad.sub_district_name ? ` (${ad.sub_district_name})` : '';
        const category = ad.category || 'عام';
        const price = ad.price_info && ad.price_info.amount ? `${Number(ad.price_info.amount).toLocaleString()} ${ad.price_info.currency}` : 'السعر: على السوم / غير محدد';
        const desc = ad.clean_description || ad.description;
        const images = ad.nimages || [];
        const firstImg = images.length > 0 ? `/imgs/${images[0]}` : '';

        const thumbsHtml = images.map((img, imgIdx) => `
          <img src="/imgs/${img}" class="gallery-thumb ${imgIdx === 0 ? 'active' : ''}" onclick="switchImg(${idx}, '/imgs/${img}', this)" />
        `).join('');

        const warningTag = ad.flags && ad.flags.length > 0 ? `
          <span class="tag tag-warning">⚠️ تنبيه: ${ad.flags.join(', ')}</span>
        ` : '';

        return `
          <div class="ad-card" id="card-${idx}">
            <div class="gallery">
              <img id="mainImg-${idx}" src="${firstImg}" onerror="this.src='https://placehold.co/600x400/1e293b/f8fafc?text=No+Image'" />
              <div class="gallery-thumbs">${thumbsHtml}</div>
            </div>
            
            <div class="card-body">
              <div class="tags-row">
                <span class="tag tag-category">📁 ${category}</span>
                <span class="tag tag-city">📍 ${city}${subDist}</span>
                <span class="tag tag-price">💰 ${price}</span>
                ${warningTag}
              </div>

              <div>
                <label style="font-size:12px; color:var(--text-muted); font-weight:700;">العنوان المهيكل:</label>
                <input type="text" class="ad-title-input" id="title-${idx}" value="${title.replace(/"/g, '&quot;')}" />
              </div>

              <div class="desc-box">${desc}</div>

              <div class="phone-row">
                <span>📞 ${ad.phone_number || 'لا يوجد رقم'}</span>
                <a href="${ad.ad_url}" target="_blank" class="source-link">🔗 المنشور على فيسبوك</a>
              </div>

              <div class="card-actions">
                <button class="btn btn-success" onclick="approveAd(${idx})">✅ نشر للموقع</button>
                <button class="btn btn-danger" onclick="rejectAd(${idx})">❌ استبعاد</button>
              </div>
            </div>
          </div>
        `;
      }).join('');
    }

    function switchImg(cardIdx, src, el) {
      document.getElementById(`mainImg-${cardIdx}`).src = src;
      const thumbs = el.parentElement.querySelectorAll('.gallery-thumb');
      thumbs.forEach(t => t.classList.remove('active'));
      el.classList.add('active');
    }

    async function approveAd(idx) {
      const ad = adsData[idx];
      const customTitle = document.getElementById(`title-${idx}`).value;
      ad.clean_title = customTitle;

      const btn = event.target;
      btn.innerText = "⏳ جاري النشر...";
      btn.disabled = true;

      try {
        const res = await fetch('/api/approve', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ ad })
        });
        const resp = await res.json();
        if (resp.success) {
          loadAds();
        } else {
          alert(resp.message || "حدث خطأ أثناء النشر");
        }
      } catch (e) {
        alert("خطأ: " + e);
      }
    }

    async function rejectAd(idx) {
      if (!confirm("هل أنت متأكد من استبعاد هذا الإعلان؟")) return;
      const ad = adsData[idx];
      try {
        await fetch('/api/reject', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ ad })
        });
        loadAds();
      } catch (e) {
        alert("خطأ: " + e);
      }
    }

    async function bulkApproveAll() {
      if (!confirm(`هل تريد اعتماد ونشر كافة الإعلانات (${adsData.length} إعلان) بضغطة واحدة؟`)) return;
      try {
        const res = await fetch('/api/bulk_approve', { method: 'POST' });
        const data = await res.json();
        alert(data.message || "تم النشر بنجاح!");
        loadAds();
      } catch (e) {
        alert("خطأ: " + e);
      }
    }

    function openConfigModal() {
      fetch('/api/config').then(r => r.json()).then(cfg => {
        document.getElementById('cfgGeminiKey').value = cfg.gemini_api_key || '';
        document.getElementById('cfgWebUrl').value = cfg.website_api_url || '';
        document.getElementById('cfgWebKey').value = cfg.website_api_key || '';
        document.getElementById('configModal').style.display = 'flex';
      });
    }

    function closeConfigModal() {
      document.getElementById('configModal').style.display = 'none';
    }

    async function saveConfigData() {
      const cfg = {
        gemini_api_key: document.getElementById('cfgGeminiKey').value.trim(),
        website_api_url: document.getElementById('cfgWebUrl').value.trim(),
        website_api_key: document.getElementById('cfgWebKey').value.trim()
      };
      await fetch('/api/config', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(cfg)
      });
      closeConfigModal();
      alert("تم حفظ الإعدادات بنجاح! ✅");
    }

    loadAds();
    setInterval(loadAds, 8000); // تحديث تلقائي كل 8 ثواني
  </script>
</body>
</html>
"""

class ReviewDashboardHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass # منع تشويش شاشة الأوامر بالـ Logs العادية

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_DASHBOARD.encode("utf-8"))
            return

        elif path == "/api/ads":
            pending = read_json_file(PENDING_FILE)
            published = read_json_file(PUBLISHED_FILE)
            flagged = read_json_file(FLAGGED_FILE)

            resp_data = {
                "pending": pending,
                "pending_count": len(pending),
                "published_count": len(published),
                "flagged_count": len(flagged)
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(resp_data, ensure_ascii=False).encode("utf-8"))
            return

        elif path == "/api/config":
            cfg = load_config()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(cfg, ensure_ascii=False).encode("utf-8"))
            return

        elif path.startswith("/imgs/"):
            filename = os.path.basename(path)
            img_full_path = os.path.join(IMGS_DIR, filename)
            if os.path.exists(img_full_path):
                ext = filename.split(".")[-1].lower()
                mime = "image/webp" if ext == "webp" else ("image/jpeg" if ext in ["jpg", "jpeg"] else "image/png")
                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Cache-Control", "public, max-age=86400")
                self.end_headers()
                with open(img_full_path, "rb") as f:
                    self.wfile.write(f.read())
                return
            else:
                self.send_response(404)
                self.end_headers()
                return

        self.send_response(404)
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

        if path == "/api/approve":
            ad = req_data.get("ad", {})
            success, msg = publish_ad_to_website(ad)

            # إزالة الإعلان من pending_review.json
            pending = read_json_file(PENDING_FILE)
            ad_url = ad.get("ad_url")
            pending = [p for p in pending if p.get("ad_url") != ad_url]
            write_json_file(PENDING_FILE, pending)

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"success": success, "message": msg}, ensure_ascii=False).encode("utf-8"))
            return

        elif path == "/api/reject":
            ad = req_data.get("ad", {})
            ad_url = ad.get("ad_url")

            pending = read_json_file(PENDING_FILE)
            pending = [p for p in pending if p.get("ad_url") != ad_url]
            write_json_file(PENDING_FILE, pending)

            flagged = read_json_file(FLAGGED_FILE)
            if ad not in flagged:
                flagged.append(ad)
            write_json_file(FLAGGED_FILE, flagged)

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}, ensure_ascii=False).encode("utf-8"))
            return

        elif path == "/api/bulk_approve":
            pending = read_json_file(PENDING_FILE)
            count = 0
            for ad in pending:
                publish_ad_to_website(ad)
                count += 1
            
            write_json_file(PENDING_FILE, [])
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "message": f"تم اعتماد ونشر {count} إعلان بنجاح!"}, ensure_ascii=False).encode("utf-8"))
            return

        elif path == "/api/config":
            cfg = load_config()
            cfg["gemini_api_key"] = req_data.get("gemini_api_key", cfg.get("gemini_api_key"))
            cfg["website_api_url"] = req_data.get("website_api_url", cfg.get("website_api_url"))
            cfg["website_api_key"] = req_data.get("website_api_key", cfg.get("website_api_key"))
            save_config(cfg)

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}, ensure_ascii=False).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

def start_review_server(port: int = 5000):
    """تشغيل خادم المراجعة المحلي"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, ReviewDashboardHandler)
    print(f"\n" + "="*65)
    print(f"🖥️  لوحة المراجعة البشرية والنشر تعمل الآن على الرابط:")
    print(f"👉 http://localhost:{port}")
    print(f"="*65 + "\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[+] تم إيقاف خادم المراجعة.")

if __name__ == "__main__":
    cfg = load_config()
    port = int(cfg.get("dashboard_port", 5000))
    start_review_server(port)
