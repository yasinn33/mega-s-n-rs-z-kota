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

# --- CSS (CYBERPUNK V2) ---
SHARED_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;700&family=Share+Tech+Mono&display=swap');
    :root { --main: #00f3ff; --sec: #00ff9d; --danger: #ff0055; --bg: #050505; --glass: rgba(10, 10, 10, 0.9); }
    body {
        background-color: var(--bg);
        background-image: linear-gradient(rgba(0, 243, 255, 0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0, 243, 255, 0.03) 1px, transparent 1px);
        background-size: 30px 30px; color: white; font-family: 'Rajdhani', sans-serif;
        margin: 0; min-height: 100vh; display: flex; flex-direction: column; align-items: center;
    }
    .container {
        background: var(--glass); border: 1px solid #333; box-shadow: 0 0 50px rgba(0,0,0,0.8);
        padding: 30px; border-radius: 10px; text-align: center; width: 90%; max-width: 800px; margin-top: 30px;
    }
    h1 { color: var(--main); text-shadow: 0 0 15px var(--main); letter-spacing: 4px; margin: 0; }
    h2 { margin: 0; color: white; }
    input { width: 100%; padding: 15px; background: #000; border: 1px solid #333; color: var(--main); font-family: 'Share Tech Mono'; text-align: center; margin: 15px 0; box-sizing: border-box; }
    .btn { padding: 12px 30px; background: transparent; border: 2px solid var(--main); color: var(--main); font-weight: bold; cursor: pointer; transition: 0.3s; width: 100%; }
    .btn:hover { background: var(--main); color: black; box-shadow: 0 0 20px var(--main); }
    .btn-danger { border-color: var(--danger); color: var(--danger); }
    .btn-danger:hover { background: var(--danger); color: white; box-shadow: 0 0 20px var(--danger); }
    
    .job-card { background: #111; border-left: 4px solid #333; padding: 15px; margin-bottom: 10px; text-align: left; position: relative; }
    .s-ISLENIYOR { border-color: var(--main); }
    .s-TAMAMLANDI { border-color: var(--sec); }
    .s-HATA { border-color: var(--danger); }
    
    .terminal { background: #000; color: #aaa; padding: 10px; font-family: 'Share Tech Mono'; font-size: 0.8rem; margin-top: 10px; border: 1px solid #333; height: 40px; overflow: hidden; white-space: nowrap; }
    .blink { animation: blink 1s infinite; }
    @keyframes blink { 50% { opacity: 0; } }
    
    /* Admin Tablo */
    table { width: 100%; border-collapse: collapse; margin-top: 20px; }
    th, td { border: 1px solid #333; padding: 10px; text-align: left; font-size: 0.9rem; }
    th { color: var(--main); }
</style>
"""

HTML_LOGIN = f"""<!DOCTYPE html><html><head><title>GİRİŞ</title>{SHARED_CSS}</head><body>
<div class="container" style="max-width:400px; margin-top:100px;">
    <h1>GİRİŞ</h1>
    <input type="password" id="k" placeholder="LİSANS ANAHTARI">
    <button onclick="go()" class="btn">SİSTEME GİR</button>
</div>
<script>
function go(){{
    let k = document.getElementById('k').value;
    let hwid = localStorage.getItem('hwid') || crypto.randomUUID(); localStorage.setItem('hwid',hwid);
    fetch('/api/login', {{method:'POST', headers:{{'Content-Type':'application/json'}}, body:JSON.stringify({{key:k, hwid:hwid}})}})
    .then(r=>r.json()).then(d=>{{ if(d.ok){{localStorage.setItem('ukey',k); location.href='/panel'}} else alert(d.msg) }});
}}
</script></body></html>"""

HTML_PANEL = f"""<!DOCTYPE html><html><head><title>PANEL</title>{SHARED_CSS}</head><body>
<div class="container">
    <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #333; padding-bottom:15px; margin-bottom:20px;">
        <div><h2>PANEL V46</h2><small style="color:#666">ID: <span id="uid">...</span></small></div>
        <div style="text-align:right">KOTA: <span id="used" style="color:var(--main)">0</span> / <span id="limit">0</span> GB</div>
    </div>

    <input id="link" placeholder="MEGA LİNKİNİ YAPIŞTIR...">
    <button onclick="add()" class="btn">🚀 İNDİRMEYİ BAŞLAT</button>
    
    <div style="display:flex; justify-content:space-between; align-items:center; margin-top:30px; border-bottom:1px solid #333; padding-bottom:10px;">
        <span style="color:#666">GEÇMİŞ İŞLEMLER</span>
        <button onclick="clearHistory()" style="background:none; border:none; color:var(--danger); cursor:pointer; font-weight:bold;">🗑️ TEMİZLE</button>
    </div>
    <div id="jobs"></div>
    <button onclick="logout()" style="margin-top:20px; background:none; border:none; color:#444; cursor:pointer">ÇIKIŞ YAP</button>
</div>
<script>
const k=localStorage.getItem('ukey'); if(!k) location.href='/login';
document.getElementById('uid').innerText = k.substring(0,6)+'...';

function load(){{
    fetch('/api/data', {{headers:{{'X-Key':k}}}}).then(r=>r.json()).then(d=>{{
        if(d.err) return location.href='/login';
        document.getElementById('used').innerText = d.used.toFixed(2);
        document.getElementById('limit').innerText = d.limit;
        
        let h="";
        d.jobs.forEach(j=>{{
            let status = j.status;
            let actions = "";
            let term = "";
            
            if(j.status === 'ISLENIYOR') {{
                status = `<span style="color:var(--main)">⚙️ İŞLENİYOR</span>`;
                term = `<div class="terminal"><span style="color:var(--sec)">></span> ${{j.log || 'Hazırlanıyor...'}}<span class="blink">_</span></div>`;
                actions = `<button onclick="stop('${{j.id}}')" style="float:right; background:var(--danger); color:white; border:none; padding:5px 10px; cursor:pointer;">DURDUR</button>`;
            }} else if(j.status === 'TAMAMLANDI') {{
                status = `<span style="color:var(--sec)">✅ TAMAMLANDI</span>`;
                actions = `<a href="/teslimat/${{j.did}}" target="_blank" style="float:right; color:var(--sec); text-decoration:none; border:1px solid var(--sec); padding:5px 10px;">İNDİR</a>`;
            }} else {{
                status = `<span style="color:var(--danger)">⚠️ ${{j.status}}</span>`;
            }}

            h += `<div class="job-card s-${{j.status}}">
                <div style="overflow:hidden; white-space:nowrap; text-overflow:ellipsis; font-weight:bold; color:white; margin-bottom:5px;">${{j.link}}</div>
                <div style="font-size:0.8rem; color:#666; display:flex; justify-content:space-between; align-items:center;">
                    <span>${{status}} <span style="margin-left:10px">${{j.date}}</span></span>
                    ${{actions}}
                </div>
                ${{term}}
            </div>`;
        }});
        document.getElementById('jobs').innerHTML = h || '<div style="padding:20px; color:#444">LİSTE BOŞ</div>';
    }});
}}

function add(){{
    let l = document.getElementById('link').value;
    if(!l) return alert("Link boş!");
    fetch('/api/add', {{method:'POST', headers:{{'X-Key':k, 'Content-Type':'application/json'}}, body:JSON.stringify({{link:l}})}})
    .then(r=>r.json()).then(d=>{{ alert(d.msg); load(); document.getElementById('link').value=''; }});
}}
function stop(jid){{ if(confirm("Durdurmak istiyor musun?")) fetch('/api/stop_job', {{method:'POST', headers:{{'X-Key':k, 'Content-Type':'application/json'}}, body:JSON.stringify({{jid:jid}})}}).then(()=>load()); }}
function clearHistory(){{ if(confirm("Tüm geçmiş silinecek?")) fetch('/api/clear_history', {{headers:{{'X-Key':k}}}}).then(()=>load()); }}
function logout(){{ localStorage.removeItem('ukey'); location.href='/login'; }}
setInterval(load, 2000); load();
</script></body></html>"""

HTML_ADMIN = f"""<!DOCTYPE html><html><head><title>ADMIN</title>{SHARED_CSS}</head><body>
<div class="container" style="max-width:900px">
    <h1>YÖNETİCİ PANELİ</h1>
    <div style="display:flex; gap:10px; margin-bottom:20px; margin-top:20px;">
        <input id="l" type="number" value="10" placeholder="LİMİT (GB)" style="width:100px; margin:0">
        <button onclick="create()" class="btn">🔑 YENİ KEY OLUŞTUR</button>
    </div>
    <div id="newKey" style="color:var(--sec); font-family:'Share Tech Mono'; font-size:1.2rem; margin-bottom:20px;"></div>
    
    <h3>KULLANICI LİSTESİ</h3>
    <table id="tbl"></table>
</div>
<script>
const p = prompt("YÖNETİCİ ŞİFRESİ:");
function load(){{
    fetch('/api/admin/users?pwd='+p).then(r=>r.json()).then(d=>{{
        if(d.err) return document.body.innerHTML="<h1 style='color:red;text-align:center;margin-top:50px'>YETKİSİZ GİRİŞ</h1>";
        let h="<tr><th>KEY</th><th>LİMİT</th><th>KULLANILAN</th><th>DURUM</th><th>İŞLEM</th></tr>";
        d.users.forEach(u=>{{
            let btn = u.banned ? `<button onclick="ban('${{u.key}}',false)" style="color:#0f0; background:none; border:1px solid #0f0; cursor:pointer">AÇ</button>` : `<button onclick="ban('${{u.key}}',true)" style="color:red; background:none; border:1px solid red; cursor:pointer">BANLA</button>`;
            h+=`<tr><td>${{u.key}}</td><td>${{u.limit_gb}}</td><td>${{u.used_gb.toFixed(2)}}</td><td>${{u.banned?'BANLI':'AKTİF'}}</td><td>${{btn}}</td></tr>`;
        }});
        document.getElementById('tbl').innerHTML=h;
    }});
}}
function create(){{
    let l = document.getElementById('l').value;
    fetch('/api/admin/create?pwd='+p+'&limit='+l).then(r=>r.text()).then(d=>{{
        document.getElementById('newKey').innerText = "OLUŞTURULAN KEY: " + d;
        load();
    }});
}}
function ban(k, s){{
    fetch('/api/admin/ban', {{method:'POST', headers:{{'Content-Type':'application/json'}}, body:JSON.stringify({{pwd:p, key:k, ban:s}})}}).then(()=>load());
}}
load();
</script></body></html>"""

# --- ROUTES ---
@app.route('/')
def r1(): return render_template_string(HTML_LOGIN)
@app.route('/login')
def r2(): return render_template_string(HTML_LOGIN)
@app.route('/panel')
def r3(): return render_template_string(HTML_PANEL)
@app.route('/admin') # UNUTTUĞUM ROUTE BU!
def r4(): return render_template_string(HTML_ADMIN)
@app.route('/teslimat/<id>')
def r5(id):
    d = deliveries_col.find_one({"id": id})
    if d:
        # Arka planı siyah yapalım ki kör etmesin
        fixed_html = d['html'].replace("<body>", "<body style='background:#111; color:#ddd'>")
        return render_template_string(fixed_html)
    return "Bulunamadı"

# --- API ---
@app.route('/api/login', methods=['POST'])
def api_login():
    d=request.json; u=users_col.find_one({"key":d['key']})
    if not u or u.get('banned'): return jsonify({"ok":False,"msg":"Geçersiz Anahtar"})
    if not u.get('hwid'): users_col.update_one({"key":d['key']},{"$set":{"hwid":d['hwid']}})
    elif u['hwid']!=d['hwid']: return jsonify({"ok":False,"msg":"Farklı Cihaz Tespit Edildi!"})
    return jsonify({"ok":True})

@app.route('/api/data')
def api_data():
    k=request.headers.get('X-Key'); u=users_col.find_one({"key":k})
    if not u: return jsonify({"err":True})
    jobs=list(jobs_col.find({"user_key":k},{'_id':0}).sort("_id",-1))
    return jsonify({"used":u['used_gb'],"limit":u['limit_gb'],"jobs":[{"id":j['job_id'],"status":j['status'],"link":j['link'],"log":j.get('progress_log'),"did":j.get('delivery_id'),"date":j.get('date')} for j in jobs]})

@app.route('/api/add', methods=['POST'])
def api_add():
    k=request.headers.get('X-Key'); l=request.json.get('link'); u=users_col.find_one({"key":k})
    if not u or u['used_gb']>=u['limit_gb']: return jsonify({"msg":"KOTA LİMİTİ DOLDU!"})
    jid=str(uuid.uuid4())[:8]
    jobs_col.insert_one({"job_id":jid,"user_key":k,"link":l,"status":"SIRADA","date":get_tr_time(),"stop_requested":False})
    return jsonify({"msg":"İşlem Başlatıldı!"})

@app.route('/api/stop_job', methods=['POST'])
def api_stop():
    jobs_col.update_one({"job_id":request.json.get('jid')},{"$set":{"status":"DURDURULUYOR...","stop_requested":True}})
    return jsonify({"ok":True})

@app.route('/api/clear_history', methods=['GET'])
def api_clear():
    k=request.headers.get('X-Key')
    if k: jobs_col.delete_many({"user_key":k})
    return jsonify({"ok":True})

# WORKER API
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

# ADMIN API
@app.route('/api/admin/users')
def adm_u():
    if request.args.get('pwd')!=ADMIN_PASSWORD: return jsonify({"err":True})
    return jsonify({"users":list(users_col.find({},{'_id':0}))})

@app.route('/api/admin/create')
def adm_c():
    if request.args.get('pwd')!=ADMIN_PASSWORD: return "ERR"
    k="YAEL-"+''.join(random.choices(string.ascii_uppercase+string.digits,k=8))
    users_col.insert_one({"key":k,"limit_gb":int(request.args.get('limit')),"used_gb":0,"hwid":None,"banned":False})
    return k

@app.route('/api/admin/ban', methods=['POST'])
def adm_b():
    d=request.json
    if d.get('pwd')!=ADMIN_PASSWORD: return jsonify({"err":True})
    users_col.update_one({"key":d['key']},{"$set":{"banned":d['ban']}})
    return jsonify({"ok":True})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
