import certifi
from flask import Flask, request, jsonify, render_template_string
from pymongo import MongoClient
import os
import datetime
import uuid
import pytz

app = Flask(__name__)

# --- AYARLAR ---
# Render'da Environment Variable olarak MONGO_URI girili olmalı!
MONGO_URI = os.environ.get("MONGO_URI") 
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['mega_leech']
queue = db['queue']
licenses_col = db['licenses'] # Yeni Lisans Tablosu

# Saat Ayarı (Türkiye)
TR_TZ = pytz.timezone('Europe/Istanbul')

# --- HTML (KURUMSAL MAVİ & BEYAZ TASARIM) ---
HTML_PAGE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MEGA ENTERPRISE | Güvenli Transfer</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        body { background-color: #f1f5f9; font-family: 'Segoe UI', sans-serif; }
        .log-terminal { 
            background: #0f172a; color: #4ade80; font-family: 'Consolas', monospace; 
            height: 200px; overflow-y: auto; font-size: 0.85rem; padding: 15px; 
            border-radius: 8px; border: 1px solid #334155; box-shadow: inset 0 0 10px rgba(0,0,0,0.5);
        }
        .log-terminal::-webkit-scrollbar { width: 6px; }
        .log-terminal::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
        .hidden { display: none; }
        .fade-in { animation: fadeIn 0.5s ease-in; }
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    </style>
</head>
<body class="flex flex-col min-h-screen">

    <nav class="bg-blue-900 text-white p-4 shadow-lg flex justify-between items-center z-50">
        <div class="flex items-center gap-3">
            <div class="bg-white text-blue-900 p-2 rounded-lg shadow"><i class="fa-solid fa-cloud-arrow-down text-xl"></i></div>
            <div>
                <h1 class="font-bold text-lg tracking-wide">MEGA SAVER</h1>
                <p class="text-xs text-blue-200">Enterprise Edition v3.0</p>
            </div>
        </div>
        <div id="userStatus" class="hidden flex items-center gap-4 text-sm">
            <span class="bg-blue-800 px-3 py-1 rounded border border-blue-700 flex items-center gap-2">
                <i class="fa-solid fa-key"></i> <span id="displayKey" class="font-mono">...</span>
            </span>
            <button onclick="logout()" class="text-red-200 hover:text-white transition"><i class="fa-solid fa-power-off"></i> Çıkış</button>
        </div>
    </nav>

    <div id="loginSection" class="flex-grow flex items-center justify-center p-4 fade-in">
        <div class="bg-white p-8 rounded-xl shadow-2xl w-full max-w-md border-t-4 border-blue-600">
            <div class="text-center mb-8">
                <div class="bg-blue-50 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                    <i class="fa-solid fa-shield-halved text-3xl text-blue-600"></i>
                </div>
                <h2 class="text-2xl font-bold text-slate-800">Güvenli Giriş</h2>
                <p class="text-sm text-gray-500">Lisans anahtarınız ile oturum açın.</p>
            </div>
            
            <div class="space-y-4">
                <div>
                    <label class="block text-gray-700 text-sm font-bold mb-2">Lisans Anahtarı</label>
                    <div class="relative">
                        <span class="absolute inset-y-0 left-0 pl-3 flex items-center text-gray-400"><i class="fa-solid fa-ticket"></i></span>
                        <input type="text" id="licenseKey" class="w-full pl-10 p-3 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 outline-none transition" placeholder="Örn: MEGA-VIP-XXXX">
                    </div>
                </div>
                <button onclick="login()" id="loginBtn" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded shadow-lg transition duration-200 transform hover:scale-[1.02]">
                    Sisteme Bağlan
                </button>
            </div>
            <p class="text-xs text-gray-400 mt-6 text-center">Device ID: <span id="deviceIdDisplay" class="font-mono">...</span></p>
        </div>
    </div>

    <div id="panelSection" class="hidden container mx-auto p-4 max-w-5xl mt-6 space-y-6 fade-in">
        
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="bg-white p-5 rounded-lg shadow-md border-l-4 border-blue-500 flex items-center gap-4">
                <div class="bg-blue-100 p-3 rounded-full text-blue-600"><i class="fa-solid fa-gauge-high text-xl"></i></div>
                <div><h3 class="font-bold text-slate-700">Limitsiz Hız</h3><p class="text-xs text-gray-500">Premium Sunucu</p></div>
            </div>
            <div class="bg-white p-5 rounded-lg shadow-md border-l-4 border-purple-500 flex items-center gap-4">
                <div class="bg-purple-100 p-3 rounded-full text-purple-600"><i class="fa-solid fa-server text-xl"></i></div>
                <div><h3 class="font-bold text-slate-700">50 GB Kota</h3><p class="text-xs text-gray-500">Büyük Arşiv Desteği</p></div>
            </div>
            <div class="bg-white p-5 rounded-lg shadow-md border-l-4 border-green-500 flex items-center gap-4">
                <div class="bg-green-100 p-3 rounded-full text-green-600"><i class="fa-solid fa-user-lock text-xl"></i></div>
                <div><h3 class="font-bold text-slate-700">Oturum Koruması</h3><p class="text-xs text-gray-500">Cihaz Kilitli</p></div>
            </div>
        </div>

        <div class="bg-white rounded-lg shadow-lg overflow-hidden">
            <div class="bg-slate-50 p-4 border-b flex justify-between items-center">
                <h3 class="font-bold text-slate-700"><i class="fa-solid fa-link text-blue-500 mr-2"></i>Yeni İşlem Başlat</h3>
                <span class="text-xs bg-green-100 text-green-700 px-2 py-1 rounded font-bold">Sistem Aktif</span>
            </div>
            <div class="p-6">
                <div class="flex gap-2 mb-4">
                    <input type="text" id="megaLink" class="flex-grow p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-slate-700" placeholder="https://mega.nz/file/...">
                    <button onclick="addTask()" class="bg-slate-800 hover:bg-slate-900 text-white px-8 py-3 rounded-lg font-bold transition flex items-center gap-2">
                        <i class="fa-solid fa-rocket"></i> BAŞLAT
                    </button>
                </div>

                <div class="flex justify-between text-xs text-gray-500 mb-2">
                    <span>> Canlı İşlem Logları</span>
                    <span id="statusIndicator" class="text-orange-500 animate-pulse">● Bekleniyor...</span>
                </div>
                <div id="logBox" class="log-terminal">
                    <div>[SYSTEM] Sistem hazır. Link bekleniyor...</div>
                </div>
            </div>
        </div>

        <div id="resultArea" class="hidden bg-white p-6 rounded-lg shadow-lg border-2 border-green-500">
            <h3 class="font-bold text-green-700 mb-2 flex items-center gap-2"><i class="fa-solid fa-circle-check"></i> İşlem Tamamlandı!</h3>
            <div id="fileInfo" class="text-sm text-gray-600 mb-4"></div>
            <a id="downloadBtn" href="#" target="_blank" class="block w-full bg-green-600 hover:bg-green-700 text-white text-center font-bold py-3 rounded shadow transition">
                <i class="fa-solid fa-download"></i> DOSYAYI İNDİR
            </a>
        </div>

    </div>

    <footer class="bg-slate-900 text-slate-500 py-6 mt-auto text-center text-xs">
        <p>&copy; 2026 Mega Saver Enterprise. <span id="footerId"></span></p>
    </footer>

    <script>
        // Cihaz Kimliği (HWID)
        let hwid = localStorage.getItem('hwid');
        if (!hwid) { hwid = 'DEV-' + Math.random().toString(36).substr(2, 9).toUpperCase(); localStorage.setItem('hwid', hwid); }
        document.getElementById('deviceIdDisplay').innerText = hwid;
        document.getElementById('footerId').innerText = hwid;

        let currentTaskId = null;
        let pollInterval = null;

        async function login() {
            const key = document.getElementById('licenseKey').value;
            const btn = document.getElementById('loginBtn');
            if(!key) return alert("Anahtar giriniz!");

            btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Kontrol Ediliyor...';
            
            try {
                const res = await fetch('/api/login', {
                    method: 'POST', headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ key, hwid })
                });
                const data = await res.json();

                if(data.success) {
                    localStorage.setItem('licenseToken', key);
                    showPanel(key);
                } else {
                    alert(data.msg);
                    btn.innerHTML = 'Sisteme Bağlan';
                }
            } catch(e) { alert("Sunucu Hatası!"); btn.innerHTML = 'Sisteme Bağlan'; }
        }

        async function addTask() {
            const link = document.getElementById('megaLink').value;
            const token = localStorage.getItem('licenseToken');
            if(!link) return alert("Link boş!");

            document.getElementById('logBox').innerHTML = '<div>[SYSTEM] İstek kuyruğa alınıyor...</div>';
            document.getElementById('resultArea').classList.add('hidden');
            document.getElementById('statusIndicator').className = 'text-blue-500 animate-pulse';
            document.getElementById('statusIndicator').innerText = '● İşleniyor...';

            const res = await fetch('/api/task', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ link, token, hwid })
            });
            const data = await res.json();

            if(data.success) {
                currentTaskId = data.taskId;
                startPolling();
            } else {
                alert(data.msg);
                document.getElementById('logBox').innerHTML += `<div class="text-red-400">[HATA] ${data.msg}</div>`;
            }
        }

        function startPolling() {
            if(pollInterval) clearInterval(pollInterval);
            pollInterval = setInterval(async () => {
                const res = await fetch('/api/status/' + currentTaskId);
                const data = await res.json();

                if(data.log) {
                    const box = document.getElementById('logBox');
                    // Son logu kontrol et, aynıysa yazma (spam engelleme)
                    const lastLog = box.lastElementChild ? box.lastElementChild.innerText : '';
                    if(!lastLog.includes(data.log)) {
                        box.innerHTML += `<div>${data.log}</div>`;
                        box.scrollTop = box.scrollHeight;
                    }
                }

                if(data.status === 'TAMAMLANDI') {
                    clearInterval(pollInterval);
                    document.getElementById('statusIndicator').className = 'text-green-500';
                    document.getElementById('statusIndicator').innerText = '● Tamamlandı';
                    document.getElementById('resultArea').classList.remove('hidden');
                    document.getElementById('fileInfo').innerText = `Dosya: ${data.result.name} | Boyut: ${(data.result.size/1024/1024).toFixed(2)} MB`;
                    document.getElementById('downloadBtn').href = data.result.url;
                } else if (data.status.includes('HATA')) {
                    clearInterval(pollInterval);
                    document.getElementById('statusIndicator').className = 'text-red-500';
                    document.getElementById('statusIndicator').innerText = '● Hata';
                }
            }, 2000);
        }

        function showPanel(key) {
            document.getElementById('loginSection').classList.add('hidden');
            document.getElementById('panelSection').classList.remove('hidden');
            document.getElementById('userStatus').classList.remove('hidden');
            document.getElementById('displayKey').innerText = key;
        }

        function logout() { localStorage.removeItem('licenseToken'); location.reload(); }

        if(localStorage.getItem('licenseToken')) showPanel(localStorage.getItem('licenseToken'));
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

