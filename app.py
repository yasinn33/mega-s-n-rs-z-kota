import certifi
from flask import Flask, request, jsonify, render_template_string
from pymongo import MongoClient
from functools import wraps
import os
import datetime

app = Flask(__name__)

# --- AYARLAR ---
# BURAYI DEGISTIR AGAM (Giris Sifresi)
LICENSE_KEY = "YAEL-CODE-2026" 

# Veritabanı
MONGO_URI = os.environ.get("MONGO_URI") 
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['mega_leech']
queue = db['queue']

# --- GÜVENLİK KONTROLÜ (DECORATOR) ---
def require_license(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Header'dan veya JSON'dan anahtarı kontrol et
        key = request.headers.get('X-License-Key')
        if not key:
            return jsonify({"msg": "❌ LİSANS ANAHTARI EKSİK!", "error": True}), 403
        if key != LICENSE_KEY:
            return jsonify({"msg": "🚫 GEÇERSİZ LİSANS!", "error": True}), 403
        return f(*args, **kwargs)
    return decorated_function

# --- HTML ARAYÜZ (GİRİŞ EKRANLI) ---
HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YAEL /// SECURE ACCESS</title>
    <link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap" rel="stylesheet">
    <style>
        :root { --neon: #00f3ff; --bg: #050505; --panel: #111; --danger: #ff0055; }
        body { background-color: var(--bg); color: var(--neon); font-family: 'Share Tech Mono', monospace; margin: 0; padding: 20px; display: flex; flex-direction: column; align-items: center; min-height: 100vh; }
        
        /* GİRİŞ EKRANI (LOGIN OVERLAY) */
        #login-overlay {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: #000; z-index: 9999; display: flex; flex-direction: column;
            justify-content: center; align-items: center;
        }
        .login-box {
            border: 2px solid var(--neon); padding: 40px; text-align: center;
            box-shadow: 0 0 50px rgba(0, 243, 255, 0.2); background: #111;
            max-width: 400px; width: 90%;
        }
        
        /* ANA SAYFA */
        h1 { text-shadow: 0 0 20px var(--neon); letter-spacing: 5px; margin-bottom: 30px; }
        .container { width: 100%; max-width: 800px; filter: blur(5px); transition: 0.5s; pointer-events: none; }
        .container.unlocked { filter: blur(0); pointer-events: all; }

        input { 
            padding: 15px; background: #222; border: 1px solid #444; color: white; 
            font-family: inherit; font-size: 1.1rem; width: 70%; margin-bottom: 10px;
        }
        button { 
            padding: 15px 30px; background: var(--neon); color: black; font-weight: bold; 
            border: none; cursor: pointer; font-family: inherit; font-size: 1.1rem;
            transition: 0.3s;
        }
        button:hover { transform: scale(1.05); box-shadow: 0 0 15px var(--neon); }

        .card { 
            background: #111; border: 1px solid #333; margin: 10px 0; padding: 15px;
            display: flex; justify-content: space-between; align-items: center;
        }
        .status { font-weight: bold; }
        .completed a { color: #00ff00; text-decoration: none; border: 1px solid #00ff00; padding: 5px 10px; }
        
        .reset-btn { background: transparent; border: 1px solid var(--danger); color: var(--danger); margin-top: 50px; }
        .reset-btn:hover { background: var(--danger); color: white; }
    </style>
</head>
<body>

    <div id="login-overlay">
        <div class="login-box">
            <h2 style="margin-top:0">SECURITY CHECK</h2>
            <p>LÜTFEN LİSANS ANAHTARINI GİRİN</p>
            <input type="password" id="license-input" placeholder="LICENSE KEY...">
            <br><br>
            <button onclick="login()">SİSTEME GİRİŞ</button>
            <p id="login-msg" style="color: red; margin-top: 10px;"></p>
        </div>
    </div>

    <h1>YAEL SYSTEM</h1>
    <div class="container" id="main-panel">
        <div style="display:flex; gap:10px;">
            <input type="text" id="link" placeholder="MEGA LINKINI BURAYA YAPISTIR...">
            <button onclick="sendJob()">BAŞLAT</button>
        </div>
        <div id="list"></div>
        
        <br>
        <button onclick="resetSystem()" class="reset-btn">⚠️ SİSTEMİ SIFIRLA / RESET</button>
    </div>

    <script>
        // --- GİRİŞ SİSTEMİ ---
        let USER_KEY = localStorage.getItem("YAEL_KEY");

        function login() {
            let key = document.getElementById('license-input').value;
            if(!key) return;
            
            // Basit bir ön kontrol, asıl kontrol sunucuda
            USER_KEY = key;
            localStorage.setItem("YAEL_KEY", key);
            checkAccess();
        }

        function checkAccess() {
            if(USER_KEY) {
                document.getElementById('login-overlay').style.display = 'none';
                document.getElementById('main-panel').classList.add('unlocked');
                loadList(); // Listeyi yüklemeye başla
            }
        }
        
        // Sayfa açılınca kayıtlı şifre varsa direkt aç
        if(USER_KEY) checkAccess();

        // --- BUTON FONKSİYONLARI ---
        async function sendJob() {
            let l = document.getElementById('link').value;
            if(!l) return alert("Link boş!");

            try {
                let r = await fetch('/add', {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'X-License-Key': USER_KEY // Şifreyi gönder
                    },
                    body: JSON.stringify({link: l})
                });
                let d = await r.json();
                
                if(r.status === 403) {
                    alert("GİRİŞ BAŞARISIZ: " + d.msg);
                    logout(); // Şifre yanlışsa at
                } else {
                    alert(d.msg);
                    document.getElementById('link').value = '';
                    loadList();
                }
            } catch(e) {
                alert("HATA OLUŞTU: " + e);
            }
        }

        async function resetSystem() {
            if(!confirm("TÜM KUYRUK SİLİNSİN Mİ?")) return;
            
            try {
                let r = await fetch('/reset', {
                    method: 'GET',
                    headers: { 'X-License-Key': USER_KEY }
                });
                let d = await r.json();
                alert(d.msg);
                loadList();
            } catch(e) {
                alert("Reset Hatası: " + e);
            }
        }

        function logout() {
            localStorage.removeItem("YAEL_KEY");
            location.reload();
        }

        function loadList() {
            fetch('/list').then(r=>r.json()).then(d=>{
                let h = "";
                d.forEach(i=>{
                    let status = i.status;
                    let action = "";
                    
                    if(status === 'TAMAMLANDI') {
                        action = `<span class="completed"><a href="${i.gofile}" target="_blank">LİSTEYİ İNDİR</a></span>`;
                    } else if(status.startsWith('HATA')) {
                        action = `<span style="color:red">${status}</span>`;
                    } else {
                        action = `<span style="color:orange">${status}</span>`;
                    }

                    h += `<div class="card">
                            <div style="font-size:0.8rem; overflow:hidden; width:60%;">${i.link}</div>
                            <div>${action}</div>
                          </div>`;
                });
                document.getElementById('list').innerHTML = h;
            });
        }
        
        // Otomatik yenile
        setInterval(() => {
            if(document.getElementById('main-panel').classList.contains('unlocked')){
                loadList();
            }
        }, 3000);
    </script>
</body>
</html>
"""

@app.route('/')
def home(): return render_template_string(HTML)

# --- KORUMALI ROTALAR ---
@app.route('/add', methods=['POST'])
@require_license # <-- BU ARTIK ŞİFRE İSTER
def add():
    link = request.json.get('link')
    if not link: return jsonify({"msg": "Link yok"})
    
    # Kuyruğa ekle
    queue.insert_one({
        "link": link, 
        "status": "SIRADA", 
        "gofile": None, 
        "date": str(datetime.datetime.now())
    })
    return jsonify({"msg": "Sıraya Alındı!"})

@app.route('/reset')
@require_license # <-- BU ARTIK ŞİFRE İSTER
def reset():
    queue.delete_many({})
    return jsonify({"msg": "Sistem Temizlendi!"})

# --- AÇIK ROTALAR (İşçi ve Liste için) ---
@app.route('/list')
def list_jobs():
    # Liste herkese görünebilir ama işlem yapılamaz
    return jsonify(list(queue.find({}, {'_id':0}).sort("_id", -1).limit(10)))

@app.route('/api/update_status', methods=['POST'])
def update_status():
    d = request.json
    queue.update_one({"link": d['link']}, {"$set": {"status": d['status']}})
    return jsonify({"status": "ok"})

@app.route('/api/get_job')
def get_job():
    job = queue.find_one({"status": "SIRADA"})
    if job:
        queue.update_one({"link": job['link']}, {"$set": {"status": "ISLENIYOR"}})
        return jsonify({"found": True, "link": job['link']})
    return jsonify({"found": False})

@app.route('/api/done', methods=['POST'])
def done():
    d = request.json
    status = "TAMAMLANDI" if d['url'] and "http" in d['url'] else "HATA"
    queue.update_one({"link": d['link']}, {"$set": {"status": status, "gofile": d['url']}})
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
