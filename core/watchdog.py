import os
import sys
import subprocess
from db_manager import get_connect

# Batas toleransi kelakuan buruk (dalam hitungan log, misal 1 log = 5-10 detik)
# Kalau dalam 15 menit terakhir ada lebih dari 15 log Instagram/Medsos, Jess bakal ngamuk.
DISTRACTION_THRESHOLD = 5 

def check_distraction():
    # List nama proses atau judul window yang diidentifikasi sebagai dosa/distraksi
    bad_apps = ['instagram', 'tiktok', 'facebook', 'twitter', 'youtube', 'discord', 'spotify']
    
    with get_connect() as conn:
        # Ambil aktivitas dalam 15 menit terakhir
        query = """
            SELECT process_name, window_title 
            FROM activity_logs 
            WHERE timestamp >= datetime('now', '-15 minutes')
        """
        rows = conn.execute(query).fetchall()
        
    if not rows:
        return

    distraction_count = 0
    detected_app = ""
    
    for r in rows:
        proc = r['process_name'].lower()
        title = r['window_title'].lower()
        
        # Cek apakah ada aplikasi haram yang lagi aktif
        if any(bad in proc or bad in title for bad in bad_apps):
            distraction_count += 1
            if not detected_app:
                detected_app = r['process_name']

    # Jika melewati batas toleransi, tembak Zar pake Whiplash Notification!
    if distraction_count > DISTRACTION_THRESHOLD:
        trigger_whiplash(detected_app)

def trigger_whiplash(app_name):
    title = "🚨 [JESS ALERT] DETEKSI DOSA INTERNET"
    message = f"kerjaan bukannya di kelarin,  malah asyik mantengin {app_name}. KLIK SINI KALO MAU DEBAT!"
    
    # Perintah buat ngebuka terminal baru langsung ke room chat Jess pas diklik
    # Kita pake wrapper bash untuk trigger action notifikasi
    # Jalankan notify-send dengan hint atau action (GNOME support default action)
    cmd = [
        "notify-send",
        title,
        message,
        "-i", "dialog-warning",
        "-u", "critical"
    ]
    
    # Eksekusi pop-up ke layar GNOME
    subprocess.run(cmd)
    
    # Otomatis pop terminal ke depan layar biar Zar auto panik (Opsi Hardcore)
    # Lo bisa hapus baris di bawah ini kalau berasa terlalu mengganggu, tapi ini efektif biar tobat
    os.system("gnome-terminal -- bash -c 'python3 ~/ghost-agent/brain/jess.py; exec bash'")

if __name__ == '__main__':
    check_distraction()
