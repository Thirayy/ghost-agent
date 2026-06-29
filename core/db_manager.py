import sqlite3
import os

# Ngunci path absolut biar aman dari mana aja
DB_PATH = os.path.expanduser('~/ghost-agent/database/ghost.db')

def get_connect():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_connect() as conn:
        cursor = conn.cursor()
        
        # 1. RAW LOGS (Pastikan kolom 'topic' & 'importance' ada di sini!)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                username TEXT,
                process_name TEXT,
                window_title TEXT,
                category TEXT,
                topic TEXT,          -- Kolom vital yang bikin error tadi
                importance INTEGER,  -- Kolom vital yang bikin error tadi
                duration INTEGER DEFAULT 0
            )
        ''')
        
        # 2. SESSION LAYER
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time DATETIME,
                end_time DATETIME,
                apps_used TEXT,
                dominant_topic TEXT,
                importance INTEGER
            )
        ''')
        
        # 3. MEMORY LAYER
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ghost_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                type TEXT,
                content TEXT,
                importance_score INTEGER
            )
        ''')
        
        # 4. IDENTITY LAYER
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS identity_profile (
                trait TEXT PRIMARY KEY,
                score REAL,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()

if __name__ == '__main__':
    init_db()
    print("[DB V3] FIXED: Seluruh layer arsitektur memori berhasil dibangun!")
