import certifi
from flask import Flask, request, jsonify, render_template_string, make_response
from pymongo import MongoClient
from functools import wraps
import os
import datetime
import uuid
import random
import string

app = Flask(__name__)

# --- AYARLAR ---
ADMIN_PASSWORD = "Ata_Yasin5353"  # Admin paneli giriş şifresi
MONGO_URI = os.environ.get("MONGO_URI") 
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['mega_leech']
users_col = db['users']       
jobs_col = db['jobs']         
deliveries_col = db['deliveries'] 

def get_tr_time():
    return (datetime.datetime.utcnow() + datetime.timedelta(hours=3)).strftime("%d.%m.%Y %H:%M")

# --- HTML: LANDING PAGE (YABANCILAR İÇİN) ---
HTML_LANDING = """
<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>YAEL CODE /// SYSTEMS</title>
<link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;700&display=swap" rel="stylesheet">
<style>
body{background:#020202;color:white;font-family:'Rajdhani',sans-serif;margin:0;display:flex;flex-direction:column;align-items:center;justify-content:center;height:100vh;text-align:center}
h1{font-size:4rem;margin:0;color:#00f3ff;text-shadow:0 0 20px #00f3ff;letter-spacing:5px}
p{color:#888;font-size:1.2rem;letter-spacing:2px}
.btn{padding:15px 40px;background:transparent;border:2px solid #00f3ff;color:#00f3ff;font-size:1.2rem;font-weight:bold;cursor:pointer;margin-top:30px;transition:0.3s;text-decoration:none;display:inline-block}
.btn:hover{background:#00f3ff;color:black;box-shadow:0 0 30px #00f3ff}
.footer{position:absolute;bottom:20px;color:#444;font-size:0.9rem}
.social{margin-top:20px}
.social a{color:#fff;margin:0 10px;text-decoration:none;font-size:1.1rem}
</style>
</head>
<body>
    <h1>YAEL CODE</h1>
    <p>PROFESSIONAL CLOUD SOLUTIONS</p>
    <div style="margin:40px 0;border-top:1px solid #333;border-bottom:1px solid #333;padding:20px;width:60%">
        Bu sistem özel bir bulut transfer yazılımıdır. <br>
        Erişim sadece lisanslı kullanıcılara açıktır.
    </div>
    <a href="/login" class="btn">MÜŞTERİ GİRİŞİ</a>
    
    <div class="social">
        <p>Lisans Satın Almak İçin:</p>
        <a href="https://t.me/yasin33" target="_blank">✈️ Telegram: @yasin33</a>
        <a href="https://instagram.com/mysthraw" target="_blank">📸 Insta: @mysthraw</a>
    </div>
    <div class="footer">© 2026 YAEL CODE SYSTEMS. Tüm Hakları Saklıdır.</div>
</body></html>
"""

# --- HTML: LOGIN & PANEL (MÜŞTERİ İÇİN) ---
HTML_LOGIN = """
<!DOCTYPE html><html lang="tr"><head><meta charset="UTF-8"><title>GİRİŞ</title>
<style>body{background:#000;color:#0f0;display:flex;justify-content:center;align-items:center;height:100vh;font-family:monospace}
input{padding:10px;background:#111;border:1px solid #0f0;color:#fff;text-align:center} button{padding:10px;background:#0f0;border:none;cursor:pointer}</style>
</head><body><div style="text-align:center"><h2>YAEL SECURE LOGIN</h2>
<input type="password" id="k" placeholder="LİSANS ANAHTARI"><br><br><button onclick="go()">SİSTEME BAĞLAN</button></div>
<script>
function go(){
    // Cihaz Parmak İzi (Basit UUID)
    let hwid = localStorage.getItem('yael_hwid');
    if(!hwid) { hwid = crypto.randomUUID(); localStorage.setItem('yael_hwid', hwid); }
    
    fetch('/api/login', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({key:document.getElementById('k').value, hwid:hwid})})
    .then(r=>r.json()).then(d=>{
        if(d.ok){ localStorage.setItem('user_key', document.getElementById('k').value); window.location.href='/panel'; }
        else alert(d.msg);
    });
}
</script></body></html>
"""

