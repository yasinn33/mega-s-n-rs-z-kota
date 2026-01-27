import time
import requests
import os
import threading
from mega import Mega
from flask import Flask

# --- AYARLAR ---
RENDER_URL = os.environ.get("RENDER_URL") 
# Eğer environment variable çalışmazsa test için direkt adresi tırnak içine yazabilirsin:
# RENDER_URL = "https://senin-render-siten.onrender.com"

app = Flask(__name__)
mega = Mega()

# --- ARKA PLAN İŞÇİSİ ---
def worker_loop():
    print("---- WORKER BAŞLADI (7/24) ----")
    m = mega.login() # Anonim giriş
    
    while True:
        try:
            # 1. Patron'a (Render) sor
            try:
                r = requests.get(f"{RENDER_URL}/api/get_job", timeout=10).json()
            except:
                print("Render sitesine ulaşılamadı...")
                time.sleep(10)
                continue

            if r.get('found'):
                link = r['link']
                print(f"İş bulundu: {link}")
                
                # 2. İndir
                try:
                    filename = m.download_url(link)
                    print(f"İndi: {filename}")
                    
                    # 3. GoFile Yükle
                    srv = requests.get("https://api.gofile.io/getServer").json()['data']['server']
                    with open(filename, "rb") as f:
                        u = requests.post(f"https://{srv}.gofile.io/uploadFile", files={'file': f}).json()
                    
                    gofile_url = u['data']['downloadPage']
                    
                    # 4. Raporla
                    requests.post(f"{RENDER_URL}/api/done", json={"link": link, "url": gofile_url})
                    print(f"Tamamlandı: {gofile_url}")
                    
                    # 5. Sil
                    os.remove(filename)
                except Exception as e:
                    print(f"İndirme/Yükleme hatası: {e}")
                    # Hata olsa bile dosyayı silmeyi dene
                    if 'filename' in locals() and os.path.exists(filename):
                        os.remove(filename)
            else:
                print("İş yok, bekleniyor...")
                time.sleep(10)
                
        except Exception as e:
            print(f"Genel Hata: {e}")
            time.sleep(10)

# --- SAHTE WEB SUNUCUSU (UptimeRobot İçin) ---
@app.route('/')
def home():
    return "Worker Calisiyor! (7/24)"

if __name__ == '__main__':
    # İşçiyi ayrı bir kanalda (thread) başlat
    t = threading.Thread(target=worker_loop)
    t.start()
    
    # Web sunucusunu başlat (HuggingFace 7860 portunu sever)
    app.run(host='0.0.0.0', port=7860)
