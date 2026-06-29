from datetime import datetime, timedelta
from db_manager import get_connect

def compress_raw_logs_to_sessions():
    """Mengelompokkan log aktivitas mentah menjadi sesi-sesi padat"""
    print("[AGGREGATOR] Memproses log mentah menjadi sesi...")
    with get_connect() as conn:
        logs = conn.execute("SELECT * FROM activity_logs ORDER BY timestamp ASC").fetchall()
        if not logs:
            return

        session_start = logs[0]['timestamp']
        session_end = logs[0]['timestamp']
        apps = set([logs[0]['process_name']])
        topics = {}
        max_importance = logs[0]['importance']
        
        # Aturan: jika jeda log < 5 menit, dianggap satu sesi aktivitas
        for log in logs[1:]:
            t1 = datetime.strptime(log['timestamp'], "%Y-%m-%d %H:%M:%S")
            t2 = datetime.strptime(session_end, "%Y-%m-%d %H:%M:%S")
            
            if (t1 - t2).total_seconds() < 300: # 5 menit
                session_end = log['timestamp']
                apps.add(log['process_name'])
                topics[log['topic']] = topics.get(log['topic'], 0) + log['duration']
                if log['importance'] > max_importance:
                    max_importance = log['importance']
            else:
                # Simpan sesi yang selesai
                dom_topic = max(topics, key=topics.get) if topics else "general"
                conn.execute('''
                    INSERT INTO sessions (start_time, end_time, apps_used, dominant_topic, importance)
                    VALUES (?, ?, ?, ?, ?)
                ''', (session_start, session_end, ",".join(apps), dom_topic, max_importance))
                
                # Reset untuk sesi berikutnya
                session_start = log['timestamp']
                session_end = log['timestamp']
                apps = set([log['process_name']])
                topics = {log['topic']: log['duration']}
                max_importance = log['importance']
                
        # Simpan sisa sesi terakhir
        if topics:
            dom_topic = max(topics, key=topics.get)
            conn.execute('''
                INSERT INTO sessions (start_time, end_time, apps_used, dominant_topic, importance)
                VALUES (?, ?, ?, ?, ?)
            ''', (session_start, session_end, ",".join(apps), dom_topic, max_importance))
            
        # PROTEKSI DATABASE MELEDAK: Hapus log mentah yang sudah diekstrak
        conn.execute("DELETE FROM activity_logs WHERE timestamp <= ?", (session_end,))
        conn.commit()
    print("[AGGREGATOR] Selesai. Log mentah berhasil dibersihkan.")

if __name__ == '__main__':
    compress_raw_logs_to_sessions()
