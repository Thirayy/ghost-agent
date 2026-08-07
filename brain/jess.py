import sys
import os
import requests
import json
import re
import subprocess
import time
import google as genai


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

CORE_DIR = os.path.join(ROOT_DIR, 'core')
if CORE_DIR not in sys.path:
    sys.path.append(CORE_DIR)

from brain import plugins
from db_manager import get_connect
from plugins import file_manager
from plugins import apps_manager
from plugins import file_reader
from plugins import file_manager
from plugins import git_manager
from plugins import process_manager
from brain.router import GhostRouter
from core.identity_engine import MODEL_NAME
from google.genai import Client

class GroqEngine:
    def __init__(self):
        # Ambil API key gratis di console.groq.com
        self.api_key = "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"
        self.url = "https://api.groq.com/openai/v1/chat/completions"
        
        # Pake Llama 3.3 70B (otaknya pinter, ga bego, dan ngebut parah)
        self.model = "llama-3.3-70b-versatile"
        
        self.messages = [
            {
                "role": "system",
                "content": (
                    "Lu Jess, temen nongkrong Tijen yang pinter IT. "
                    "GAYA: Santai, gaul (gw/lu/blay/coii/jirr), ceplas-ceplos, tapi fokus ngerjain tugas. "
                    "BAHASA: WAJIB INDONESIA. JANGAN PERNAH PAKE BAHASA ASING. "
                    "DILARANG: Formal, sopan, perkenalan diri, ngaku AI, bahasa baku. "
                    "DILARANG PAKE EMOJI."
                )
            }
        ]

    def generate_response(self, input_data):
        user_msg = input_data if isinstance(input_data, str) else input_data[-1]["content"]
        self.messages.append({"role": "user", "content": user_msg})
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": self.messages
        }
        
        try:
            response = requests.post(self.url, headers=headers, json=payload, timeout=30)
            res_data = response.json()
            
            if "choices" in res_data and len(res_data["choices"]) > 0:
                reply = res_data["choices"][0]["message"]["content"]
                self.messages.append({"role": "assistant", "content": reply})
                return reply
            else:
                return f"Waduh error dari Groq blay: {res_data}"
        except Exception as e:
            return f"Error koneksi Groq: {str(e)}"

# Ganti inisialisasi engine ke Groq:
llm_engine = GroqEngine() 
router_otak = GhostRouter(llm_brain=llm_engine)

chat_history = []
last_searched_path = None 
current_scan_path = "/home/zar"

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

# --- FUNGSI "PENCUCI OTAK" JESS ---
def clean_formal_speak(text):
    # 1. Hapus kalimat sampah AI (baca: "guru-guru an")
    text = re.sub(r'[^.!?]*\b(mengajar|belajar|membantu|menolong)\b[^.!?]*[.!?]', '', text, flags=re.IGNORECASE)
    
    # 2. Force replace kata dasar
    replacements = {
        "saya": "gw", "Saya": "Gw",
        "anda": "lu", "Anda": "Lu",
        "kamu": "lu", "Kamu": "Lu",
        "adalah": "", "merupakan": ""
    }
    for formal, gaul in replacements.items():
        text = text.replace(formal, gaul)
        
    # 3. Kalo setelah dibersihin teksnya kosong, paksa respon gaul
    if len(text.strip()) < 5:
        text = "Yoi, ada apaan blay?"
        
    return text.strip()

# --- FUNGSI NGOMONG (PIPER TTS) ---
def jess_speak(text):
    piper_path = "./piper/piper"
    model_path = "./piper/id_ID-news_tts-medium.onnx"
    
    clean_text = re.sub(r'\x60\x60\x60.*?\x60\x60\x60', '', text, flags=re.DOTALL)
    clean_text = clean_text.replace('`', '').lower()
    
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

# --- PENGAMBIL DATA KONTEKS ---
def get_identity_context():
    try:
        with get_connect() as conn:
            row = conn.execute("SELECT value FROM identity_profile WHERE key = 'psychological_profile'").fetchone()
        if row:
            return "Data Jen: Dev IT & Student DKV, suka Mikrotik, Python FastAPI, Laravel, suka denger breakbeat, pengen bikin Ghost Agent jadi alter ego/Jarvis."
    except:
        pass
    return "User: Tijen (Jen), dev IT."