HTML_PANEL = """
<!DOCTYPE html><html lang="tr"><head><meta charset="UTF-8"><title>PANEL</title>
<link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@600&display=swap" rel="stylesheet">
<style>
body{background:#050505;color:white;font-family:'Rajdhani',sans-serif;padding:20px;max-width:800px;margin:0 auto}
.head{display:flex;justify-content:space-between;border-bottom:1px solid #333;padding-bottom:10px;margin-bottom:20px}
.bar{background:#222;height:10px;border-radius:5px;width:200px;overflow:hidden}.fill{height:100%;background:#00f3ff;width:0%}
input{width:70%;padding:15px;background:#111;border:1px solid #444;color:white}
button{padding:15px;background:#00f3ff;border:none;cursor:pointer;font-weight:bold}
.card{background:#111;padding:15px;margin-top:10px;border-left:4px solid #333}
.s-ISLENIYOR{border-color:#00f3ff} .s-TAMAMLANDI{border-color:#00ff9d} .s-HATA{border-color:#ff0055}
</style></head><body>
<div class="head">
    <div><h1>YAEL CLOUD</h1><small id="uid">...</small></div>
    <div style="text-align:right">KOTA: <span id="used">0</span>/<span id="limit">0</span> GB<div class="bar"><div id="fill" class="fill"></div></div></div>
</div>
<div><input id="link" placeholder="MEGA LINK..."><button onclick="add()">BAŞLAT</button></div>
<div id="jobs"></div>
<script>
const key = localStorage.getItem('user_key');
if(!key) window.location.href='/login';
document.getElementById('uid').innerText = key;

function load(){
    fetch('/api/data', {headers:{'X-Key':key}}).then(r=>r.json()).then(d=>{
        if(d.err) { alert(d.msg); window.location.href='/login'; return; }
        document.getElementById('used').innerText = d.used.toFixed(2);
        document.getElementById('limit').innerText = d.limit;
        document.getElementById('fill').style.width = (d.used/d.limit)*100 + '%';
        
        let h = "";
        d.jobs.forEach(j=>{
            let extra = j.status==='ISLENIYOR' ? `<br><small style="color:#00f3ff">${j.log || '...'}</small> <button onclick="stop('${j.id}')" style="padding:5px;background:red;color:white;float:right">DURDUR</button>` : '';
            if(j.status==='TAMAMLANDI') extra = `<br><a href="/teslimat/${j.did}" target="_blank" style="color:#00ff9d">📂 İNDİR</a>`;
            h += `<div class="card s-${j.status}"><b>${j.status}</b> - ${j.date}${extra}<br><small>${j.link}</small></div>`;
        });
        document.getElementById('jobs').innerHTML = h;
    });
}
function add(){
    fetch('/api/add', {method:'POST', headers:{'X-Key':key, 'Content-Type':'application/json'}, body:JSON.stringify({link:document.getElementById('link').value})})
    .then(r=>r.json()).then(d=>{ alert(d.msg); load(); });
}
function stop(jid){
    if(confirm("Durdurulsun mu?")) fetch('/api/stop_job', {method:'POST', headers:{'X-Key':key, 'Content-Type':'application/json'}, body:JSON.stringify({jid:jid})}).then(()=>load());
}
setInterval(load, 2000); load();
</script></body></html>
"""

