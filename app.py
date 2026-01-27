# app.py - Sadece Web Arayüzü ve Veritabanı
import certifi
from flask import Flask, request, jsonify, render_template_string, session
from pymongo import MongoClient
import os
import datetime

app = Flask(__name__)
app.secret_key = "cok_gizli_key"

# MongoDB Bağlantısı (Aşağıda anlatacağım nasıl alacağını)
MONGO_URI = os.environ.get("MONGO_URI") 
# ca = certifi.where() komutu SSL hatasını çözer
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['mega_leech']
queue = db['queue']

# Basit Arayüz HTML'i
HTML = """
<body style="background:#000; color:#0f0; font-family:monospace; padding:20px; text-align:center;">
    <h1>MEGA LEECH SYSTEM (7/24)</h1>
    <input type="text" id="link" placeholder="Mega Linki..." style="width:300px; padding:10px;">
    <button onclick="send()" style="padding:10px; background:#0f0; border:none; cursor:pointer;">ÇEVİR</button>
    <p id="status">Durum: Bekleniyor...</p>
    <div id="list" style="margin-top:20px;"></div>
    <script>
        function send() {
            var l = document.getElementById('link').value;
            fetch('/add', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({link:l})})
            .then(r=>r.json()).then(d=>{alert(d.msg); load();});
        }
        function load() {
            fetch('/list').then(r=>r.json()).then(d=>{
                var h = "";
                d.forEach(i=>{
                    h += "<div style='border:1px solid #333; margin:5px; padding:10px;'>" + 
                         "Link: " + i.link.substring(0,20) + "... | Durum: " + i.status + 
                         (i.gofile ? " | <a href='"+i.gofile+"' style='color:white'>İNDİR</a>" : "") + "</div>";
                });
                document.getElementById('list').innerHTML = h;
            });
        }
        setInterval(load, 5000); // 5 saniyede bir yenile
        load();
    </script>
</body>
"""

@app.route('/')
def home(): return render_template_string(HTML)

@app.route('/add', methods=['POST'])
def add():
    link = request.json.get('link')
    queue.insert_one({"link": link, "status": "SIRADA", "gofile": None, "date": datetime.datetime.now()})
    return jsonify({"msg": "Sıraya alındı!"})

@app.route('/list')
def list_jobs():
    jobs = list(queue.find({}, {'_id':0}).sort("date", -1).limit(10))
    return jsonify(jobs)

# --- İŞÇİ (WORKER) API ---
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
