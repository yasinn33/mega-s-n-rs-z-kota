import certifi
from flask import Flask, request, jsonify, render_template_string
from pymongo import MongoClient
import os
import datetime

app = Flask(__name__)

# Veritabanı
MONGO_URI = os.environ.get("MONGO_URI") 
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['mega_leech']
queue = db['queue']
history = db['history']

# MODERN CYBERPUNK TASARIM (CSS + JS)
HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YAEL /// UNLIMITED</title>
    <link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap" rel="stylesheet">
    <style>
        :root { --neon: #00f3ff; --bg: #050505; --panel: #111; --danger: #ff0055; }
        body { background-color: var(--bg); color: var(--neon); font-family: 'Share Tech Mono', monospace; margin: 0; padding: 20px; display: flex; flex-direction: column; align-items: center; min-height: 100vh; background-image: radial-gradient(circle at 50% 50%, #111 0%, #000 100%); }
        
        h1 { font-size: 3rem; text-shadow: 0 0 20px var(--neon); letter-spacing: 5px; margin-bottom: 10px; }
        .subtitle { color: #888; font-size: 0.9rem; margin-bottom: 40px; letter-spacing: 2px; }

        .container { width: 100%; max-width: 800px; position: relative; z-index: 2; }
        
        /* INPUT ALANI */
        .input-group { display: flex; gap: 10px; margin-bottom: 30px; position: relative; }
        input { 
            flex: 1; padding: 20px; background: rgba(0,0,0,0.7); border: 2px solid #333; 
            color: white; font-family: 'Share Tech Mono', monospace; font-size: 1.2rem;
            border-radius: 4px; transition: 0.3s;
        }
        input:focus { outline: none; border-color: var(--neon); box-shadow: 0 0 15px rgba(0, 243, 255, 0.3); }
        
        button { 
            padding: 0 40px; background: var(--neon); color: black; font-weight: bold; font-size: 1.2rem;
            border: none; cursor: pointer; border-radius: 4px; font-family: 'Share Tech Mono', monospace;
            transition: 0.3s; clip-path: polygon(10% 0, 100% 0, 100% 90%, 90% 100%, 0 100%, 0 10%);
        }
        button:hover { transform: scale(1.05); box-shadow: 0 0 20px var(--neon); }

        /* KARTLAR */
        .card { 
            background: rgba(20, 20, 20, 0.9); border: 1px solid #333; margin-bottom: 15px; padding: 20px;
            border-left: 5px solid #333; position: relative; overflow: hidden; animation: slideIn 0.5s ease;
        }
        .card.active { border-left-color: var(--neon); box-shadow: 0 0 15px rgba(0, 243, 255, 0.1); }
        .card.completed { border-left-color: #00ff00; }
        .card.error { border-left-color: var(--danger); }

        .job-header { display: flex; justify-content: space-between; margin-bottom: 10px; font-size: 0.9rem; color: #aaa; }
        .job-link { color: white; font-size: 1.1rem; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; max-width: 70%; margin-bottom: 15px; }
        
        /* İLERLEME ÇUBUĞU */
        .progress-container { width: 100%; background: #222; height: 6px; border-radius: 3px; overflow: hidden; position: relative; }
        .progress-bar { height: 100%; background: var(--neon); width: 0%; transition: width 0.5s; box-shadow: 0 0 10px var(--neon); }
        .progress-bar.striped { 
            background-image: linear-gradient(45deg,rgba(255,255,255,.15) 25%,transparent 25%,transparent 50%,rgba(255,255,255,.15) 50%,rgba(255,255,255,.15) 75%,transparent 75%,transparent);
            background-size: 1rem 1rem; animation: stripe 1s linear infinite;
        }
        
        .status-text { margin-top: 8px; font-size: 0.85rem; color: var(--neon); text-transform: uppercase; display: flex; justify-content: space-between; }
        
        .download-btn { 
            display: inline-block; padding: 10px 20px; background: transparent; border: 2px solid #00ff00; 
            color: #00ff00; text-decoration: none; font-weight: bold; margin-top: 10px;
            transition: 0.3s;
        }
        .download-btn:hover { background: #00ff00; color: black; box-shadow: 0 0 20px #00ff00; }

        .reset-section { margin-top: 50px; text-align: center; opacity: 0.5; transition: 0.3s; }
        .reset-section:hover { opacity: 1; }
        .btn-danger { background: transparent; border: 1px solid var(--danger); color: var(--danger); font-size: 0.8rem; }
        .btn-danger:hover { background: var(--danger); color: white; }

        @keyframes stripe { from { background-position: 1rem 0; } to { background-position: 0 0; } }
        @keyframes slideIn { from { transform: translateX(-20px); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
    </style>
</head>
<body>
    <h1>YAEL SYSTEM</h1>
    <div class="subtitle">/// MEGA.NZ BYPASS & LEECH PROTOCOL_</div>

    <div class="container">
        <div class="input-group">
            <input type="text" id="link" placeholder="MEGA LINKINI BURAYA YAPISTIR...">
            <button onclick="send()">BAŞLAT</button>
        </div>
        <div id="list"></div>
        
        <div class="reset-section">
            <button onclick="resetQueue()" class="btn-danger">⚠️ SİSTEMİ SIFIRLA / RESET SYSTEM</button>
        </div>
    </div>

    <script>
        function send() {
            var l = document.getElementById('link').value;
            if(!l) return alert("LINK GIRMEDIN AGAM!");
            fetch('/add', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({link:l})})
            .then(r=>r.json()).then(d=>{ document.getElementById('link').value=''; load(); });
        }
        
        function resetQueue() {
            if(confirm("TÜM İŞLEMLER SİLİNECEK?")) {
                fetch('/reset').then(r=>r.json()).then(d=>{ load(); });
            }
        }

        function load() {
            fetch('/list').then(r=>r.json()).then(d=>{
                var h = "";
                d.forEach(i=>{
                    let statusHtml = '';
                    let cardClass = '';
                    let progressWidth = '0%';
                    let progressClass = '';
                    
                    // Duruma göre tasarım
                    if(i.status === 'SIRADA') {
                        cardClass = '';
                        statusHtml = '<span>KUYRUKTA BEKLIYOR...</span><span>%0</span>';
                    } else if(i.status === 'INDIRILIYOR') {
                        cardClass = 'active';
                        progressWidth = '40%';
                        progressClass = 'striped';
                        statusHtml = '<span>MEGA\'DAN İNDİRİLİYOR...</span><span>%40</span>';
                    } else if(i.status.startsWith('YUKLENIYOR')) {
                        cardClass = 'active';
                        progressWidth = '80%';
                        progressClass = 'striped';
                        statusHtml = `<span>${i.status}</span><span>%80</span>`;
                    } else if(i.status === 'TAMAMLANDI') {
                        cardClass = 'completed';
                        progressWidth = '100%';
                        statusHtml = `<a href="${i.gofile}" target="_blank" class="download-btn">DOSYALARI İNDİR (GOFILE)</a>`;
                    } else {
                        cardClass = 'error';
                        statusHtml = `<span>HATA: ${i.gofile}</span>`;
                    }

                    h += `
                    <div class="card ${cardClass}">
                        <div class="job-header">
                            <span>ID: ${i.date}</span>
                            <span>${i.status}</span>
                        </div>
                        <div class="job-link">${i.link}</div>
                        ${i.status !== 'TAMAMLANDI' && i.status !== 'HATA' ? 
                            `<div class="progress-container"><div class="progress-bar ${progressClass}" style="width: ${progressWidth}"></div></div>` : ''}
                        <div class="status-text">${statusHtml}</div>
                    </div>`;
                });
                document.getElementById('list').innerHTML = h;
            });
        }
        setInterval(load, 2000); // 2 saniyede bir güncelle
        load();
    </script>
</body>
</html>
"""

@app.route('/')
def home(): return render_template_string(HTML)

@app.route('/add', methods=['POST'])
def add():
    link = request.json.get('link')
    if not link: return jsonify({"msg": "Link yok"})
    # Status başlangıcı: SIRADA
    queue.insert_one({"link": link, "status": "SIRADA", "gofile": None, "date": str(datetime.datetime.now().time())[:8]})
    return jsonify({"msg": "OK"})

@app.route('/list')
def list_jobs():
    return jsonify(list(queue.find({}, {'_id':0}).sort("_id", -1).limit(5)))

# İşçinin durumu güncellemesi için yeni API
@app.route('/api/update_status', methods=['POST'])
def update_status():
    d = request.json
    queue.update_one({"link": d['link']}, {"$set": {"status": d['status']}})
    return jsonify({"status": "ok"})

@app.route('/api/get_job')
def get_job():
    job = queue.find_one({"status": "SIRADA"})
    if job:
        queue.update_one({"link": job['link']}, {"$set": {"status": "INDIRILIYOR"}})
        return jsonify({"found": True, "link": job['link']})
    return jsonify({"found": False})

@app.route('/api/done', methods=['POST'])
def done():
    d = request.json
    status = "TAMAMLANDI" if d['url'] and "http" in d['url'] else "HATA"
    queue.update_one({"link": d['link']}, {"$set": {"status": status, "gofile": d['url']}})
    return jsonify({"status": "ok"})

@app.route('/reset')
def reset():
    queue.delete_many({})
    return jsonify({"msg": "Resetlendi"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
