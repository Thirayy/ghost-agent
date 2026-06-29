import sys
import os
import requests
import json
from db_manager import get_connect

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:3b"

def update_identity():
    print("[IDENTITY] Menganalisis memori jangka panjang untuk memperbarui profil Zar...")
    
    with get_connect() as conn:
        memories = conn.execute("SELECT content FROM ghost_memory ORDER BY created_at DESC LIMIT 10").fetchall()
        
        if not memories:
            print("[IDENTITY] Belum ada memori jangka panjang yang cukup untuk membentuk identitas.")
            return

        memory_context = "\n".join([f"- {m['content']}" for m in memories])
        
        system_prompt = (
            "Kamu adalah Identity Profiler Engine untuk Ghost Agent bernama Jess. Tugasmu adalah menganalisis "
            "rekaman memori jangka panjang aktivitas Zar dan mengekstraknya menjadi profil psikologis format JSON mentah.\n"
            "PENTING: Jangan gunakan kata umum seperti 'teknologi' atau 'fleksibel'. Gali secara SPESIFIK nama aplikasi "
            "(seperti Winbox, Brave, Terminal) atau topik (seperti Mikrotik, Python, Ghost Agent) dan sebutkan kelemahan distraksinya (seperti Instagram/medsos jika ada).\n\n"
            "Format JSON wajib mentah tanpa markdown block (HANYA JSON), dengan key berikut:\n"
            "{\n"
            "  \"core_interests\": [\"Topik spesifik 1 (misal: Mikrotik Network, Python Coding)\", \"Topik spesifik 2\"],\n"
            "  \"work_style\": \"Gaya kerja nyata (misal: Fokus oprek sistem, rentan distraksi Instagram, sering begadang)\",\n"
            "  \"psychological_trait\": \"Sifat dominan (misal: Ambisius tech-savvy, gampang bosan, soliter)\"\n"
            "}"
        )
        
        user_prompt = f"Data Memori Jangka Panjang Zar:\n{memory_context}\n\nEkstrak menjadi JSON profil sesuai instruksi!"
        
        payload = {
            "model": MODEL_NAME,
            "prompt": f"{system_prompt}\n\nZar Data:\n{user_prompt}\nJSON:",
            "stream": False,
            "format": "json"  # <--- INI KUNCINYA! Paksa Ollama mode JSON asli
        }
        
        try:
            response = requests.post(OLLAMA_URL, json=payload)
            if response.status_code == 200:
                raw_response = response.json()['response'].strip()
                
                # Coba parsing JSON langsung
                try:
                    parsed_json = json.loads(raw_response)
                except json.JSONDecodeError:
                    # Kalau Ollama beneran ngaco, bersihkan manual dari sisa markdown block
                    if "```" in raw_response:
                        raw_response = raw_response.split("```")[1]
                        if raw_response.startswith("json"):
                            raw_response = raw_response[4:]
                    raw_response = raw_response.strip()
                    parsed_json = json.loads(raw_response)
                
                # Simpan atau Update ke tabel identity_profile
                conn.execute("DELETE FROM identity_profile")
                conn.execute('''
                    INSERT INTO identity_profile (key, value, confidence_score)
                    VALUES (?, ?, ?)
                ''', ('psychological_profile', json.dumps(parsed_json), 0.90))
                conn.commit()
                
                print("\n[IDENTITY SUCCESS] Profil Psikologis Zar Berhasil Diperbarui:")
                print(json.dumps(parsed_json, indent=2))
            else:
                print(f"[IDENTITY Error] Ollama error: {response.status_code}")
        except Exception as e:
            print(f"[IDENTITY Error] Gagal memproses identitas: {e}")

            # PASTIKAN DUA BARIS INI ADA DI PALING BAWAH
if __name__ == '__main__':
    update_identity()