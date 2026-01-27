# worker.py - 7/24 Arkada Çalışan Köle
import time
import requests
import os
from mega import Mega

# BURAYI RENDER SİTE ADRESİNLE DEĞİŞTİRECEKSİN
RENDER_URL = os.environ.get("RENDER_URL") 

mega = Mega()
m = mega.login() # Anonim giriş

def upload_gofile(path):
    # En iyi gofile sunucusunu bul
    srv = requests.get("https://api.gofile.io/getServer").json()['data']['server']
    print(f"Yükleniyor: {srv}...")
    with open(path, "rb") as f:
        # Dosyayı yükle
        u = requests.post(f"https://{srv}.gofile.io/uploadFile", files={'file': f}).json()
    return u['data']['downloadPage']

print("---- WORKER BAŞLADI (7/24) ----")

while True:
    try:
        # 1. Patron'a (Render) sor: İş var mı?
        r = requests.get(f"{RENDER_URL}/api/get_job").json()
        
        if r['found']:
            link = r['link']
            print(f"İş bulundu: {link}")
            
            # 2. İndir (Mega -> HuggingFace Diskine)
            print("Mega'dan indiriliyor...")
            filename = m.download_url(link)
            print(f"İndi: {filename}")
            
            # 3. Yükle (HuggingFace -> GoFile)
            print("GoFile'a yükleniyor...")
            gofile_url = upload_gofile(filename)
            
            # 4. Raporla
            requests.post(f"{RENDER_URL}/api/done", json={"link": link, "url": gofile_url})
            print(f"Bitti: {gofile_url}")
            
            # 5. Sil (Diski temizle)
            os.remove(filename)
            
        else:
            print("İş yok, bekleniyor...")
            time.sleep(10) # 10 saniye bekle
            
    except Exception as e:
        print(f"Hata: {e}")
        time.sleep(10)
