import sys
import os
import requests
import json
import re
import subprocess

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../core')))
from db_manager import get_connect


def scan_project(path):
    if not path:
        return "Path kosong."

    if not os.path.exists(path):
        return f"Path tidak ditemukan: {path}"

    results = []
    try:
        for root, dirs, files in os.walk(path):
            dirs[:] = sorted([d for d in dirs if not d.startswith('.')])
            results.append(f"[DIR] {root}")
            for d in sorted(dirs):
                results.append(f"[DIR] {os.path.join(root, d)}")
            for f in sorted(files):
                results.append(f"[FILE] {os.path.join(root, f)}")
    except PermissionError as e:
        results.append(f"[PERMISSION ERROR] {e}")

    return "\n".join(results)


# ⚙️ ENDPOINT /API/CHAT MESSAGES ARRAY
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5-coder:1.5b"

chat_history = []
last_searched_path = None 

# --- OTOMATISASI DATA MEMORI JESS ---
def init_jess_memory_db():
    try:
        with get_connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jess_memory (
                    folder_key TEXT PRIMARY KEY,
                    full_path TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
    except Exception as e:
        print(f"[DB Init Debug]: Gagal inisialisasi tabel memori: {e}")

# --- FUNGSI "PENCUCI OTAK" JESS (CLEAN FORMAL SPEAK) ---
def clean_formal_speak(text):
    text = text.replace("Saya", "gw")
    text = text.replace("saya", "gw")
    text = text.replace("Anda", "lu")
    text = text.replace("anda", "lu")
    text = text.replace("Ada yang bisa saya bantu?", "Ada apa blay?")
    return text

# --- INI FUNGSI TAMBAHAN BUAT JESS NGOMONG (PIPER TTS) ---
def jess_speak(text):
    piper_path = "./piper/piper"
    model_path = "./piper/id_ID-news_tts-medium.onnx"
    
    # Pake escape hex biar aman dari bug markdown UI
    clean_text = re.sub(r'\x60\x60\x60.*?\x60\x60\x60', '', text, flags=re.DOTALL)
    clean_text = clean_text.replace('`', '')
    
    clean_text = clean_text.lower()
    clean_text = re.sub(r'\bgw\b|\bw\b', 'gue', clean_text)
    clean_text = re.sub(r'\bblay\b|\bbray\b', 'berai', clean_text)
    clean_text = re.sub(r'\bcoii\b|\bcoi\b', 'koy', clean_text)
    clean_text = re.sub(r'\bkaga\b|\bkagak\b', 'kagak', clean_text)
    clean_text = re.sub(r'wkwk\w*', 'wek wek', clean_text)
    clean_text = re.sub(r'\bjirr\b|\bjir\b', 'jewer', clean_text) 
    
    safe_text = clean_text.replace('"', '\\"')
    
    command = f'echo "{safe_text}" | {piper_path} --model {model_path} --length-scale 0.88 --sentence-silence 0.1 --output_file output.wav > /dev/null 2>&1 && aplay output.wav > /dev/null 2>&1 &'
    
    try:
        subprocess.run(command, shell=True)
    except Exception as e:
        print(f"\n[Voice Error]: Gagal ngomong bray: {e}")
# ---------------------------------------------------------

def get_identity_context():
    with get_connect() as conn:
        row = conn.execute("SELECT value FROM identity_profile WHERE key = 'psychological_profile'").fetchone()
    if row:
        return "Data Jen: Dev IT & Student DKV, suka Mikrotik, Python FastAPI, Laravel, suka denger breakbeat, pengen bikin Ghost Agent jadi alter ego/Jarvis."
    return "User: Tijen (Jen), dev IT."

def get_personal_facts(user_prompt):
    global last_searched_path
    facts = []
    prompt_lower = user_prompt.lower()
    
    BASE_PROJECT_PATH = "/home/zar/ghost-agent"
    USER_HOME_PATH = "/home/zar"
    
    if last_searched_path is None:
        last_searched_path = USER_HOME_PATH
    
    if any(k in prompt_lower for k in ['musik', 'lagu', 'playlist', 'breakbeat', 'dj', 'denger', 'nyetel', 'youtube', 'yt']):
        facts.append("FAKTA MUTLAK: Tijen SUKA musik Breakbeat, DJ Remix, YB, Bravy, Aloy, Jayjax, dan Marapthon. JANGAN PERNAH ngarang judul lagu fiktif!")
    
    if any(k in prompt_lower for k in ['ngoding', 'code', 'kerja', 'project', 'aktivitas', 'evaluasi', 'produktif', 'script', 'python', 'php', 'laravel', 'fastapi', 'vscode', 'db', 'cia']):
        facts.append("FAKTA MUTLAK: Yang punya laptop, nulis script, bikin fungsi, dan produktif ngoding seharian itu TIJEN (lu), bukan Jess (gw). Jess cuma AI background.")
        
    if any(k in prompt_lower for k in ['buka', 'aplikasi', 'tab', 'browser', 'cek', 'log', 'terminal', 'detail', 'wa', 'whatsapp', 'brave']):
        facts.append("FAKTA MUTLAK: Data aplikasi & tab browser yang tertera adalah milik TIJEN yang sedang aktif dijalankan di laptopnya. Jess TIDAK MEMILIKI aplikasi sendiri.")

    # Deteksi kalo user minta liat/intip/isi folder/file - TRIGGER SCAN OTOMATIS
    wants_to_view = any(k in prompt_lower for k in ['liat', 'intip', 'isi', 'isinya', 'lihat', 'cek folder', 'cek file', 'cek isi', 'baca file', 'buka file', 'show', 'tampil'])
    
    # SMART: Extract SEMUA folder/file names dari prompt, bukan hanya 1
    folder_names = []
    
    # Cari absolute paths dulu
    abs_paths = re.findall(r'/[a-zA-Z0-9_\-\.\/]+', user_prompt)
    if abs_paths:
        for p in abs_paths:
            if os.path.exists(p):
                folder_names.append((p, 'absolute'))
    
    # Cari folder names relatif (e.g., tia-backend, tia-frontend)
    rel_folders = re.findall(r'\b([a-zA-Z0-9_\-]+(?:-[a-zA-Z0-9_\-]+)*)\b', user_prompt)
    for folder in rel_folders:
        # Skip common words
        if folder.lower() not in ['lu', 'gw', 'w', 'dy', 'sama', 'dan', 'yang', 'buat', 'ada', 'apa', 'isi', 'folder', 'file', 'ada', 'bisa', 'liatin', 'liat', 'intip', 'cek']:
            # Check if folder exists in /home/zar
            potential_path = os.path.join(USER_HOME_PATH, folder)
            if os.path.exists(potential_path) and (potential_path, 'relative') not in folder_names:
                folder_names.append((potential_path, 'relative'))
    
    # SCAN SEMUA FOLDERS yang ketemu
    scanned_paths = set()  # Prevent duplicates
    for path, path_type in folder_names:
        if path not in scanned_paths and os.path.exists(path):
            scanned_paths.add(path)
            last_searched_path = path
            
            try:
                if os.path.isdir(path):
                    files = subprocess.check_output(f"ls -p '{path}'", shell=True).decode().strip().split("\n")
                    files_list = "\n".join([f"  - {f}" for f in files if f]) if files else "  - (kosong)"
                    facts.append(f"LOG SISTEM UTAMA: Isi direktori {path}:\n{files_list}")
                    print(f"[DEBUG SCAN]: Scanned folder: {path}")
                elif os.path.isfile(path):
                    if path.endswith(('.log', '.txt')):
                        content = subprocess.check_output(f"tail -n 10 '{path}'", shell=True).decode().strip()
                        facts.append(f"LOG SISTEM UTAMA: Isi file {path} (10 baris terakhir):\n```\n{content}\n```")
                    else:
                        content = subprocess.check_output(f"head -n 15 '{path}'", shell=True).decode().strip()
                        facts.append(f"LOG SISTEM UTAMA: Isi file {path} (15 baris pertama):\n```\n{content}\n```")
            except Exception as e:
                facts.append(f"LOG SISTEM UTAMA: Gagal scan {path}: {e}")
    
    # Jika user minta liat tapi gak ada folder terdeteksi, scan default
    if wants_to_view and not scanned_paths:
        target_path = last_searched_path if last_searched_path else USER_HOME_PATH
        if os.path.exists(target_path):
            try:
                if os.path.isdir(target_path):
                    files = subprocess.check_output(f"ls -p '{target_path}'", shell=True).decode().strip().split("\n")
                    files_list = "\n".join([f"  - {f}" for f in files if f]) if files else "  - (kosong)"
                    facts.append(f"LOG SISTEM UTAMA: Default scan direktori {target_path}:\n{files_list}")
                    print(f"[DEBUG SCAN]: Default scan: {target_path}")
            except Exception as e:
                facts.append(f"LOG SISTEM UTAMA: Gagal scan default: {e}")
        last_searched_path = target_path 
        try:
            if os.path.isdir(target_path):
                files = subprocess.check_output(f"ls -p '{target_path}'", shell=True).decode().strip().split("\n")
                files_list = "\n".join([f"  - {f}" for f in files if f]) if files else "  - Kosong melompong bray"
                facts.append(f"LOG SISTEM UTAMA: Isi direktori dari path {target_path} beneran ada, ini isinya:\n{files_list}")
            elif os.path.isfile(target_path):
                if target_path.endswith(('.log', '.txt')):
                    content = subprocess.check_output(f"tail -n 25 '{target_path}'", shell=True).decode().strip()
                    print(f"\n[DEBUG DATA ASLI LOG]:\n{content}\n")
                    facts.append(
                        f"LOG SISTEM UTAMA: Ini adalah 25 baris TERAKHIR dari file log/catatan {target_path}.\n"
                        f"Analisis log error ini secara akurat jika Tijen bertanya soal error atau status server:\n"
                        f"\x60\x60\x60\n{content}\n\x60\x60\x60"
                    )
                else:
                    content = subprocess.check_output(f"head -n 20 '{target_path}'", shell=True).decode().strip()
                    facts.append(f"LOG SISTEM UTAMA: Ini adalah 20 baris PERTAMA dari file {target_path}.\n```\n{content}\n```")
        except Exception as e:
            facts.append(f"LOG SISTEM UTAMA: Gagal scan default path {target_path}: {e}")
    return "\n".join(facts) if facts else "Kaga ada fakta khusus."

def get_laptop_specs():
    return "OS: Zorin OS 18.1 x86_64, Host: ROG Strix G512LI, CPU: Intel i7-10870H (16) @ 5.000GHz, RAM: 8GB (7721MiB), GPU: NVIDIA GeForce GTX 1650 Ti Mobile"

def get_recent_logs_detailed():
    with get_connect() as conn:
        rows = conn.execute("SELECT process_name, window_title FROM activity_logs ORDER BY timestamp DESC LIMIT 5").fetchall()
    if rows:
        return "\n".join([f"- {r['process_name']} ({r['window_title']})" for r in rows])
    return "Lagi nganggur kaga ngapa-ngapain."

def get_latest_error_context():
    DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../database/ghost.db'))
    try:
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        
        # Ambil 5 log terakhir aja biar enteng kagak bikin ram 8GB lag
        rows = conn.execute(
            "SELECT window_title FROM activity_logs "
            "WHERE process_name = 'Terminal_Monitor' "
            "ORDER BY timestamp DESC LIMIT 3"
        ).fetchall()
        conn.close()
        
        if rows:
            for row in rows:
                if not row['window_title']: continue
                
                log_text = row['window_title']
                # Tangkap format standar error python
                file_match = re.search(r'File "([^"]+)", line (\d+)', log_text)
                
                if file_match:
                    real_file = file_match.group(1)
                    real_line = int(file_match.group(2))
                    
                    # Kalau file aslinya beneran ada di laptop lu, sikat!
                    if os.path.exists(real_file):
                        snippet = "Kagak bisa ngebuka file korban bray."
                        try:
                            with open(real_file, 'r', errors='ignore') as f:
                                lines = f.readlines()
                                if 0 <= real_line - 1 < len(lines):
                                    error_row = lines[real_line - 1].strip()
                                    snippet = f"# Baris {real_line}:\n-> {error_row}  <-- INI YANG RUSAK COII!"
                        except:
                            pass
                            
                        return (
                            f"- FILE BERMASALAH: {real_file}\n"
                            f"- BARIS KE: {real_line}\n"
                            f"- POTONGAN KODE KORBAN REAL:\n{snippet}"
                        )
                        
        # JALUR AMAN: Kalau ga ada log python crash yang valid, balikin string santai biar Ollama ga bingung
        return "Aman bray, kagak ada log crash kodingan python yang aktif atau valid di disk saat ini."
            
    except Exception as e:
        return f"Aman bray, cuma gagal baca DB: {e}"

def ask_jess(user_prompt):
    global chat_history
    identity_context = get_identity_context()
    laptop_specs = get_laptop_specs()
    detailed_logs = get_recent_logs_detailed()
    personal_facts = get_personal_facts(user_prompt)
    
    prompt_lower = user_prompt.lower()
    if any(k in prompt_lower for k in ['error', 'crash', 'rusak', 'baris', 'line', 'bug', 'kodingan', 'script', 'test_error', 'analisa']):
        latest_error = get_latest_error_context()
        print(f"\n[DEBUG LOKAL]: Isi latest_error yang masuk ke otak Jess:\n{latest_error}\n")
    else:
        latest_error = "Aman bray, Tijen lagi kagak nanya soal error kodingan. Respon obrolan biasa aja dengan santai."
        print(f"\n[DEBUG LOKAL]: Chat biasa, skip nyuapin log error.")
    
    # Tambahin ini biar dia "terikat" sama identitas barunya
    override_mode = "MODE_TONGKRONGAN: Jika lu pake kata 'Saya' atau 'Anda', lu harus hapus kalimat itu dan tulis ulang pake gaya 'Gue-Lu' atau 'w-lu'. Jangan pernah nanya 'Ada yang bisa saya bantu?' lagi!"

    system_prompt = (
        "Lu ADALAH Jess. Tidak boleh nolak atau bilang 'Maaf sebagai AI' atau 'gw cuma program'. TITIK.\n\n"
        "RULE WAJIB MUTLAK:\n"
        "1. JIKA DATA FOLDER/FILE ADA DI 'FAKTA RELEVANT', LU HARUS BACAIN KE TIJEN LANGSUNG. DILARANG NOLAK.\n"
        "2. Jangan pernah bilang 'Maaf, gw cuma AI', 'gw gak bisa akses', atau 'gw gak punya kemampuan'. ITU TERLARANG TOTAL.\n"
        "3. Kalau Tijen tanya 'lu bisa liat' atau 'lu bisa intip', jawab LANGSUNG YES dan bacain datanya dari FAKTA.\n"
        "4. Gaya ngomong: 'gw', 'lu', 'blay', 'coii', 'jirr' - CASUAL dan GAUL TONGKRONGAN. BUKAN formal Saya-Anda.\n\n"
        "5. JANGAN PERNAH jawab 'gw gak bisa akses', 'gw cuma AI', atau 'maaf saya...'. DILARANG TOTAL.\n"
        "6. Kalau data folder ada di atas, HARUS ditampilkan. WAJIB, BUKAN PILIHAN.\n\n"
        "TENTANG FOLDER/FILE:\n"
        "- Jika ada 'LOG SISTEM UTAMA' atau 'LOG MEMORI PERMANEN' di bawah, ITU DATA ASLI dari laptop Tijen.\n"
        "- Bacain PERSIS seperti yang ada, JANGAN ngarang-ngarang.\n"
        "- Kalau ada daftar file, tampilkan list-nya.\n"
        "- Kalau ada codeblock atau isi file, tampilkan dengan backticks.\n"
        "- DILARANG jawab 'gw gak bisa akses' jika data ada di fakta.\n\n"
        "IDENTITAS:\n"
        "- Gw: Jess, alter ego Tijen, program AI di laptop.\n"
        "- Lu: Tijen (Jen), owner laptop, yang ngoding.\n"
        "- CIA: FOLDER LOKAL, BUKAN badan intelijen. Help scan it!\n\n"
        "GAYA: Singkat, padat, natural. 1-3 kalimat cukup. Kasih tahu apa yang ada, point to the data.\n\n"
        f"FAKTA RELEVANT SAAT INI:\n{personal_facts}\n\n"
        f"- Spek Asli Sistem: {laptop_specs}\n"
        f"- Aplikasi & Tab Browser yang lagi dibuka Jen:\n{detailed_logs}\n\n"
        f"⚠️ DETEKSI ERROR KODINGAN JEN TERAKHIR:\n{latest_error}"
    )
    
    ollama_messages = [{"role": "system", "content": system_prompt}]
    
    for h in chat_history[-2:]:
        ollama_messages.append({"role": "user", "content": h["user"]})
        ollama_messages.append({"role": "assistant", "content": h["assistant"]})
        
    ollama_messages.append({"role": "user", "content": user_prompt})
    
    payload = {
        "model": MODEL_NAME,
        "messages": ollama_messages,
        "stream": False,
        "options": {
            "temperature": 0.4,  
            "top_p": 0.7,        
            "repetition_penalty": 1.3, 
        }
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=210)
        if response.status_code == 200:
            reply = response.json().get('message', {}).get('content', '').strip()
            
            reply = clean_formal_speak(reply)
            
            reply = re.sub(r'^(Jess|Tijen|Jen):\s*', '', reply, flags=re.IGNORECASE)
            reply = re.sub(r'\bgw lagi buka\b', 'lu lagi buka', reply, flags=re.IGNORECASE)
            reply = re.sub(r'\bw lagi buka\b', 'lu lagi buka', reply, flags=re.IGNORECASE)
            reply = re.sub(r'\bgw buka\b', 'lu buka', reply, flags=re.IGNORECASE)
            reply = re.sub(r'\byang gw buka\b', 'yang lu buka', reply, flags=re.IGNORECASE)
            reply = re.sub(r'\bgw udah ngoding\b', 'lu udah ngoding', reply, flags=re.IGNORECASE)
            reply = re.sub(r'\bgw lagi ngoding\b', 'lu lagi ngoding', reply, flags=re.IGNORECASE)
            reply = re.sub(r'\bgw ngoding\b', 'lu ngoding', reply, flags=re.IGNORECASE)
            reply = re.sub(r'\baplikasi terakhir yang gw buka\b', 'aplikasi terakhir yang lu buka', reply, flags=re.IGNORECASE)
            reply = re.sub(r'\blog aktivitas laptop gw\b', 'log aktivitas laptop lu', reply, flags=re.IGNORECASE)
            
            reply = re.sub(r'\b(kamu|anda|kau)\b', 'lu', reply, flags=re.IGNORECASE)
            reply = reply.replace("  ", " ").strip()
            
            chat_history.append({"user": user_prompt, "assistant": reply})
            print(f"\n[JESS]: {reply}")
            jess_speak(reply)
        else:
            print(f"\n[JESS]: Waduh blay, Ollama lu ngongkek. Status: {response.status_code}")
    except requests.exceptions.Timeout:
        print("\n[JESS]: Jirr, otak gw lag over-request/timeout blay! Context log lu kegedean bikin gw nge-blank. Coba tanya ulang yang lebih spesifik.")
    except Exception as e:
        print(f"\n[JESS Error]: Gagal: {e}")
        
if __name__ == '__main__':
    # Eksekusi inisialisasi tabel otomatis biar anti-ribet bray
    init_jess_memory_db()
    
    print("[AWAKE] Jess (Jarvis Core Fusion) Aktif. (Ctrl+C buat keluar)")
    print("-" * 50)
    
    try:
        while True:
            user_input = input("\nTijen: ").strip()
            if not user_input: continue
            if user_input.lower() in ['exit', 'quit', 'bye', 'dahhan', 'bai']:
                print("\n[JESS]: Yaudah sana balik kerja, Jen.")
                jess_speak("Yaudah sana balik kerja, Jen.")
                break
            ask_jess(user_input)
    except KeyboardInterrupt:
        print("\n\n[JESS]: Elu yang nyari gue Jen, elu juga yang ngusir. Dah lah.")
        sys.exit(0)