# --- HTML: ADMIN PANELİ ---
HTML_ADMIN = """
<!DOCTYPE html><html><head><title>YAEL ADMIN</title>
<style>body{background:#222;color:#fff;font-family:sans-serif;padding:20px} table{width:100%;border-collapse:collapse} th,td{border:1px solid #444;padding:8px;text-align:left} button{cursor:pointer}</style>
</head><body>
<h1>👑 YAEL ADMIN PANEL</h1>
<div style="background:#333;padding:10px;margin-bottom:20px">
    <h3>YENİ LİSANS OLUŞTUR</h3>
    Limit (GB): <input id="limit" type="number" value="10">
    <button onclick="create()">OLUŞTUR</button>
</div>
<h3>KULLANICILAR</h3>
<table id="users"></table>
<script>
const pwd = prompt("Admin Şifresi:");
function load(){
    fetch('/api/admin/users?pwd='+pwd).then(r=>r.json()).then(d=>{
        if(d.err) return alert("Yanlış Şifre");
        let h = "<tr><th>Key</th><th>Limit</th><th>Kullanılan</th><th>Cihaz ID</th><th>Durum</th><th>İşlem</th></tr>";
        d.users.forEach(u=>{
            let status = u.banned ? '<span style="color:red">BANLI</span>' : '<span style="color:#0f0">AKTİF</span>';
            let btn = u.banned ? `<button onclick="toggle('${u.key}', false)">AÇ</button>` : `<button onclick="toggle('${u.key}', true)">BANLA</button>`;
            h += `<tr><td>${u.key}</td><td>${u.limit_gb}</td><td>${u.used_gb.toFixed(2)}</td><td>${u.hwid || '-'}</td><td>${status}</td><td>${btn}</td></tr>`;
        });
        document.getElementById('users').innerHTML = h;
    });
}
function create(){
    let l = document.getElementById('limit').value;
    fetch('/api/admin/create?pwd='+pwd+'&limit='+l).then(r=>r.json()).then(d=>{ prompt("Kopyala:", d.key); load(); });
}
function toggle(k, state){
    fetch('/api/admin/ban', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({pwd:pwd, key:k, ban:state})}).then(()=>load());
}
load();
</script></body></html>
"""

# --- ROUTES ---
@app.route('/')
def index(): return render_template_string(HTML_LANDING)

@app.route('/login')
def login_page(): return render_template_string(HTML_LOGIN)

@app.route('/panel')
def panel_page(): return render_template_string(HTML_PANEL)

@app.route('/admin')
def admin_page(): return render_template_string(HTML_ADMIN)

@app.route('/teslimat/<id>')
def delivery(id):
    d = deliveries_col.find_one({"id": id})
    if d: return render_template_string(d['html'])
    return "Bulunamadı", 404

# --- API ---
@app.route('/api/login', methods=['POST'])
def api_login():
    d = request.json
    k = d.get('key')
    hwid = d.get('hwid') # Tarayıcıdan gelen cihaz kimliği
    
    user = users_col.find_one({"key": k})
    if not user: return jsonify({"ok": False, "msg": "Geçersiz Anahtar"})
    if user.get('banned'): return jsonify({"ok": False, "msg": "BU HESAP YÖNETİCİ TARAFINDAN ENGELLENDİ!"})
    
    # CİHAZ KİLİDİ KONTROLÜ
    if user.get('hwid'):
        if user['hwid'] != hwid:
            return jsonify({"ok": False, "msg": "⚠️ GÜVENLİK UYARISI: Bu anahtar başka bir cihazda kullanılıyor! Erişim reddedildi."})
    else:
        # İlk giriş: Cihazı kilitle
        users_col.update_one({"key": k}, {"$set": {"hwid": hwid}})
        
    return jsonify({"ok": True})

@app.route('/api/data')
def api_data():
    k = request.headers.get('X-Key')
    user = users_col.find_one({"key": k})
    if not user or user.get('banned'): return jsonify({"err": True, "msg": "Oturum Kapalı"})
    
    jobs = list(jobs_col.find({"user_key": k}, {'_id':0}).sort("_id", -1).limit(10))
    return jsonify({
        "limit": user['limit_gb'],
        "used": user['used_gb'],
        "jobs": [{"id": j['job_id'], "status": j['status'], "link": j['link'], "date": j['date'], "log": j.get('progress_log'), "did": j.get('delivery_id')} for j in jobs]
    })

