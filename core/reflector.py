import sys
import os
import requests
from datetime import datetime
from db_manager import get_connect

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:3b"

def generate_reflection():
    """Menarik data sessions, merangkumnya lewat Ollama, lalu menyimpan ke ghost_memory"""
    print("[REFLECTION] Mengumpulkan data sesi untuk refleksi harian...")
    
    with get_connect() as conn:
        # Ambil semua data sesi yang belum di-reflect
        sessions = conn.execute("SELECT * FROM sessions ORDER BY start_time ASC").fetchall()
        
        if not sessions:
            print("[REFLECTION] Gak ada data sesi baru yang bisa direfleksikan.")
            return

        # Rakit data sesi jadi teks mentah buat dibaca Ollama
        context_lines = []
        highest_importance = 0
        all_topics = set()
        
        for s in sessions:
            context_lines.append(
                f"- Sesi [{s['start_time']} s/d {s['end_time']}]: Apps ({s['apps_used']}) | Topik: {s['dominant_topic']} | Importance: {s['importance']}/10"
            )
            all_topics.add(s['dominant_topic'])
            if s['importance'] > highest_importance:
                highest_importance = s['importance']
        
        sessions_context = "\n".join(context_lines)
        
        # System prompt agar Ollama bertindak sebagai Reflection Engine
        system_prompt = (
            "Kamu adalah Reflection Engine untuk Ghost Agent bernama Jess. Tugasmu adalah menganalisis data sesi aktivitas harian user (Zar) "
            "dan mengubahnya menjadi satu paragraf ringkasan memori jangka panjang yang padat, dingin, faktual, dan mendalam.\n"
            "Tulis dalam Bahasa Indonesia, gunakan sudut pandang orang ketiga (User/Zar), fokus pada pencapaian, pola produktivitas, atau distrasi yang dominan."
        )
        
        user_prompt = f"Data Sesi Aktivitas Zar hari ini:\n{sessions_context}\n\nEkstrak menjadi satu paragraf memori jangka panjang!"
        
        payload = {
            "model": MODEL_NAME,
            "prompt": f"{system_prompt}\n\n{user_prompt}\nMemory:",
            "stream": False
        }
        
        try:
            response = requests.post(OLLAMA_URL, json=payload)
            if response.status_code == 200:
                memory_content = response.json()['response'].strip()
                
                # Simpan ke tabel ghost_memory
                conn.execute('''
                    INSERT INTO ghost_memory (type, content, importance_score)
                    VALUES (?, ?, ?)
                ''', ('daily', memory_content, highest_importance))
                
                # CLEAR SESSIONS: Hapus sesi yang sudah berhasil dirangkum jadi memori permanen
                conn.execute("DELETE FROM sessions")
                conn.commit()
                
                print("\n[REFLECTION SUCCESS] Memori baru berhasil dicatat:")
                print(f"-> {memory_content}")
                print(f"-> Importance Score Tertinggi: {highest_importance}/10")
                print("[REFLECTION] Tabel sessions telah dibersihkan untuk menjaga performa DB.")
            else:
                print(f"[REFLECTION Error] Ollama error dengan status: {response.status_code}")
        except Exception as e:
            print(f"[REFLECTION Error] Gagal terhubung ke Ollama: {e}")

if __name__ == '__main__':
    generate_reflection()