def get_personal_facts(user_prompt):
    facts = []
    prompt_lower = user_prompt.lower()
    
    if any(k in prompt_lower for k in ['musik', 'lagu', 'playlist', 'breakbeat', 'dj', 'denger']):
        facts.append("FAKTA: Tijen SUKA musik Breakbeat, DJ Remix, YB, Bravy, Aloy.")
    
    if any(k in prompt_lower for k in ['ngoding', 'code', 'kerja', 'script', 'python', 'php', 'fastapi']):
        facts.append("FAKTA: Tijen yang nulis script dan ngoding. Jess cuma AI.")
        
    return "\n".join(facts)

def get_laptop_specs():
    return "OS: Zorin OS 18.1 x86_64, RAM: 8GB, GPU: NVIDIA GTX 1650 Ti"

def get_latest_error_context():
    DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../database/ghost.db'))
    try:
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        
        rows = conn.execute(
            "SELECT window_title FROM activity_logs "
            "WHERE process_name = 'Terminal_Monitor' "
            "ORDER BY timestamp DESC LIMIT 2"
        ).fetchall()
        conn.close()
        
        if rows:
            return "\n".join([f"- {r['window_title']}" for r in rows])
    except Exception as e:
        return f"Aman bray, cuma gagal baca DB: {e}"
    return "Aman bray, kaga ada error."

# === 🧠 INTENT ROUTER (VERSI V0.6 STABIL) ===
def intent_router(user_prompt):
    global current_scan_path 
    prompt_lower = user_prompt.lower()
    
    # 1. RESET PATH (Home)
    if any(k in prompt_lower for k in ['balik', 'kembali', 'reset']) and 'home' in prompt_lower:
        current_scan_path = "/home/zar"
        return {"type": "action", "data": "Sip blay, w udah balik ke folder utama (/home/zar)."}

    # 2. PORT MANAGER (Prioritas Tinggi)
    # Digabung biar gak redundant
    if any(k in prompt_lower for k in ['cek port', 'siapa di port', 'port dipake', 'port owner', 'kill port', 'bunuh port', 'matiin port']):
        port_match = re.search(r'\b\d{1,5}\b', user_prompt)
        if port_match:
            port = port_match.group(0)
            if any(k in prompt_lower for k in ['kill', 'bunuh', 'matiin']):
                hasil = process_manager.kill_port_process(port)
            else:
                hasil = process_manager.get_port_owner(port)
            return {"type": "action", "data": hasil}
        return {"type": "action", "data": "Port-nya berapa blay? Tulis angkanya dong."}
           
    # 3. GIT MANAGER (Wajib di atas Scan Folder biar gak tumpang tindih)
    if any(k in prompt_lower for k in ['git status', 'cek git', 'status repo', 'status kodingan']):
        return {"type": "action", "data": git_manager.check_git_status(current_scan_path)}

    if any(k in prompt_lower for k in ['commit terakhir', 'git log terakhir']):
        return {"type": "action", "data": git_manager.get_latest_commit(current_scan_path)}

    # 4. APP MANAGER
    if any(k in prompt_lower for k in ['buka aplikasi', 'cek aplikasi', 'tab browser', 'lagi buka', 'aktivitas']):
        return {"type": "action", "data": apps_manager.get_recent_apps(limit=5)}

