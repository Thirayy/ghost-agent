import subprocess
import re

def get_port_owner(port):
    """Ngecek aplikasi apa yang lagi pake port tertentu"""
    try:
        # Jalain lsof buat nyari tahu port
        result = subprocess.run(f"lsof -i :{port} -t", shell=True, capture_output=True, text=True)
        pid = result.stdout.strip()
        if pid:
            # Cari nama proses berdasarkan PID
            proc_info = subprocess.run(f"ps -p {pid} -o comm=", shell=True, capture_output=True, text=True)
            return f"Port {port} lagi dipake sama proses: **{proc_info.stdout.strip()}** (PID: {pid})"
        return f"Port {port} kosong melompong blay, aman digas!"
    except Exception as e:
        return f"Gagal ngecek port: {e}"

def kill_port_process(port):
    """Langsung eksekusi mati proses di port tertentu"""
    try:
        result = subprocess.run(f"lsof -i :{port} -t", shell=True, capture_output=True, text=True)
        pid = result.stdout.strip()
        if pid:
            # Pecah kalau ada beberapa PID yang nempel
            pids = pid.split('\n')
            for p in pids:
                subprocess.run(f"kill -9 {p}", shell=True)
            return f"Selesai blay! Proses di port {port} (PID: {pid}) udah w eksekusi mati (SIGKILL)."
        return f"Kaga ada proses apa-apa di port {port}, aman."
    except Exception as e:
        return f"Gagal ngebunuh proses di port {port}: {e}"