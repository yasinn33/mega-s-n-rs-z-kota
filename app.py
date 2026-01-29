import certifi
from flask import Flask, request, jsonify, render_template_string
from pymongo import MongoClient
import os
import datetime
import uuid
import random
import string

app = Flask(__name__)

# --- AYARLAR ---
ADMIN_PASSWORD = "Ata_Yasin5353"
MONGO_URI = os.environ.get("MONGO_URI") 
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['mega_leech']
users_col = db['users']       
jobs_col = db['jobs']         
deliveries_col = db['deliveries'] 

def get_tr_time():
    return (datetime.datetime.utcnow() + datetime.timedelta(hours=3)).strftime("%d.%m.%Y %H:%M")

# --- CSS STYLES (ORTAK TASARIM DİLİ) ---
SHARED_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;700&family=Share+Tech+Mono&display=swap');
    
    :root { --main: #00f3ff; --sec: #00ff9d; --bg: #050505; --glass: rgba(10, 10, 10, 0.8); }
    
    body {
        background-color: var(--bg);
        background-image: 
            linear-gradient(rgba(0, 243, 255, 0.05) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 243, 255, 0.05) 1px, transparent 1px);
        background-size: 40px 40px;
        color: white;
        font-family: 'Rajdhani', sans-serif;
        margin: 0;
        min-height: 100vh;
        overflow-x: hidden;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }
    
    /* Hareketli Arka Plan Işığı */
    body::before {
        content: ''; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background: radial-gradient(circle at 50% 50%, rgba(0, 243, 255, 0.05), transparent 70%);
        pointer-events: none;
        animation: pulseBg 10s infinite alternate;
    }

    .container {
        background: var(--glass);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(0, 243, 255, 0.3);
        box-shadow: 0 0 30px rgba(0, 243, 255, 0.1);
        padding: 40px;
        border-radius: 15px;
        text-align: center;
        width: 90%;
        max-width: 500px;
        position: relative;
        overflow: hidden;
    }
    
    /* Neon Çizgi Animasyonu */
    .container::after {
        content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 2px;
        background: linear-gradient(90deg, transparent, var(--main), transparent);
        animation: scan 3s infinite linear;
    }

    h1 { font-size: 2.5rem; margin: 0; color: var(--main); text-shadow: 0 0 20px var(--main); letter-spacing: 5px; text-transform: uppercase; }
    p { color: #aaa; font-family: 'Share Tech Mono', monospace; font-size: 0.9rem; letter-spacing: 2px; margin-bottom: 30px; }

    input {
        width: 100%; box-sizing: border-box; padding: 15px; margin: 15px 0;
        background: rgba(0,0,0,0.5); border: 1px solid #333; color: var(--main);
        font-family: 'Share Tech Mono', monospace; font-size: 1.1rem; text-align: center;
        border-radius: 5px; transition: 0.3s;
    }
    input:focus { outline: none; border-color: var(--main); box-shadow: 0 0 15px rgba(0, 243, 255, 0.2); }

    .btn {
        display: inline-block; padding: 15px 40px; background: transparent;
        border: 2px solid var(--main); color: var(--main); font-size: 1.1rem;
        font-weight: bold; text-decoration: none; cursor: pointer;
        text-transform: uppercase; letter-spacing: 2px;
        transition: 0.3s; position: relative; overflow: hidden;
        margin-top: 10px; width: 100%; box-sizing: border-box;
    }
    .btn:hover { background: var(--main); color: black; box-shadow: 0 0 30px var(--main); }
    
    .btn-green { border-color: var(--sec); color: var(--sec); }
    .btn-green:hover { background: var(--sec); color: black; box-shadow: 0 0 30px var(--sec); }

    @keyframes scan { 0% { transform: translateX(-100%); } 100% { transform: translateX(100%); } }
    @keyframes pulseBg { 0% { opacity: 0.5; } 100% { opacity: 1; } }
    
    /* Scrollbar */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: #000; }
    ::-webkit-scrollbar-thumb { background: #333; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--main); }
</style>
"""

# --- HTML: LANDING PAGE ---
HTML_LANDING = f"""
<!DOCTYPE html><html lang="tr"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>YAEL SYSTEMS</title>
{SHARED_CSS}
</head><body>
    <div class="container">
        <h1 style="font-size: 3.5rem;">YAEL CODE</h1>
        <p>/// SECURE CLOUD TRANSFER SYSTEMS ///</p>
        
        <div style="margin: 30px 0; border: 1px solid #333; padding: 20px; background: rgba(0,0,0,0.3);">
            <div style="font-family: 'Share Tech Mono'; color: #fff;">SİSTEM DURUMU: <span style="color:var(--sec)">ÇEVRİMİÇİ</span></div>
            <div style="font-family: 'Share Tech Mono'; color: #fff; margin-top:5px;">GÜVENLİK: <span style="color:var(--sec)">AKTİF</span></div>
        </div>

        <a href="/login" class="btn">MÜŞTERİ PANELİNE GİRİŞ</a>
        
        <div style="margin-top: 30px; font-size: 0.8rem; color: #666;">
            &copy; 2026 YAEL CODE INC.<br>
            <a href="https://t.me/yasin33" target="_blank" style="color: #888; text-decoration: none;">Telegram: @yasin33</a>
        </div>
    </div>
</body></html>
"""

# --- HTML: LOGIN ---
HTML_LOGIN = f"""
<!DOCTYPE html><html lang="tr"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>GİRİŞ</title>
{SHARED_CSS}
</head><body>
    <div class="container">
        <h1>GİRİŞ KAPISI</h1>
        <p>LÜTFEN LİSANS ANAHTARINIZI GİRİN</p>
        <input type="password" id="k" placeholder="XXXX-XXXX-XXXX">
        <button onclick="go()" class="btn">SİSTEME BAĞLAN</button>
        <div id="msg" style="margin-top:15px; color:red; font-family:'Share Tech Mono'"></div>
    </div>
<script>
function go(){
    let btn = document.querySelector('button');
    btn.innerText = "BAĞLANIYOR...";
    let hwid = localStorage.getItem('hwid') || crypto.randomUUID(); localStorage.setItem('hwid',hwid);
    fetch('/api/login', {{method:'POST', headers:{{'Content-Type':'application/json'}}, body:JSON.stringify({{key:document.getElementById('k').value, hwid:hwid}})}})
    .then(r=>r.json()).then(d=>{{
        if(d.ok){{ localStorage.setItem('ukey', document.getElementById('k').value); window.location.href='/panel'; }}
        else {{ document.getElementById('msg').innerText = "ERİŞİM REDDEDİLDİ: " + d.msg; btn.innerText = "SİSTEME BAĞLAN"; }}
    }});
}
</script></body></html>
"""

# --- HTML: PANEL (ASIL ŞOV BURADA) ---
HTML_PANEL = f"""
<!DOCTYPE html><html lang="tr"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>KONTROL PANELİ</title>
{SHARED_CSS}
<style>
    body {{ justify-content: flex-start; padding-top: 40px; }}
    .panel-container {{ width: 95%; max-width: 900px; background: rgba(0,0,0,0.6); border: 1px solid #333; }}
    
    .hud-header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 20px; }}
    .hud-box {{ text-align: right; font-family: 'Share Tech Mono'; }}
    
    .progress-track {{ width: 200px; height: 10px; background: #222; border: 1px solid #444; margin-top: 5px; }}
    .progress-fill {{ height: 100%; background: var(--main); width: 0%; box-shadow: 0 0 10px var(--main); transition: width 0.5s; }}
    
    .input-group {{ display: flex; gap: 10px; margin-bottom: 30px; }}
    .input-group input {{ margin: 0; text-align: left; }}
    .input-group button {{ margin: 0; width: auto; white-space: nowrap; }}
    
    .job-card {{ 
        background: rgba(20, 20, 20, 0.8); border: 1px solid #333; padding: 15px; margin-bottom: 15px; 
        border-left: 5px solid #555; display: flex; flex-direction: column; gap: 10px;
        transition: 0.3s;
    }}
    .job-card:hover {{ border-color: #555; transform: translateX(5px); }}
    
    .status-badge {{ font-family: 'Share Tech Mono'; font-size: 0.8rem; padding: 5px 10px; background: #222; display: inline-block; width: fit-content; }}
    
    .s-ISLENIYOR {{ border-left-color: var(--main); }}
    .s-ISLENIYOR .status-badge {{ color: var(--main); border: 1px solid var(--main); }}
    
    .s-TAMAMLANDI {{ border-left-color: var(--sec); }}
    .s-TAMAMLANDI .status-badge {{ color: var(--sec); border: 1px solid var(--sec); }}
    
    .s-HATA {{ border-left-color: #ff0055; }}
    .s-HATA .status-badge {{ color: #ff0055; border: 1px solid #ff0055; }}

    .log-text {{ color: #aaa; font-size: 0.9rem; font-family: 'Share Tech Mono'; }}
    .glow-text {{ animation: glow 2s infinite alternate; }}
    @keyframes glow {{ from {{ text-shadow: 0 0 5px var(--main); }} to {{ text-shadow: 0 0 15px var(--main); }} }}
</style>
</head><body>
    <div class="container panel-container">
        <div class="hud-header">
            <div>
                <h2 style="margin:0; color:white; letter-spacing:3px;">KOMUTA MERKEZİ</h2>
                <small style="color:#666; font-family:'Share Tech Mono'">ID: <span id="uid" style="color:var(--main)">...</span></small>
            </div>
            <div class="hud-box">
                <div>KOTA DURUMU: <span id="used" style="color:white">0</span> / <span id="limit">0</span> GB</div>
                <div class="progress-track"><div id="fill" class="progress-fill"></div></div>
            </div>
        </div>

        <div class="input-group">
            <input id="link" placeholder="MEGA.NZ KLASÖR LİNKİNİ BURAYA YAPIŞTIR...">
            <button onclick="add()" class="btn">🚀 BAŞLAT</button>
        </div>

        <div style="text-align:left; margin-bottom:10px; font-family:'Share Tech Mono'; color:#666;">/// AKTİF GÖREVLER ///</div>
        <div id="jobs"></div>
        
        <button onclick="logout()" style="margin-top:30px; background:none; border:none; color:#444; cursor:pointer;">OTURUMU KAPAT</button>
    </div>

<script>
const k = localStorage.getItem('ukey'); if(!k) location.href='/login';
document.getElementById('uid').innerText = k.substring(0,8) + '****';

function load(){
    fetch('/api/data', {{headers:{{'X-Key':k}}}}).then(r=>r.json()).then(d=>{{
        if(d.err) return location.href='/login';
        
        // Kota Animasyonu
        document.getElementById('used').innerText = d.used.toFixed(2);
        document.getElementById('limit').innerText = d.limit;
        let pct = (d.used/d.limit)*100;
        document.getElementById('fill').style.width = pct + '%';
        if(pct > 90) document.getElementById('fill').style.backgroundColor = '#ff0055';

        let h = "";
        d.jobs.forEach(j=>{{
            let statusHTML = j.status;
            let extra = "";
            let logHTML = "";
            
            if(j.status === 'ISLENIYOR') {{
                statusHTML = "⚙️ SİSTEM İŞLİYOR...";
                logHTML = `<div class="log-text glow-text">> ${{j.log || 'Veri akışı bekleniyor...'}}</div>`;
                extra = `<button onclick="stop('${{j.id}}')" style="background:#ff0055; color:white; border:none; padding:5px 10px; cursor:pointer; font-weight:bold; font-size:0.7rem; float:right;">İPTAL ET</button>`;
            }} else if (j.status === 'TAMAMLANDI') {{
                statusHTML = "✅ GÖREV BAŞARILI";
                extra = `<a href="/teslimat/${{j.did}}" target="_blank" class="btn btn-green" style="padding:10px; margin:0; width:auto; font-size:0.9rem;">📂 DOSYALARI İNDİR</a>`;
            }} else if (j.status === 'SIRADA') {{
                statusHTML = "⏳ KUYRUKTA BEKLİYOR";
            }}

            h += `
            <div class="job-card s-${{j.status}}">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span class="status-badge">${{statusHTML}}</span>
                    <small style="color:#666">${{j.date}}</small>
                </div>
                <div style="font-size:0.9rem; color:white; overflow:hidden; white-space:nowrap; text-overflow:ellipsis;">${{j.link}}</div>
                ${{logHTML}}
                <div style="text-align:right;">${{extra}}</div>
            </div>`;
        }});
        document.getElementById('jobs').innerHTML = h || '<div style="color:#444; padding:20px;">HENÜZ BİR İŞLEM YOK...</div>';
    }});
}

function add(){{
    let l = document.getElementById('link').value;
    if(!l) return alert("LİNK GİRMEDİNİZ!");
    let btn = document.querySelector('.input-group button');
    btn.innerText = "GÖNDERİLİYOR...";
    
    fetch('/api/add', {{method:'POST', headers:{{'X-Key':k, 'Content-Type':'application/json'}}, body:JSON.stringify({{link:l}})}})
    .then(r=>r.json()).then(d=>{{ 
        alert(d.msg); 
        document.getElementById('link').value=''; 
        btn.innerText = "🚀 BAŞLAT";
        load(); 
    }});
}}

function stop(jid){{ if(confirm("İşlemi iptal etmek istediğine emin misin?")) fetch('/api/stop_job', {{method:'POST', headers:{{'X-Key':k, 'Content-Type':'application/json'}}, body:JSON.stringify({{jid:jid}})}}).then(()=>load()) }}
function logout(){{ localStorage.removeItem('ukey'); location.href='/login'; }}

setInterval(load, 3000); 
load();
</script></body></html>
"""

# --- HTML: ADMIN (BASİT TUTTUM, SADECE İŞLEVSEL OLSUN) ---
HTML_ADMIN = f"""
<!DOCTYPE html><html><head><title>ADMIN CORE</title>{SHARED_CSS}<style>table{{width:100%; border-collapse:collapse; margin-top:20px;}} th,td{{border:1px solid #333; padding:10px; text-align:left; color:#ccc;}} th{{color:var(--main);}}</style></head>
<body>
<div class="container" style="max-width:800px;">
    <h1>YÖNETİCİ MODU</h1>
    <div style="display:flex; gap:10px; margin-bottom:20px;">
        <input id="l" type="number" value="10" placeholder="GB LİMİTİ">
        <button onclick="c()" class="btn">YENİ KEY OLUŞTUR</button>
    </div>
    <div id="res" style="color:var(--sec); font-family:'Share Tech Mono'; margin-bottom:20px;"></div>
    
    <h3>KULLANICI VERİTABANI</h3>
    <table id="tbl"></table>
</div>
<script>
const p=prompt("ERİŞİM ŞİFRESİ:");
function load(){{
    fetch('/api/admin/users?pwd='+p).then(r=>r.json()).then(d=>{{
        if(d.err) return document.body.innerHTML="<h1>YETKİSİZ ERİŞİM</h1>";
        let h="<tr><th>KEY</th><th>LİMİT</th><th>KULLANILAN</th><th>DURUM</th><th>İŞLEM</th></tr>";
        d.users.forEach(u=>{{
            let btn = u.banned ? `<button onclick="ban('${{u.key}}',false)" style="color:#0f0">AÇ</button>` : `<button onclick="ban('${{u.key}}',true)" style="color:red">BANLA</button>`;
            h+=`<tr><td>${{u.key}}</td><td>${{u.limit_gb}}</td><td>${{u.used_gb.toFixed(2)}}</td><td>${{u.banned?'BANLI':'AKTİF'}}</td><td>${{btn}}</td></tr>`;
        }});
        document.getElementById('tbl').innerHTML=h;
    }});
}}
function c(){{fetch('/api/admin/create?pwd='+p+'&limit='+document.getElementById('l').value).then(r=>r.json()).then(d=>{{document.getElementById('res').innerText="YENİ KEY: "+d.key; load();}})}}
function ban(k,s){{fetch('/api/admin/ban',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{pwd:p,key:k,ban:s}})}}).then(()=>load())}}
load();
</script></body></html>
"""

# --- FLASK ROUTES (MANTIK DEĞİŞMEDİ, SADECE HTML'LER GÜNCELLENDİ) ---
@app.route('/')
def r1(): return render_template_string(HTML_LANDING)
@app.route('/login')
def r2(): return render_template_string(HTML_LOGIN)
@app.route('/panel')
def r3(): return render_template_string(HTML_PANEL)
@app.route('/admin')
def r4(): return render_template_string(HTML_ADMIN)
@app.route('/teslimat/<id>')
def r5(id):
    d = deliveries_col.find_one({"id": id})
    # Teslimat sayfasını da CSS'e uyduralım
    if d:
        clean_html = d['html'].replace("background:#050505;", "").replace("</body>", "</body>") # Eski stili temizle
        return render_template_string(SHARED_CSS + clean_html) 
    return "Bulunamadı"

# --- API (AYNI KODLAR) ---
@app.route('/api/login', methods=['POST'])
def api_login():
    d=request.json; u=users_col.find_one({"key":d['key']})
    if not u or u.get('banned'): return jsonify({"ok":False,"msg":"GEÇERSİZ VEYA BANLI ANAHTAR"})
    if u.get('hwid') and u['hwid']!=d['hwid']: return jsonify({"ok":False,"msg":"BU ANAHTAR BAŞKA CİHAZA KİLİTLİ!"})
    if not u.get('hwid'): users_col.update_one({"key":d['key']},{"$set":{"hwid":d['hwid']}})
    return jsonify({"ok":True})

@app.route('/api/data')
def api_data():
    k=request.headers.get('X-Key'); u=users_col.find_one({"key":k})
    if not u: return jsonify({"err":True})
    jobs=list(jobs_col.find({"user_key":k},{'_id':0}).sort("_id",-1).limit(10))
    return jsonify({"used":u['used_gb'],"limit":u['limit_gb'],"jobs":[{"id":j['job_id'],"status":j['status'],"link":j['link'],"log":j.get('progress_log'),"did":j.get('delivery_id'),"date":j.get('date','-')} for j in jobs]})

@app.route('/api/add', methods=['POST'])
def api_add():
    k=request.headers.get('X-Key'); l=request.json.get('link'); u=users_col.find_one({"key":k})
    if not u: return jsonify({"msg":"Oturum hatası"})
    if u['used_gb']>=u['limit_gb']: return jsonify({"msg":"⚠️ KOTA LİMİTİNE ULAŞILDI!"})
    jid=str(uuid.uuid4())[:8]
    jobs_col.insert_one({"job_id":jid,"user_key":k,"link":l,"status":"SIRADA","date":get_tr_time(),"stop_requested":False})
    return jsonify({"msg":"✅ İŞLEM KUYRUĞA ALINDI"})

@app.route('/api/stop_job', methods=['POST'])
def api_stop():
    jobs_col.update_one({"job_id":request.json.get('jid')},{"$set":{"status":"DURDURULUYOR...","stop_requested":True}})
    return jsonify({"ok":True})

# WORKER & ADMIN API'LERI (AYNI)
@app.route('/api/worker/get')
def w_get():
    j=jobs_col.find_one({"status":"SIRADA"})
    if j: 
        jobs_col.update_one({"job_id":j['job_id']},{"$set":{"status":"ISLENIYOR"}})
        return jsonify({"found":True,"job":j['job_id'],"link":j['link']})
    return jsonify({"found":False})

@app.route('/api/worker/update', methods=['POST'])
def w_upd():
    d=request.json; j=jobs_col.find_one({"job_id":d['id']})
    if j and j.get('stop_requested'): return jsonify({"stop":True})
    jobs_col.update_one({"job_id":d['id']},{"$set":{"progress_log":d['msg']}})
    return jsonify({"stop":False})

@app.route('/api/worker/done', methods=['POST'])
def w_done():
    d=request.json; jid=d['id']; j=jobs_col.find_one({"job_id":jid})
    if d.get('error'): jobs_col.update_one({"job_id":jid},{"$set":{"status":d['error']}})
    else:
        did=str(uuid.uuid4())[:8]
        deliveries_col.insert_one({"id":did,"html":d['html']})
        jobs_col.update_one({"job_id":jid},{"$set":{"status":"TAMAMLANDI","delivery_id":did}})
        users_col.update_one({"key":j['user_key']},{"$inc":{"used_gb":d['size']}})
    return jsonify({"ok":True})

@app.route('/api/admin/users')
def adm_users():
    if request.args.get('pwd')!=ADMIN_PASSWORD: return jsonify({"err":True})
    return jsonify({"users":list(users_col.find({},{'_id':0}))})

@app.route('/api/admin/create')
def adm_create():
    if request.args.get('pwd')!=ADMIN_PASSWORD: return jsonify({"err":True})
    k="YAEL-"+''.join(random.choices(string.ascii_uppercase+string.digits,k=8))
    users_col.insert_one({"key":k,"limit_gb":int(request.args.get('limit')),"used_gb":0,"hwid":None,"banned":False})
    return jsonify({"key":k})

@app.route('/api/admin/ban', methods=['POST'])
def adm_ban():
    d=request.json
    if d.get('pwd')!=ADMIN_PASSWORD: return jsonify({"err":True})
    users_col.update_one({"key":d['key']},{"$set":{"banned":d['ban']}})
    return jsonify({"ok":True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
