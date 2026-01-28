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

# HTML (Reset butonu eklendi)
HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YAEL CLOUD LEECHER</title>
    <style>
        body { background-color: #0a0a0a; color: #eee; font-family: sans-serif; padding: 20px; text-align: center; }
        input { padding: 10px; width: 300px; }
        button { padding: 10px 20px; cursor: pointer; background: #00ff9d; border: none; font-weight: bold; }
        .reset-btn { background: #ff0055; color: white; margin-top: 20px; display: inline-block; text-decoration: none; padding: 10px;}
        .card { border: 1px solid #333; padding: 10px; margin: 10px auto; max-width: 500px; background: #111; }
        a { color: #00ff9d; }
    </style>
</head>
<body>
    <h1>YAEL SYSTEM</h1>
    <input type="text" id="link" placeholder="Mega Linki...">
    <button onclick="send()">ÇEVİR</button>
    <br><br>
    <div id="list"></div>
    <br>
    <a href="#" onclick="resetQueue()" class="reset-btn">⚠️ SİSTEMİ SIFIRLA (RESET)</a>

    <script>
        function send() {
            var l = document.getElementById('link').value;
            fetch('/add', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({link:l})})
            .then(r=>r.json()).then(d=>{ alert(d.msg); load(); });
        }
        function resetQueue() {
            if(confirm("Tüm kuyruk silinecek! Emin misin?")) {
                fetch('/reset').then(r=>r.json()).then(d=>{ alert(d.msg); load(); });
            }
        }
        function load() {
            fetch('/list').then(r=>r.json()).then(d=>{
                var h = "";
                d.forEach(i=>{
                    let action = i.gofile ? `<a href="${i.gofile}" target="_blank">İNDİR</a>` : i.status;
                    h += `<div class="card">${i.link.substring(0,30)}... <br> <b>${action}</b></div>`;
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
    queue.insert_one({"link": link, "status": "SIRADA", "gofile": None, "date": datetime.datetime.now()})
    return jsonify({"msg": "Sıraya alındı."})

@app.route('/list')
def list_jobs():
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
    queue.update_one({"link": d['link']}, {"$set": {"status": "TAMAMLANDI", "gofile": d['url']}})
    return jsonify({"status": "ok"})

# --- RESET ÖZELLİĞİ ---
@app.route('/reset')
def reset():
    queue.delete_many({}) # Her şeyi sil
    return jsonify({"msg": "Sistem temizlendi! Yeniden başlayabilirsin."})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
