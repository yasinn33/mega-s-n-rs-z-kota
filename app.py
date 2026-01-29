import certifi
from flask import Flask, request, jsonify, render_template_string, redirect, session, url_for
from pymongo import MongoClient
import os
import datetime
import uuid
import pytz
import random
import string

app = Flask(__name__)
app.secret_key = "Yaso333322"

# --- AYARLAR ---
MONGO_URI = os.environ.get("MONGO_URI") 
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['mega_leech']
queue = db['queue']
licenses_col = db['licenses']

TR_TZ = pytz.timezone('Europe/Istanbul')
ADMIN_PASSWORD = "YasoReis3628" # BURAYI KENDİNE GÖRE DEĞİŞTİR!

# --- HTML ŞABLONLARI ---

# 1. KULLANICI PANELİ
HTML_USER = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MEGA VIP SYSTEM</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        body { background: #f1f5f9; font-family: 'Segoe UI', sans-serif; }
        .log-box { background: #0f172a; color: #4ade80; height: 250px; overflow-y: auto; padding: 15px; border-radius: 8px; font-family: monospace; font-size: 0.85rem; }
    </style>
</head>
<body class="flex flex-col min-h-screen">
    <nav class="bg-slate-900 text-white p-4 flex justify-between items-center shadow-lg">
        <div class="font-bold text-xl tracking-wider"><i class="fa-solid fa-bolt text-yellow-400"></i> MEGA <span class="text-blue-400">VIP</span></div>
        <button onclick="logout()" class="text-xs bg-red-600 px-3 py-1 rounded hover:bg-red-700">ÇIKIŞ</button>
    </nav>

    <div id="loginScreen" class="flex-grow flex items-center justify-center p-4">
        <div class="bg-white p-8 rounded-xl shadow-2xl w-full max-w-md border-t-4 border-blue-600">
            <h2 class="text-2xl font-bold text-slate-800 mb-6 text-center">VIP Giriş</h2>
            <input type="text" id="licenseKey" class="w-full p-3 border rounded mb-4 focus:ring-2 focus:ring-blue-600 outline-none" placeholder="Lisans Anahtarı">
            <button onclick="login()" class="w-full bg-blue-600 text-white font-bold py-3 rounded shadow hover:bg-blue-700">GİRİŞ YAP</button>
            <p class="text-xs text-center text-gray-400 mt-4">ID: <span id="hwidDisplay">...</span></p>
        </div>
    </div>

    <div id="panelScreen" class="hidden container mx-auto p-4 max-w-4xl mt-6 space-y-6">
        <div class="bg-white p-6 rounded-lg shadow-lg">
            <div class="flex gap-2 mb-4">
                <input type="text" id="megaLink" class="flex-grow p-3 border rounded focus:ring-2 focus:ring-blue-500 outline-none" placeholder="Mega Linki...">
                <button onclick="startTask()" class="bg-blue-600 text-white px-6 py-3 rounded font-bold hover:bg-blue-700">BAŞLAT</button>
            </div>
            
            <div id="activeTaskArea" class="hidden bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4 flex justify-between items-center">
                <div>
                    <span class="font-bold text-yellow-700">İşlem Devam Ediyor...</span>
                    <p class="text-xs text-yellow-600" id="currentTaskLink">...</p>
                </div>
                <button onclick="stopTask()" class="bg-red-500 hover:bg-red-600 text-white font-bold py-2 px-4 rounded text-xs"><i class="fa-solid fa-stop"></i> DURDUR</button>
            </div>

            <div class="flex justify-between text-xs text-gray-500 mb-1">
                <span>CANLI LOGLAR</span>
                <span id="statusText" class="text-orange-500 font-bold">BEKLİYOR</span>
            </div>
            <div id="logBox" class="log-box"><div>[SİSTEM] Hazır. Link bekleniyor...</div></div>
        </div>

        <div id="resultArea" class="hidden bg-white p-6 rounded-lg shadow-lg border-l-4 border-green-500">
            <h3 class="font-bold text-green-700 mb-2">✅ İŞLEM TAMAMLANDI</h3>
            <div id="fileInfo" class="text-sm text-gray-600 mb-4"></div>
            <a id="downloadBtn" href="#" target="_blank" class="block w-full bg-green-600 text-white text-center font-bold py-3 rounded hover:bg-green-700">İNDİR</a>
        </div>
    </div>

    <script>
        let hwid = localStorage.getItem('hwid') || 'DEV-' + Math.random().toString(36).substr(2, 9).toUpperCase();
        localStorage.setItem('hwid', hwid);
        document.getElementById('hwidDisplay').innerText = hwid;
        let currentTaskId = null;
        let pollInterval = null;

        async function login() {
            const key = document.getElementById('licenseKey').value;
            const res = await fetch('/api/login', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ key, hwid })
            });
            const data = await res.json();
            if(data.success) {
                localStorage.setItem('vipKey', key);
                showPanel();
            } else alert(data.msg);
        }

        async function startTask() {
            const link = document.getElementById('megaLink').value;
            const key = localStorage.getItem('vipKey');
            if(!link) return alert("Link girin!");

            document.getElementById('logBox').innerHTML = '<div>[SİSTEM] Kuyruğa alınıyor...</div>';
            document.getElementById('resultArea').classList.add('hidden');
            
            const res = await fetch('/api/task', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ link, token: key, hwid })
            });
            const data = await res.json();

            if(data.success) {
                currentTaskId = data.taskId;
                document.getElementById('activeTaskArea').classList.remove('hidden');
                document.getElementById('currentTaskLink').innerText = link;
                startPolling();
            } else {
                alert(data.msg);
            }
        }

        async function stopTask() {
            if(!currentTaskId) return;
            if(!confirm("İşlemi iptal etmek istiyor musun?")) return;
            
            await fetch('/api/stop/' + currentTaskId);
            document.getElementById('logBox').innerHTML += '<div class="text-red-400">[SİSTEM] Kullanıcı tarafından durduruldu.</div>';
            document.getElementById('activeTaskArea').classList.add('hidden');
            if(pollInterval) clearInterval(pollInterval);
        }

        function startPolling() {
            if(pollInterval) clearInterval(pollInterval);
            pollInterval = setInterval(async () => {
                if(!currentTaskId) return;
                const res = await fetch('/api/status/' + currentTaskId);
                const data = await res.json();

                if(data.log) {
                    const box = document.getElementById('logBox');
                    const lastLog = box.lastElementChild ? box.lastElementChild.innerText : '';
                    if(!lastLog.includes(data.log)) {
                        box.innerHTML += `<div>${data.log}</div>`;
                        box.scrollTop = box.scrollHeight;
                    }
                }

                if(data.status === 'TAMAMLANDI') {
                    clearInterval(pollInterval);
                    document.getElementById('activeTaskArea').classList.add('hidden');
                    document.getElementById('statusText').innerText = 'TAMAMLANDI';
                    document.getElementById('resultArea').classList.remove('hidden');
                    document.getElementById('fileInfo').innerText = `Dosya: ${data.result.name} | Boyut: ${(data.result.size/1024/1024).toFixed(2)} MB`;
                    document.getElementById('downloadBtn').href = data.result.url;
                } else if (data.status.includes('HATA') || data.status === 'DURDURULDU') {
                    clearInterval(pollInterval);
                    document.getElementById('activeTaskArea').classList.add('hidden');
                    document.getElementById('statusText').innerText = data.status;
                }
            }, 2000);
        }

        function showPanel() {
            document.getElementById('loginScreen').classList.add('hidden');
            document.getElementById('panelScreen').classList.remove('hidden');
        }
        function logout() { localStorage.removeItem('vipKey'); location.reload(); }
        if(localStorage.getItem('vipKey')) showPanel();
    </script>
