import certifi
from flask import Flask, request, jsonify, render_template_string
from pymongo import MongoClient
import os
import datetime

app = Flask(__name__)

# Veritabanı Bağlantısı
MONGO_URI = os.environ.get("MONGO_URI") 
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['mega_leech']
queue = db['queue']      # İşlenenler (Silinebilir)
history = db['history']  # KALICI GEÇMİŞ (Silinmez)

# HTML Arayüz
HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YAEL CLOUD LEECHER</title>
    <link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@600&display=swap" rel="stylesheet">
    <style>
        body { background-color: #050505; color: #00ff9d; font-family: 'Rajdhani', sans-serif; padding: 20px; text-align: center; }
        h1 { text-shadow: 0 0 20px #00ff9d; letter-spacing: 3px; }
        
        .container { max-width: 600px; margin: 0 auto; }
        
        input { 
            padding: 15px; width: 70%; background: #111; border: 1px solid #333; 
            color: white; border-radius: 5px; font-family: 'Rajdhani', sans-serif; font-size: 18px;
        }
        button { 
            padding: 15px 20px; cursor: pointer; background: #00ff9d; color: black; 
            border: none; font-weight: bold; border-radius: 5px; font-size: 18px;
        }
        button:hover { box-shadow: 0 0 15px #00ff9d; }

        .card { 
            border: 1px solid #222; padding: 15px; margin: 15px 0; 
            background: #0f0f0f; border-radius: 8px; text-align: left;
            display: flex; justify-content: space-between; align-items: center;
        }
        .link-info { font-size: 14px; color: #888; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; max-width: 70%; }
        
        a { color: #00ff9d; text-decoration: none; font-weight: bold; border: 1px solid #00ff9d; padding: 5px 10px; border-radius: 4px; }
        a:hover { background: #00ff9d; color: black; }

        .status-badge { padding: 5px 10px; border-radius: 4px; font-size: 12px; background: #333; color: #ccc; }
        .processing { background: #007bff; color: white; animation: pulse 1s infinite; }
        
        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }

        .admin-panel { margin-top: 50px; border-top: 1px solid #333; padding-top: 20px; }
        .reset-btn { background: #ff0040; color: white; border: none; padding: 10px 20px; cursor: pointer; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>YAEL MEGA DOWNLOADER</h1>
    <div class="container">
        <input type="text" id="link" placeholder="Mega.nz Linkini Yapıştır...">
        <button onclick="send()">ÇEVİR</button>
        <div id="list"></div>
        
        <div class="admin-panel">
            <h3 style="color: #666;">YÖNETİCİ PANELİ</h3>
            <button onclick="resetQueue()" class="reset-btn">⚠️ KUYRUĞU TEMİZLE (RESET)</button>
            <p style="font-size: 12px; color: #444;">*Geçmiş kayıtları silinmez, sadece bekleyen işler silinir.</p>
        </div>
    </div>

    <script>
        function send() {
            var l = document.getElementById('link').value;
            if(!l) return alert("Link boş olamaz!");
            fetch('/add', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({link:l})})
            .then(r=>r.json()).then(d=>{ alert(d.msg); document.getElementById('link').value=''; load(); });
        }
        
        function resetQueue() {
            if(confirm("Tüm kuyruk silinecek ama geçmiş kayıtlar tutulacak. Onaylıyor musun?")) {
                fetch('/reset').then(r=>r.json()).then(d=>{ alert(d.msg); load(); });
            }
        }
        
        function load() {
            fetch('/list').then(r=>r.json()).then(d=>{
                var h = "";
                d.forEach(i=>{
                    let statusClass = i.status === 'ISLENIYOR' ? 'status-badge processing' : 'status-badge';
                    let action = i.gofile ? `<a href="${i.gofile}" target="_blank">İNDİR ⬇</a>` : `<span class="${statusClass}">${i.status}</span>`;
                    
                    h += `<div class="card">
                            <div class="link-info">Link: ${i.link}</div>
                            <div>${action}</div>
                          </div>`;
                });
                document.getElementById('list').innerHTML = h;
            });
        }
        setInterval(load, 4000); // 4 saniyede bir yenile
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
    if not link: return jsonify({"msg": "Hata: Link yok!"})

    current_time = datetime.datetime.now()

    # 1. KUYRUĞA EKLE (İşlenmesi için)
    queue.insert_one({
        "link": link, 
        "status": "SIRADA", 
        "gofile": None, 
        "date": current_time
    })
    
    # 2. GEÇMİŞE EKLE (Kalıcı Kayıt - Log)
    history.insert_one({
        "link": link,
        "date": current_time,
        "ip": request.remote_addr # İstersen IP de kaydedebilirsin
    })
    
    return jsonify({"msg": "Link sıraya alındı!"})

@app.route('/list')
def list_jobs():
    # Sadece kuyruktaki son 10 işi göster
    return jsonify(list(queue.find({}, {'_id':0}).sort("date", -1).limit(10)))

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
    status = "TAMAMLANDI"
    if d['url'] == "HATA_OLUSTU": status = "HATA"
    
    # Kuyruğu güncelle
    queue.update_one({"link": d['link']}, {"$set": {"status": status, "gofile": d['url']}})
    
    # Geçmişi de güncelle (İndirme linkini oraya da ekle ki sonradan bulabilesin)
    history.update_one({"link": d['link']}, {"$set": {"final_url": d['url'], "completed_at": datetime.datetime.now()}})
    
    return jsonify({"status": "ok"})

@app.route('/reset')
def reset():
    # Sadece kuyruğu siler, history (geçmiş) kalır.
    queue.delete_many({}) 
    return jsonify({"msg": "Kuyruk temizlendi! (Geçmiş veritabanında saklı)"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
