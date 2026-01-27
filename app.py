import certifi
from flask import Flask, request, jsonify, render_template_string
from pymongo import MongoClient
import os
import datetime

app = Flask(__name__)

# Veritabanı Bağlantısı (SSL Hatalarına Karşı Korumalı)
MONGO_URI = os.environ.get("MONGO_URI") 
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['mega_leech']
queue = db['queue']
history = db['history'] # Geçmiş kayıtları buraya atacağız

# BYPASS.CITY Tarzı Modern Tasarım
HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YAEL CLOUD LEECHER</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root { --primary: #00ff9d; --bg: #0a0a0a; --card: #111; --text: #eee; }
        body { background-color: var(--bg); color: var(--text); font-family: 'Inter', sans-serif; display: flex; flex-direction: column; align-items: center; min-height: 100vh; margin: 0; padding: 20px; }
        h1 { font-family: 'JetBrains Mono', monospace; color: var(--primary); text-shadow: 0 0 10px rgba(0, 255, 157, 0.5); margin-bottom: 30px; }
        
        .container { width: 100%; max-width: 600px; }
        .input-group { display: flex; gap: 10px; margin-bottom: 20px; }
        
        input { 
            flex: 1; padding: 15px; border-radius: 8px; border: 1px solid #333; 
            background: #1a1a1a; color: white; font-family: 'JetBrains Mono', monospace;
            transition: 0.3s;
        }
        input:focus { outline: none; border-color: var(--primary); box-shadow: 0 0 10px rgba(0,255,157,0.2); }
        
        button {
            padding: 15px 30px; border-radius: 8px; border: none; 
            background: var(--primary); color: black; font-weight: bold; cursor: pointer;
            font-family: 'JetBrains Mono', monospace; transition: 0.3s;
        }
        button:hover { transform: translateY(-2px); box-shadow: 0 0 15px var(--primary); }

        .card { 
            background: var(--card); border: 1px solid #222; border-radius: 10px; 
            padding: 15px; margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center;
            animation: fadeIn 0.5s ease;
        }
        .status { font-size: 12px; font-weight: bold; padding: 5px 10px; border-radius: 4px; }
        .pending { background: #333; color: #aaa; }
        .processing { background: #007bff; color: white; animation: pulse 1.5s infinite; }
        .completed { background: var(--primary); color: black; }
        
        .link-text { font-family: 'JetBrains Mono', monospace; font-size: 13px; color: #888; max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        a { color: var(--primary); text-decoration: none; font-weight: bold; }
        
        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.6; } 100% { opacity: 1; } }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    </style>
</head>
<body>
    <h1>YAEL / MEGA BYPASS</h1>
    <div class="container">
        <div class="input-group">
            <input type="text" id="link" placeholder="Mega.nz Linkini Buraya Yapıştır...">
            <button onclick="send()">ÇEVİR</button>
        </div>
        <div id="list"></div>
    </div>

    <script>
        function send() {
            var l = document.getElementById('link').value;
            if(!l) return alert("Link boş olamaz!");
            fetch('/add', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({link:l})})
            .then(r=>r.json()).then(d=>{ alert(d.msg); document.getElementById('link').value = ''; load(); });
        }
        function load() {
            fetch('/list').then(r=>r.json()).then(d=>{
                var h = "";
                d.forEach(i=>{
                    let statusClass = i.status === 'ISLENIYOR' ? 'processing' : (i.status === 'TAMAMLANDI' ? 'completed' : 'pending');
                    let statusText = i.status;
                    let action = i.gofile ? `<a href="${i.gofile}" target="_blank">İNDİR ⬇</a>` : `<span class="status ${statusClass}">${statusText}</span>`;
                    
                    h += `<div class="card">
                            <div class="link-text">Original: ${i.link}</div>
                            <div>${action}</div>
                          </div>`;
                });
                document.getElementById('list').innerHTML = h;
            });
        }
        setInterval(load, 5000);
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
    # MongoDB'ye Kayıt (Loglama)
    job_data = {
        "link": link, 
        "status": "SIRADA", 
        "gofile": None, 
        "date": datetime.datetime.now()
    }
    queue.insert_one(job_data)
    
    # Ayrıca 'History' koleksiyonuna da yedek atalım (Silinmesin diye)
    history.insert_one({"original_link": link, "timestamp": datetime.datetime.now()})
    
    return jsonify({"msg": "Link sıraya alındı! İşleniyor..."})

@app.route('/list')
def list_jobs():
    # Sadece son 10 işlemi göster
    jobs = list(queue.find({}, {'_id':0}).sort("date", -1).limit(10))
    return jsonify(jobs)

# --- WORKER API ---
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
    # İş bitince durumu güncelle ve GoFile linkini kaydet
    queue.update_one({"link": d['link']}, {"$set": {"status": "TAMAMLANDI", "gofile": d['url']}})
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