</body>
</html>
"""

# 2. ADMIN PANELİ HTML
HTML_ADMIN = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <title>ADMIN PANEL</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-gray-900 text-white p-6 font-mono">
    <div class="max-w-6xl mx-auto">
        <div class="flex justify-between items-center mb-6">
            <h1 class="text-2xl font-bold text-blue-400">YÖNETİCİ KONTROL PANELİ</h1>
            <a href="/logout" class="bg-red-600 px-4 py-2 rounded text-sm">Çıkış</a>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div class="bg-gray-800 p-4 rounded border-l-4 border-blue-500">
                <div class="text-gray-400 text-xs">TOPLAM LİSANS</div>
                <div class="text-2xl font-bold">{{ stats.total }}</div>
            </div>
            <div class="bg-gray-800 p-4 rounded border-l-4 border-green-500">
                <div class="text-gray-400 text-xs">AKTİF LİSANS</div>
                <div class="text-2xl font-bold">{{ stats.active }}</div>
            </div>
            <div class="bg-gray-800 p-4 rounded border-l-4 border-red-500">
                <div class="text-gray-400 text-xs">BANLI LİSANS</div>
                <div class="text-2xl font-bold">{{ stats.banned }}</div>
            </div>
             <div class="bg-gray-800 p-4 rounded border-l-4 border-yellow-500">
                <div class="text-gray-400 text-xs">BEKLEYEN İŞLER</div>
                <div class="text-2xl font-bold">{{ stats.queue }}</div>
            </div>
        </div>

        <div class="bg-gray-800 p-6 rounded mb-8">
            <h2 class="font-bold mb-4 border-b border-gray-700 pb-2">LİSANS ÜRETİM MERKEZİ</h2>
            <form action="/admin/generate" method="post" class="flex gap-4">
                <button type="submit" name="count" value="1" class="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded font-bold">1 Tane Üret</button>
                <button type="submit" name="count" value="10" class="bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded font-bold">10 Tane (Toplu)</button>
            </form>
            
            {% if new_keys %}
            <div class="mt-4 p-4 bg-gray-900 rounded border border-green-500">
                <p class="text-green-400 mb-2">✅ Üretilen Lisanslar (Kopyala):</p>
                <textarea class="w-full bg-black text-green-300 p-2 text-sm h-32 font-mono" readonly>{% for k in new_keys %}{{ k }}&#13;&#10;{% endfor %}</textarea>
            </div>
            {% endif %}
        </div>

        <div class="bg-gray-800 rounded overflow-hidden">
             <h2 class="font-bold p-4 border-b border-gray-700 bg-gray-700">LİSANS YÖNETİMİ</h2>
             <div class="overflow-x-auto">
                <table class="w-full text-sm text-left text-gray-400">
                    <thead class="bg-gray-900 uppercase text-xs">
                        <tr>
                            <th class="p-3">Anahtar</th>
                            <th class="p-3">Durum</th>
                            <th class="p-3">Cihaz (HWID)</th>
                            <th class="p-3">Oluşturma</th>
                            <th class="p-3">İşlem</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for lic in licenses %}
                        <tr class="border-b border-gray-700 hover:bg-gray-700">
                            <td class="p-3 font-mono text-white">{{ lic.key }}</td>
                            <td class="p-3">
                                {% if lic.isActive %}
                                <span class="bg-green-900 text-green-300 px-2 py-1 rounded text-xs">AKTİF</span>
                                {% else %}
                                <span class="bg-red-900 text-red-300 px-2 py-1 rounded text-xs">PASİF</span>
                                {% endif %}
                            </td>
                            <td class="p-3 font-mono text-xs">{{ lic.hwid or 'Girilmedi' }}</td>
                            <td class="p-3">{{ lic.created_at.strftime('%d.%m.%Y') if lic.created_at else '-' }}</td>
                            <td class="p-3 flex gap-2">
                                {% if lic.isActive %}
                                <a href="/admin/ban/{{ lic.key }}" class="bg-red-600 hover:bg-red-700 text-white px-2 py-1 rounded text-xs">BANLA</a>
                                {% else %}
                                <a href="/admin/unban/{{ lic.key }}" class="bg-green-600 hover
