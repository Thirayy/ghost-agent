import time
from db_manager import get_connect, init_db
from tracker import get_active_window

INTERVAL = 5  

def start_agent():
    init_db()
    print("[GHOST CORE V3] Observer Aktif. Menjaga struktur data premium...")
    
    last_user, last_proc, last_title, last_cat, last_top, last_imp = None, None, None, None, None, None
    current_duration = 0
    
    try:
        while True:
            username, process_name, window_title, category, topic, importance = get_active_window()
            
            if process_name == last_proc and window_title == last_title:
                current_duration += INTERVAL
            else:
                if last_proc and current_duration > 0:
                    with get_connect() as conn:
                        conn.execute('''
                            INSERT INTO activity_logs (username, process_name, window_title, category, topic, importance, duration)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (last_user, last_proc, last_title, last_cat, last_top, last_imp, current_duration))
                        conn.commit()
                
                last_user, last_proc, last_title, last_cat, last_top, last_imp = username, process_name, window_title, category, topic, importance
                current_duration = INTERVAL
                
            time.sleep(INTERVAL)
            
    except KeyboardInterrupt:
        if last_proc and current_duration > 0:
            with get_connect() as conn:
                conn.execute('''
                    INSERT INTO activity_logs (username, process_name, window_title, category, topic, importance, duration)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (last_user, last_proc, last_title, last_cat, last_top, last_imp, current_duration))
                conn.commit()
        print("\n[GHOST CORE V3] Service dihentikan safely.")

if __name__ == '__main__':
    start_agent()