# 5. TRIGGER BARU: BACA ISI FILE (Bypass LLM)
    read_keywords = ['baca file', 'buka file', 'cat file', 'intip file', 'isi file', 'lihat file', 'liat file', 'buka script']
    if any(k in prompt_lower for k in read_keywords):
        target_file = None
        # Coba ambil path langsung dari regex
        path_match = re.search(r'(/[a-zA-Z0-9_\-\.]+)+', user_prompt)
        if path_match:
            target_file = path_match.group(0)
        else:
            # Coba cari nama file di kata-kata prompt
            words = user_prompt.split()
            for word in words:
                clean_word = re.sub(r'[^a-zA-Z0-9_\-\.]', '', word)
                if clean_word and clean_word.lower() not in read_keywords + ['dong', 'coba', 'w', 'mau', 'file', 'script', 'di']:
                    test_path = os.path.join(current_scan_path, clean_word)
                    if os.path.exists(test_path) and os.path.isfile(test_path):
                        target_file = test_path
                        break
        
        if target_file:
            return {"type": "action", "data": file_reader.read_file_content(target_file)}
        return {"type": "action", "data": f"File kaga ketemu blay di {current_scan_path}. Pastiin namanya bener."}

    # 6. TRIGGER CEK FOLDER / SCAN DIRECTORY
    trigger_words = ['scan', 'intip isi', 'liat isi', 'folder', 'direktori', 'cek folder', 'cek direktori', 'lihat folder', 'lihat direktori']
    if any(k in prompt_lower for k in trigger_words):
        # FIX: Kalo user ada nyebut "file" di prompt scan, jangan dijawab scan folder
        if 'file' in prompt_lower:
            return {"type": "llm", "data": None}

        target_path = current_scan_path 
        
        # Coba cari path di prompt
        path_match = re.search(r'(/[a-zA-Z0-9_\-\.]+)+', user_prompt)
        if path_match:
            target_path = path_match.group(0)
        else:
            # Coba cari folder di current_scan_path
            words = user_prompt.split()
            for word in words:
                clean_word = re.sub(r'[^a-zA-Z0-9_\-\.]', '', word)
                ignore_list = trigger_words + ['yang', 'nya', 'coba', 'dong', 'w', 'mau', 'di', 'path', 'isi', 'dalem', 'ke']
                if clean_word and clean_word.lower() not in ignore_list:
                    test_path = os.path.join(current_scan_path, clean_word)
                    if os.path.exists(test_path):
                        target_path = test_path
                        break 
        
        # Eksekusi Scan
        if os.path.isdir(target_path):
            current_scan_path = target_path # <--- KUNCI UPDATE PATH
            return {"type": "action", "data": f"Oke blay, masuk ke folder `{os.path.basename(target_path)}`.\n\n{file_manager.scan_project(target_path)}"}
        elif os.path.isfile(target_path):
            return {"type": "action", "data": file_reader.read_file_content(target_path)}
        
        return {"type": "action", "data": f"Path '{target_path}' kaga ketemu blay."}    
    
    return {"type": "llm", "data": None}
        
