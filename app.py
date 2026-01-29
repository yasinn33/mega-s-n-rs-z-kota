import certifi
from flask import Flask, request, jsonify, render_template_string
from pymongo import MongoClient
from functools import wraps
import os
import datetime
import uuid

app = Flask(__name__)

# --- AYARLAR ---
LICENSE_KEY = "YAEL2026" 
MONGO_URI = os.environ.get("MONGO_URI") 
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['mega_leech']
queue = db['queue']
deliveries = db['deliveries']

# --- GÜVENLİK ---
def require_license(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        key = request.headers.get('X-License-Key')
        if not key or key != LICENSE_KEY:
            return jsonify({"msg": "🚫 GEÇERSİZ LİSANS!", "error": True}), 403
        return f(*args, **kwargs)
    return decorated_function

# --- HTML (MATRIX & LOGIN & SOCIAL) ---
HTML_HOME = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YAEL /// CLOUD CONTROL</title>
    <link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;700&family=Share+Tech+Mono&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root { --neon: #00f3ff; --bg: #020202; --panel: #0a0a0a; --danger: #ff0055; --success: #00ff9d; }
        body { background-color: var(--bg); color: var(--neon); font-family: 'Rajdhani', sans-serif; margin: 0; padding: 0; overflow-x: hidden; }
        
        /* GİRİŞ EKRANI */
        #login-overlay {
            position: fixed; top: 0; left: 0; width: 100%; height: 100vh;
            background: black; z-index: 9999; display: flex; flex-direction: column;
            justify-content: center; align-items: center; transition: opacity 0.5s;
        }
        .login-box { text-align: center; border: 2px solid var(--neon); padding: 40px; border-radius: 10px; box-shadow: 0 0 50px rgba(0, 243, 255, 0.1); }
        
        /* ANA PANEL */
        .main-container { padding: 20px; max-width: 800px; margin: 0 auto; display: none; opacity: 0; transition: opacity 1s; }
        
        h1 { font-size: 3rem; text-shadow: 0 0 20px var(--neon); margin: 10px 0; text-align: center; }
        .subtitle { color: #666; text-align: center; margin-bottom: 30px; letter-spacing: 3px; }

        input { 
            padding: 15px; background: rgba(255,255,255,0.05); border: 1px solid #333; 
            color: white; font-family: 'Share Tech Mono', monospace; font-size: 1.1rem; border-radius: 4px; width: 100%; box-sizing: border-box;
        }
        
        .btn-group { display: flex; gap: 10px; margin-top: 10px; }
        button { 
            flex: 1; padding: 15px; font-weight: 800; font-size: 1rem; border: none; cursor: pointer; border-radius: 4px; transition: 0.3s;
        }
        .btn-start { background: var(--neon); color: black; box-shadow: 0 0 15px var(--neon); }
        .btn-stop { background: var(--danger); color: white; box-shadow: 0 0 15px var(--danger); }
        .btn-reset { background: #333; color: #aaa; margin-top: 30px; width: 100%; }

        .card { 
            background: var(--panel); border: 1px solid #222; margin-top: 20px; padding: 20px;
            border-left: 4px solid #333; position: relative; animation: slideIn 0.5s ease;
        }
        .card.active { border-left-color: var(--neon); }
        .card.completed { border-left-color: var(--success); }
        .card.error { border-left-color: var(--danger); }

        .matrix-logs {
            background: #000; color: #00ff00; font-family: 'Share Tech Mono', monospace;
            font-size: 0.8rem; padding: 10px; height: 100px; overflow: hidden;
            border: 1px solid #222; margin-top: 10px; opacity: 0.8;
            border-left: 2px solid #00ff00;
        }
        .log-line { white-space: nowrap; overflow: hidden; animation: type 0.5s steps(40, end); }

        .social-icons { display: flex; justify-content: center; gap: 20px; margin-top: 40px; }
        .social-btn { 
            color: #888; font-size: 1.5rem; transition: 0.3s; text-decoration: none; display: flex; align-items: center; gap: 10px;
        }
        .social-btn:hover { color: var(--neon); transform: scale(1.1); text-shadow: 0 0 10px var(--neon); }
        
        @keyframes slideIn { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
    </style>
</head>
<body>

    <div id="login-overlay">
        <div class="login-box">
            <h2 style="margin-top:0">SECURE GATEWAY</h2>
            <input type="password" id="login-key" placeholder="ACCESS KEY..." style="margin-bottom: 20px;">
            <button onclick="login()" class="btn-start">SİSTEME GİRİŞ</button>
        </div>
    </div>

    <div class="main-container" id="dashboard">
        <h1>YAEL CLOUD</h1>
        <div class="subtitle">/// ULTIMATE MEGA TRANSFER</div>

        <input type="text" id="link" placeholder="MEGA LINKINI YAPIŞTIR...">
        
        <div class="btn-group">
            <button onclick="send()" class="btn-start">BAŞLAT 🚀</button>
            <button onclick="stopJob()" class="btn-stop">DURDUR ⛔</button>
        </div>

        <div id="list"></div>
        
        <button onclick="reset()" class="btn-reset">⚠️ GEÇMİŞİ TEMİZLE</button>

        <div class="social-icons">
            <a href="https://t.me/yasin33" target="_blank" class="social-btn"><i class="fab fa-telegram"></i> @yasin33</a>
            <a href="https://instagram.com/mysthraw" target="_blank" class="social-btn"><i class="fab fa-instagram"></i> @mysthraw</a>
        </div>
    </div>

    <script>
        function login() {
            let k = document.getElementById('login-key').value;
            if(k === "YAEL2026") { 
                localStorage.setItem('yael_key', k);
                showDashboard();
            } else { alert("HATALI ANAHTAR!"); }
        }

        function showDashboard() {
            document.getElementById('login-overlay').style.opacity = '0';
            setTimeout(() => {
                document.getElementById('login-overlay').style.display = 'none';
                let dash = document.getElementById('dashboard');
                dash.style.display = 'block';
                setTimeout(() => dash.style.opacity = '1', 100);
            }, 500);
            load();
        }

        if(localStorage.getItem('yael_key') === "YAEL2026") showDashboard();

        function send() {
            var k = localStorage.getItem('yael_key');
            var l = document.getElementById('link').value;
            fetch('/add', {method:'POST', headers:{'Content-Type':'application/json', 'X-License-Key':k}, body:JSON.stringify({link:l})})
            .then(r=>r.json()).then(d=>{ alert(d.msg); load(); });
        }
        
        function stopJob() {
            var k = localStorage.getItem('yael_key');
            if(confirm("Durdurmak istiyor musun?")) {
                fetch('/stop', {headers:{'X-License-Key':k}}).then(r=>r.json()).then(d=>{ alert(d.msg); load(); });
            }
        }
        
        function reset() {
            var k = localStorage.getItem('yael_key');
            if(confirm("Tüm kayıtlar silinecek!")) {
                fetch('/reset', {headers:{'X-License-Key':k}}).then(r=>r.json()).then(d=>{ load(); });
            }
        }

        const fakeLogs = ["Bypassing Mega encryption...", "Allocating AWS-S3 bucket...", "Checking hash integrity...", "Optimizing TCP streams..."];

        function load() {
            fetch('/list').then(r=>r.json()).then(d=>{
                var h = "";
                d.forEach(i=>{
                    let statusHtml = '';
                    let extraHtml = '';
                    
                    if(i.status === 'TAMAMLANDI') {
                        statusHtml = `<span style="color:#00ff9d">✅ İŞLEM TAMAMLANDI</span>`;
                        // İŞTE BURASI: Artık HTML içeriğini gösteren özel sayfaya yönlendiriyor
                        extraHtml = `<a href="/teslimat/${i.delivery_id}" target="_blank" style="display:block; background:#00ff9d; color:black; padding:10px; text-align:center; text-decoration:none; font-weight:bold; margin-top:10px;">📂 DOSYALARI AÇ</a>`;
                    } else if(i.status.startsWith('HATA') || i.status.includes('DURDUR')) {
                        statusHtml = `<span style="color:#ff0055">⚠️ ${i.status}</span>`;
                    } else if(i.status === 'SIRADA') {
                         statusHtml = `<span style="color:#aaa">⏳ KUYRUKTA</span>`;
                    } else {
                        statusHtml = `<span style="color:#00f3ff">⚙️ VERİ İŞLENİYOR</span>`;
                        extraHtml = `<div class="matrix-logs"><div class="log-line">> ${fakeLogs[Math.floor(Math.random()*fakeLogs.length)]}</div></div>`;
                    }

                    h += `<div class="card ${i.status === 'ISLENIYOR' ? 'active' : ''}">
                        <div style="font-size:0.8rem; color:#888;">${i.date}</div>
                        <div style="font-weight:bold;">${i.link}</div>
                        <div style="margin-top:10px;">${statusHtml}</div>
                        ${extraHtml}
                    </div>`;
                });
                document.getElementById('list').innerHTML = h;
            });
        }
        setInterval(load, 3000);
    </script>
</body>
</html>
"""

@app.route('/')
def home(): return render_template_string(HTML_HOME)

# --- KRİTİK KISIM: TESLİMAT SAYFASI ---
@app.route('/teslimat/<id>')
def show_delivery(id):
    # Bu fonksiyon veritabanından HTML kodunu çeker ve site gibi gösterir
    data = deliveries.find_one({"id": id})
    if data: return render_template_string(data['html'])
    return "<h1>404 - TESLİMAT BULUNAMADI</h1><p>Belki veritabanı sıfırlanmıştır?</p>", 404

# API ROUTES
@app.route('/add', methods=['POST'])
@require_license
def add():
    link = request.json.get('link')
    if not link: return jsonify({"msg": "Link yok"})
    queue.insert_one({"link": link, "status": "SIRADA", "delivery_id": None, "date": str(datetime.datetime.now())[:19]})
    return jsonify({"msg": "Sıraya Alındı"})

@app.route('/stop', methods=['GET'])
@require_license
def stop_job():
    queue.update_many({"status": {"$in": ["SIRADA", "ISLENIYOR"]}}, {"$set": {"status": "DURDURULDU"}})
    return jsonify({"msg": "Durduruldu."})

@app.route('/reset', methods=['GET'])
@require_license
def reset():
    queue.delete_many({}) 
    deliveries.delete_many({}) # Teslimatları da sil
    return jsonify({"msg": "Temizlendi."})

@app.route('/list')
def list_jobs():
    return jsonify(list(queue.find({}, {'_id':0}).sort("_id", -1).limit(5)))

@app.route('/api/get_job')
def get_job():
    job = queue.find_one({"status": "SIRADA"})
    if job:
        queue.update_one({"link": job['link']}, {"$set": {"status": "ISLENIYOR"}})
        return jsonify({"found": True, "link": job['link']})
    return jsonify({"found": False})

@app.route('/api/update_status', methods=['POST'])
def update_status():
    d = request.json
    current = queue.find_one({"link": d['link']})
    if current and "DURDURULDU" in current['status']: return jsonify({"status": "stopped"})
    queue.update_one({"link": d['link']}, {"$set": {"status": d['status']}})
    return jsonify({"status": "ok"})

# --- İŞTE BURASI DÜZELTİLDİ ---
# Worker'dan gelen HTML'i alıp 'deliveries' tablosuna kaydediyor
@app.route('/api/done', methods=['POST'])
def done():
    d = request.json
    link = d['link']
    if "html_content" in d:
        delivery_id = str(uuid.uuid4())[:8]
        # HTML'i kaydet
        deliveries.insert_one({"id": delivery_id, "html": d['html_content'], "date": datetime.datetime.now()})
        # Kuyruğu güncelle ve ID'yi ekle
        queue.update_one({"link": link}, {"$set": {"status": "TAMAMLANDI", "delivery_id": delivery_id}})
    else:
        queue.update_one({"link": link}, {"$set": {"status": d.get('url', 'HATA')}})
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