@app.route('/api/add', methods=['POST'])
def api_add():
    k = request.headers.get('X-Key')
    link = request.json.get('link')
    user = users_col.find_one({"key": k})
    if not user: return jsonify({"msg": "Hata"})
    if user['used_gb'] >= user['limit_gb']: return jsonify({"msg": "Kota Dolu!"})
    
    job_id = str(uuid.uuid4())[:8]
    jobs_col.insert_one({"job_id": job_id, "user_key": k, "link": link, "status": "SIRADA", "date": get_tr_time(), "stop_requested": False})
    return jsonify({"msg": "Başlatıldı"})

@app.route('/api/stop_job', methods=['POST'])
def api_stop():
    k = request.headers.get('X-Key')
    jid = request.json.get('jid')
    # Sadece kendi işini durdurabilir
    job = jobs_col.find_one({"job_id": jid, "user_key": k})
    if job:
        # Worker'a dur emri vermek için flag koyuyoruz
        jobs_col.update_one({"job_id": jid}, {"$set": {"status": "DURDURULUYOR...", "stop_requested": True}})
    return jsonify({"msg": "ok"})

# --- WORKER API ---
@app.route('/api/worker/get')
def worker_get():
    job = jobs_col.find_one({"status": "SIRADA"})
    if job:
        jobs_col.update_one({"job_id": job['job_id']}, {"$set": {"status": "ISLENIYOR"}})
        return jsonify({"found": True, "job": job['job_id'], "link": job['link']})
    return jsonify({"found": False})

@app.route('/api/worker/update', methods=['POST'])
def worker_update():
    d = request.json
    jid = d['id']
    msg = d['msg']
    
    # Durdurma emri var mı kontrol et
    job = jobs_col.find_one({"job_id": jid})
    if job and job.get('stop_requested'):
        return jsonify({"stop": True}) # Worker'a "Öl" emri
        
    jobs_col.update_one({"job_id": jid}, {"$set": {"progress_log": msg}})
    return jsonify({"stop": False})

@app.route('/api/worker/done', methods=['POST'])
def worker_done():
    d = request.json
    jid = d['id']
    job = jobs_col.find_one({"job_id": jid})
    
    if d.get('error'):
        jobs_col.update_one({"job_id": jid}, {"$set": {"status": d['error']}})
    else:
        did = str(uuid.uuid4())[:8]
        deliveries_col.insert_one({"id": did, "html": d['html']})
        jobs_col.update_one({"job_id": jid}, {"$set": {"status": "TAMAMLANDI", "delivery_id": did}})
        users_col.update_one({"key": job['user_key']}, {"$inc": {"used_gb": d['size']}})
        
    return jsonify({"ok": True})

# --- ADMIN API ---
@app.route('/api/admin/users')
def admin_users():
    if request.args.get('pwd') != ADMIN_PASSWORD: return jsonify({"err": True})
    return jsonify({"users": list(users_col.find({}, {'_id':0}))})

@app.route('/api/admin/create')
def admin_create():
    if request.args.get('pwd') != ADMIN_PASSWORD: return jsonify({"err": True})
    key = "YAEL-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    users_col.insert_one({"key": key, "limit_gb": int(request.args.get('limit')), "used_gb": 0, "hwid": None, "banned": False})
    return jsonify({"key": key})

@app.route('/api/admin/ban', methods=['POST'])
def admin_ban():
    d = request.json
    if d.get('pwd') != ADMIN_PASSWORD: return jsonify({"err": True})
    users_col.update_one({"key": d['key']}, {"$set": {"banned": d['ban']}})
    return jsonify({"ok": True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
