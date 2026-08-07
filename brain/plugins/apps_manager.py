import os
import sqlite3

def get_recent_apps(limit=5):
    """Narik data aplikasi & window judul terakhir yang dibuka Tijen dari DB"""
    # PATH YANG BENER DIMARI BRAY (Mundur 2 tingkat dari brain/plugins/ ke ghost-agent/)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    DB_PATH = os.path.join(base_dir, 'database/ghost.db')
    
    if not os.path.exists(DB_PATH):
        return f"Database log aktivitas kaga ketemu di {DB_PATH} blay, jalankan monitornya dulu."
        
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        
        # Ambil log aktivitas paling fresh
        rows = conn.execute(
            "SELECT process_name, window_title FROM activity_logs "
            "ORDER BY timestamp DESC LIMIT ?", (limit,)
        ).fetchall()
        conn.close()
        
        if rows:
            result = "Ini aplikasi sama tab yang lagi lu buka sekarang blay:\n"
            result += "\n".join([f"- {r['process_name']} ({r['window_title']})" for r in rows])
            return result
        else:
            return "Log di DB masih kosong blay, lu lagi kagak buka aplikasi apa-apa?"
            
    except Exception as e:
        return f"Gagal narik data aplikasi dari DB: {e}"