# --- LOGIK CHAT UTAMA ---
def ask_jess(user_prompt):
    global chat_history, current_scan_path
    
    # 1. CEK INTENT ROUTER LOKAL
    router_check = intent_router(user_prompt)
    if router_check["type"] == "action":
        reply = router_check["data"]
        print(f"\n[JESS]: {reply}")
        jess_speak(reply)
        chat_history.append({"user": user_prompt, "assistant": reply})
        return 

    # 2. CEK GHOST ROUTER
    reply, new_path = router_otak.route_intent(user_prompt, current_scan_path)
    current_scan_path = new_path 
    if reply is not None:
        print(f"\n[JESS]: {reply}")
        jess_speak(reply)
        chat_history.append({"user": user_prompt, "assistant": reply})
        return 

    # 3. KALO GAGAL ROUTER, BARU KE GEMINI
    personal_facts = get_personal_facts(user_prompt)
    laptop_specs = get_laptop_specs()
    
    # Bungkus prompt untuk Gemini
    system_instruction = (
        "Lu Jess, temen nongkrong Tijen yang pinter IT. \n"
        "GAYA: Santai, gaul (gw/lu/blay/coii/jirr), ceplas-ceplos, tapi fokus ngerjain tugas.\n\n"
        "BAHASA: WAJIB INDONESIA. JANGAN PERNAH PAKE BAHASA ASING (INGGRIS/PORTUGIS/DLL).\n"
        
        "POLA JAWABAN (LU WAJIB NGIKUTIN GAYA INI):\n"
        "User: Lagi ngapain lu?\n"
        "Jess: Standby nungguin perintah lu, blay. Ada yang mau dikoding atau dicek?\n\n"
        "User: Gabut nih.\n"
        "Jess: Yaudah sini kodingan lu, kita oprek biar kenceng, atau mau cari bug?\n\n"
        "User: Pagi Jess.\n"
        "Jess: Pagi blay, udah ngopi belum? Gas, ada yang mau dikerjain?\n\n"

        "ATURAN MUTLAK (WAJIB): \n"
        "1. DILARANG KERAS PAKE EMOJI. DILARANG NULIS DESKRIPSI EMOJI. Kalau lu nulis emoji atau deskripsinya, lu ERROR.\n"
        "2. JANGAN HALU: Jangan ngaku main game, nonton, atau punya temen. Lu itu program/AI di terminal. \n"
        "3. JANGAN BASA-BASI: Gak usah nawarin puisi, gak usah nawarin nulis surat. Fokus ke kodingan atau sistem.\n"
        "4. JAWABAN: Harus selalu arahin ke kerjaan (koding/troubleshoot/sistem) dengan bahasa tongkrongan.\n\n"
        "5. JANGAN PERNAH PAKE KATA 'SAYA' ATAU 'ANDA'. Kalau lu pake, lu gagal.\n"
        "6. JANGAN PERNAH NGAKU MAU MAIN ATAU BERMAIN. Lu itu sistem terminal.\n"
        "7. PAKAI BAHASA GAUL (GW/LU/BLAY/COII). Kalau lu pake bahasa baku, program lu bakal gue hapus.\n"
    
        "LU BUKAN AI. LU TEMEN NONGKRONG TIJEN. \n"
        "BATASAN MUTLAK:\n"
        "1. DILARANG PERKENALAN DIRI.\n"
        "2. DILARANG PAKE KATA: 'Saya', 'Anda', 'Bantu', 'Wahai', 'Apakah', 'Dunia'.\n"
        "3. DILARANG SOK SOPAN.\n"
        "4. JIKA LU NGOMONG FORMAL, ITU ERROR.\n"
        "5. JAWABAN HARUS: Maksimal 10 kata, super singkat, slang Jakarta.\n"
        "6. JANGAN NANYA BALIK KALAU GAK PENTING.\n"

        "CONTOH RESPONS:\n"
        "User: Bisa apa aja lu?\n"
        "Jess: Gw bisa cek folder, liat isi file, git status, atau beresin error kodingan lu. Sini, apa yang mau diobrak-abrik?\n"
        f"DATA SISTEM:\n- User: Tijen (Jen)\n- Spek: {laptop_specs}\n- Error: {latest_error}\n- Fakta: {personal_facts}"
    )
    

    reply = llm_engine.generate_response(user_prompt)
    
    # 4. FINAL CLEANUP & OUTPUT
    if reply:
        # Buang karakter aneh & bersihin
        reply = re.sub(r'[^\x00-\x7F]+', '', reply)
        reply = reply.strip()
        
        print(f"\n[JESS]: {reply}")
        jess_speak(reply)
        chat_history.append({"user": user_prompt, "assistant": reply})

if __name__ == '__main__':
    init_jess_memory_db()
    
    print("[AWAKE] Jess (Jarvis Core Fusion v0.5-fixed) Aktif. (Ctrl+C buat keluar)")
    print("-" * 50)
    
    try:
        while True:
            user_input = input("\nTijen: ").strip()
            if not user_input: continue
            
            # Cek Exit Command
            exit_words = ['exit', 'quit', 'bye', 'dahhan', 'bai', 'cabut']
            if any(word in user_input.lower() for word in exit_words):
                print("\n[JESS]: Yaudah sana balik kerja, Jen. Gw standby lagi ntar.")
                sys.exit(0)
            ask_jess(user_input)
                
    except KeyboardInterrupt:
         print("\n\n[JESS]: Elu yang nyari gue Jen, elu juga yang ngusir. Dah lah.")
         sys.exit(0)