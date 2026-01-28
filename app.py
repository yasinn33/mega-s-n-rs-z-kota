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

# --- HTML ANASAYFA (ŞIKIR ŞIKIR TASARIM) ---
HTML_HOME = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YAEL /// CLOUD TRANSFER</title>
    <link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;700&display=swap" rel="stylesheet">
    <style>
        :root { --neon: #00f3ff; --bg: #050505; --panel: #0a0a0a; --danger: #ff0055; --success: #00ff9d; }
        body { background-color: var(--bg); color: var(--neon); font-family: 'Rajdhani', sans-serif; margin: 0; padding: 20px; display: flex; flex-direction: column; align-items: center; min-height: 100vh; background-image: radial-gradient(circle at 50% 10%, #1a1a1a 0%, #000 100%); }
        
        h1 { font-size: 3rem; text-shadow: 0 0 20px var(--neon); margin-bottom: 5px; letter-spacing: 2px; }
        .subtitle { color: #666; font-size: 0.9rem; margin-bottom: 40px; letter-spacing: 5px; }

        .container { width: 100%; max-width: 700px; z-index: 2; }
        
        .input-group { display: flex; gap: 10px; margin-bottom: 20px; }
        input { 
            flex: 1; padding: 15px; background: rgba(255,255,255,0.05); border: 1px solid #333; 
            color: white; font-family: inherit; font-size: 1.1rem; border-radius: 4px; transition: 0.3s;
        }
        input:focus { outline: none; border-color: var(--neon); box-shadow: 0 0 15px rgba(0, 243, 255, 0.2); }
        
        button { 
            padding: 15px 30px; background: var(--neon); color: black; font-weight: 800; font-size: 1.1rem;
            border: none; cursor: pointer; border-radius: 4px; transition: 0.3s;
            box-shadow: 0 0 10px var(--neon);
        }
        button:hover { transform: translateY(-2px); box-shadow: 0 0 20px var(--neon); }

        .card { 
            background: var(--panel); border: 1px solid #222; margin-bottom: 15px; padding: 20px;
            border-left: 4px solid #333; position: relative; overflow: hidden; animation: slideIn 0.4s ease;
        }
        .card.active { border-left-color: var(--neon); }
        .card.completed { border-left-color: var(--success); }
        .card.error { border-left-color: var(--danger); }

        .job-link { color: white; font-size: 1rem; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; margin-bottom: 10px; opacity: 0.8; }
        
        /* İLERLEME ÇUBUĞU */
        .progress-bg { width: 100%; background: #222; height: 6px; border-radius: 3px; overflow: hidden; margin-top: 10px; }
        .progress-bar { height: 100%; background: var(--neon); width: 0%; transition: width 0.5s ease; box-shadow: 0 0 10px var(--neon); }
        .progress-bar.striped { 
            background-image: linear-gradient(45deg,rgba(255,255,255,.15) 25%,transparent 25%,transparent 50%,rgba(255,255,255,.15) 50%,rgba(255,255,255,.15) 75%,transparent 75%,transparent);
            background-size: 1rem 1rem; animation: stripe 1s linear infinite;
        }
        
        .status-row { display: flex; justify-content: space-between; font-size: 0.8rem; margin-top: 8px; color: #888; text-transform: uppercase; }
        .status-text { color: var(--neon); font-weight: bold; }

        .btn-download { 
            display: block; width: 100%; text-align: center; padding: 12px; margin-top: 10px;
            background: transparent; border: 1px solid var(--success); color: var(--success); 
            text-decoration: none; font-weight: bold; transition: 0.3s;
        }
        .btn-download:hover { background: var(--success); color: black; box-shadow: 0 0 15px var(--success); }

        @keyframes stripe { from { background-position: 1rem 0; } to { background-position: 0 0; } }
        @keyframes slideIn { from { transform: translateY(10px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
    </style>
</head>
<body>
    <h1>YAEL TRANSFER</h1>
    <div class="subtitle">/// UNLIMITED MEGA.NZ BRIDGE</div>

    <div class="container">
        <div id="login-area" style="text-align:center; margin-bottom:30px;">
            <input type="password" id="key" placeholder="🔒 LİSANS ANAHTARI" style="width: 50%;">
        </div>

        <div class="input-group">
            <input type="text" id="link" placeholder="Mega.nz Linkini Yapıştır...">
            <button onclick="send()">BAŞLAT 🚀</button>
        </div>
        
        <div id="list"></div>
        
        <button onclick="reset()" style="background:transparent; border:1px solid #333; color:#444; font-size:0.8rem; margin-top:50px; padding:10px;">TEMİZLE</button>
    </div>

    <script>
        // Basit localStorage kullanımı (Şifreyi hatırla)
        if(localStorage.getItem('yael_key')) document.getElementById('key').value = localStorage.getItem('yael_key');

        function send() {
            var k = document.getElementById('key').value;
            var l = document.getElementById('link').value;
            if(!k) return alert("Lisans anahtarı gir!");
            
            localStorage.setItem('yael_key', k); // Kaydet

            fetch('/add', {method:'POST', headers:{'Content-Type':'application/json', 'X-License-Key':k}, body:JSON.stringify({link:l})})
            .then(r=>r.json()).then(d=>{ 
                if(d.error) alert(d.msg); 
                else { load(); document.getElementById('link').value=''; }
            });
        }
        
        function reset() {
            var k = document.getElementById('key').value;
            if(confirm("Tüm liste silinsin mi?")) {
                fetch('/reset', {headers:{'X-License-Key':k}}).then(()=>load());
            }
        }

        function load() {
            fetch('/list').then(r=>r.json()).then(d=>{
                var h = "";
                d.forEach(i=>{
                    let cardClass = '';
                    let progressHtml = '';
                    let statusHtml = '';
                    
                    if(i.status === 'SIRADA') {
                        cardClass = '';
                        statusHtml = `<span class="status-text">BEKLİYOR...</span><span>Sıra No: 1</span>`;
                        progressHtml = `<div class="progress-bg"><div class="progress-bar" style="width: 5%"></div></div>`;
                    } else if(i.status === 'TAMAMLANDI') {
                        cardClass = 'completed';
                        statusHtml = `<span style="color:#00ff9d">✅ İŞLEM BİTTİ</span><span>%100</span>`;
                        progressHtml = `<a href="/teslimat/${i.delivery_id}" target="_blank" class="btn-download">📂 DOSYALARI AÇ</a>`;
                    } else if(i.status.startsWith('HATA')) {
                        cardClass = 'error';
                        statusHtml = `<span style="color:#ff0055">⚠️ ${i.status}</span>`;
                    } else {
                        // İşleniyor Durumu (Yüzdeyi tahmin etmeye çalışırız veya sabit animasyon)
                        cardClass = 'active';
                        // Mesajdan yüzdeyi anlamaya çalış (Opsiyonel, şimdilik animasyonlu bar)
                        statusHtml = `<span class="status-text">${i.status}</span><span>İŞLENİYOR</span>`;
                        progressHtml = `<div class="progress-bg"><div class="progress-bar striped" style="width: 60%"></div></div>`;
                    }

                    h += `
                    <div class="card ${cardClass}">
                        <div class="job-link">${i.link}</div>
                        <div class="status-row">${statusHtml}</div>
                        ${progressHtml}
                    </div>`;
                });
                document.getElementById('list').innerHTML = h;
            });
        }
        setInterval(load, 2000);
        load();
    </script>
</body>
</html>
"""

@app.route('/')
def home(): return render_template_string(HTML_HOME)

@app.route('/teslimat/<id>')
def show_delivery(id):
    data = deliveries.find_one({"id": id})
    if data: return render_template_string(data['html'])
    return "TESLİMAT BULUNAMADI.", 404

# API ROUTES (Öncekilerin aynısı, sadece güvenlik eklendi)
@app.route('/add', methods=['POST'])
@require_license
def add():
    link = request.json.get('link')
    if not link: return jsonify({"msg": "Link yok"})
    queue.insert_one({"link": link, "status": "SIRADA", "delivery_id": None, "date": str(datetime.datetime.now())})
    return jsonify({"msg": "Sıraya Alındı"})

@app.route('/list')
def list_jobs():
    return jsonify(list(queue.find({}, {'_id':0}).sort("_id", -1).limit(10)))

@app.route('/api/get_job')
def get_job():
    job = queue.find_one({"status": "SIRADA"})
    if job:
        queue.update_one({"link": job['link']}, {"$set": {"status": "BAŞLATILIYOR..."}})
        return jsonify({"found": True, "link": job['link']})
    return jsonify({"found": False})

@app.route('/api/update_status', methods=['POST'])
def update_status():
    d = request.json
    queue.update_one({"link": d['link']}, {"$set": {"status": d['status']}})
    return jsonify({"status": "ok"})

@app.route('/api/done', methods=['POST'])
def done():
    d = request.json
    link = d['link']
    if "html_content" in d:
        delivery_id = str(uuid.uuid4())[:8]
        deliveries.insert_one({"id": delivery_id, "html": d['html_content'], "date": datetime.datetime.now()})
        queue.update_one({"link": link}, {"$set": {"status": "TAMAMLANDI", "delivery_id": delivery_id}})
    else:
        queue.update_one({"link": link}, {"$set": {"status": d.get('url', 'HATA')}})
    return jsonify({"status": "ok"})

@app.route('/reset')
@require_license
def reset():
    queue.delete_many({})
    return jsonify({"msg": "Temizlendi"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
