import subprocess
import sys
import sqlite3
import os

# Path database
GHOST_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'database/ghost.db'))

# 1. Ambil perintah kodingan
cmd = sys.argv[1:]
cmd_str = " ".join(cmd)
if not cmd:
    print("[MONITOR] Mana perintahnya jirr? Contoh: python3 monitor_run.py python3 brain/api.py")
    sys.exit(1)

# --- PINTU PENGECUALIAN ---
if "jess.py" in cmd_str or "monitor_run.py" in cmd_str:
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        # Ini biar kalau lu Ctrl+C, dia langsung diem, gak usah ngeluarin traceback panjang
        print("\n[MONITOR] Jess dimatikan Jen. Aman.")
        sys.exit(0)
    sys.exit(0)
# --------------------------
# --------------------------

print(f"[MONITOR] Mulai memantau proses: {cmd_str} ...")

# 2. Jalanin kodingan lu
process = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=sys.stdout, text=True)

error_buffer = []

# 3. Baca output error terminal secara real-time
while True:
    line = process.stderr.readline()
    if not line and process.poll() is not None:
        break
    if line:
        sys.stderr.write(line) 
        if 'File "' in line and 'line ' in line:
            error_buffer.append(line.strip())

# 4. Filter error
if error_buffer:
    latest_traceback = None
    for err in reversed(error_buffer):
        # Filter: bukan library sistem, dan harus ada path file yang jelas
        is_internal_lib = "/usr/lib" in err or "site-packages" in err or "dist-packages" in err
        if "/" in err and not is_internal_lib:
            latest_traceback = err
            break
            
    if not latest_traceback:
        latest_traceback = error_buffer[-1]

    print(f"\n[MONITOR] Ketemu error valid blay: {latest_traceback}")
    
    try:
        conn = sqlite3.connect(GHOST_DB_PATH)
        conn.execute(
            "INSERT INTO activity_logs (process_name, window_title, timestamp) VALUES (?, ?, datetime('now'))",
            ("Terminal_Monitor", latest_traceback)
        )
        conn.commit()
        conn.close()
        print("[MONITOR] GOKIL! Error berhasil dicatat otomatis ke ghost.db 🚀")
    except Exception as e:
        print(f"[MONITOR] Waduh gagal insert ke db: {e}")