# --- API ENDPOINTS ---

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    key = data.get('key')
    browser_id = data.get('hwid')

    # Lisans Kontrolü
    lic = licenses_col.find_one({"key": key})
    
    if not lic: return jsonify({"success": False, "msg": "❌ Geçersiz Anahtar!"})
    if not lic.get('isActive', True): return jsonify({"success": False, "msg": "🚫 Lisans Pasif Durumda."})
    
    # Süre Kontrolü (Opsiyonel: Eğer DB'de expiryDate varsa)
    # if lic.get('expiryDate') and datetime.datetime.now() > lic['expiryDate']: return ...

    # HWID Kilidi
    db_hwid = lic.get('hwid')
    if db_hwid and db_hwid != browser_id:
        return jsonify({"success": False, "msg": "🔒 Bu lisans başka bir cihazda kilitli!"})
    
    # İlk girişse kilitle
    if not db_hwid:
        licenses_col.update_one({"key": key}, {"$set": {"hwid": browser_id}})

    return jsonify({"success": True})

@app.route('/api/task', methods=['POST'])
def add_task():
    data = request.json
    token = data.get('token')
    hwid = data.get('hwid')
    link = data.get('link')

    # İşlemden önce tekrar lisans onayı
    lic = licenses_col.find_one({"key": token, "hwid": hwid, "isActive": True})
    if not lic: return jsonify({"success": False, "msg": "Yetkisiz Erişim!"})

    task_id = str(uuid.uuid4())
    queue.insert_one({
        "task_id": task_id,
        "link": link,
        "status": "SIRADA",
        "log": "[KUYRUK] İşlem sıraya alındı...",
        "created_at": datetime.datetime.now(TR_TZ),
        "user_key": token
    })
    return jsonify({"success": True, "taskId": task_id})

@app.route('/api/status/<task_id>')
def check_status(task_id):
    task = queue.find_one({"task_id": task_id}, {"_id": 0})
    if not task: return jsonify({"status": "HATA", "log": "İşlem bulunamadı."})
    return jsonify(task)

# --- WORKER İÇİN API (Hugging Face Buraya Bağlanacak) ---

@app.route('/api/get_job')
def get_job():
    # Sadece SIRADA olan en eski işi al ve ISLENIYOR yap
    job = queue.find_one_and_update(
        {"status": "SIRADA"},
        {"$set": {"status": "ISLENIYOR", "log": "[WORKER] Dosya işleniyor..."}},
        sort=[("created_at", 1)]
    )
    if job:
        return jsonify({"found": True, "link": job['link'], "task_id": job['task_id']})
    return jsonify({"found": False})

@app.route('/api/done', methods=['POST'])
def report_done():
    d = request.json
    task_id = d.get('task_id')
    status = d.get('status')
    
    update_data = {"status": status}
    if 'log' in d: update_data['log'] = d['log']
    if 'result' in d: update_data['result'] = d['result'] # İndirme linki burada olacak
    
    queue.update_one({"task_id": task_id}, {"$set": update_data})
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
