import subprocess
import os
import psutil
import re

def extract_topic_and_importance(process_name, window_title):
    """Mengekstrak topik spesifik dan bobot kepentingan (Importance Score) harian"""
    proc = process_name.lower()
    title = window_title.lower()
    
    # Default values
    topic = "general"
    importance = 3
    
    # 1. SPECIAL TRACKING: GHOST AGENT & RAY OS (Top Priority)
    if any(x in title for x in ["ghost", "agent", "jess"]):
        return "ghost-agent-dev", 9
    if any(x in title for x in ["ray", "ray os", "ray-os"]):
        return "ray-os-dev", 9

    # 2. NETWORKING & MIKROTIK (Winbox Window Title Parsing)
    if "winbox" in proc or "winbox" in title:
        importance = 8
        if "firewall" in title: return "mikrotik-firewall-config", importance
        if "interface" in title: return "mikrotik-interface-setting", importance
        if "route" in title: return "mikrotik-routing-management", importance
        if "ip" in title: return "mikrotik-ip-addressing", importance
        if "system" in title: return "mikrotik-system-maintenance", importance
        return "mikrotik-network-engineering", importance

    # 3. LINUX, TERMINAL, NETWORKING INFRASTRUCTURE (SSH / Scripting)
    if "terminal" in proc or "konsole" in proc:
        importance = 7
        if any(x in title for x in ["nano", "micro", "vim", "neovim"]): return "linux-terminal-editing", importance
        if "ssh" in title or "@" in title: return "remote-server-ssh", importance
        if "git" in title: return "git-version-control", importance
        if any(x in title for x in ["apt", "pacman", "systemctl"]): return "linux-sysadmin-task", importance
        return "terminal-commands", importance

    # 4. DATABASE MANAGEMENT
    if any(x in title for x in ["sqlite", "postgres", "mysql", "pgadmin", "dbgate"]):
        return "database-management", 8

    # 5. CODING & TEXT EDITORS
    if any(x in proc for x in ["code", "cursor", "sublime", "text-editor"]):
        importance = 8
        if ".py" in title: return "python-programming", importance
        if ".php" in title or "laravel" in title: return "laravel-php-programming", importance
        return "software-development", importance

    # 6. AI RESEARCH & DOCUMENTATION
    if "brave" in proc or "chrome" in proc:
        if any(x in title for x in ["gemini", "chatgpt", "ollama", "ai"]): 
            return "ai-research", 7
        if any(x in title for x in ["github", "stackoverflow", "docs"]): 
            return "developer-documentation", 6
        if any(x in title for x in ["instagram", "tiktok", "facebook"]): 
            return "social-media", 1
        if any(x in title for x in ["whatsapp", "discord", "telegram"]): 
            return "communication", 2
        return "web-browsing", 3
        
    return topic, importance

def normalize_activity(process_name, window_title):
    proc = process_name.lower()
    title = window_title.lower()
    
    if "brave" in proc or "chrome" in proc or "firefox" in proc:
        if any(x in title for x in ["instagram", "facebook", "tiktok"]): return "social-media"
        if any(x in title for x in ["whatsapp", "discord", "telegram"]): return "communication"
        if any(x in title for x in ["gemini", "chatgpt", "github"]): return "research"
        return "browsing"
    if "code" in proc or "cursor" in proc: return "coding"
    if "winbox" in proc: return "network-configuring"
    if "terminal" in proc or "konsole" in proc: return "terminal-activity"
    return "idle" if "gnome-shell" in proc else "other"

def get_active_window():
    try:
        username = os.getlogin()
        window_id = subprocess.check_output(["xdotool", "getwindowfocus"]).decode("utf-8").strip()
        if not window_id:
            return username, "idle", "Idle", "idle", "none", 0
            
        window_title = subprocess.check_output(["xdotool", "getwindowname", window_id]).decode("utf-8").strip()
        pid_out = subprocess.check_output(["xdotool", "getwindowpid", window_id]).decode("utf-8").strip()
        
        process_name = psutil.Process(int(pid_out)).name() if pid_out else "unknown"
        category = normalize_activity(process_name, window_title)
        
        # Ekstrak Topic dan Importance yang sudah ditajemin
        topic, importance = extract_topic_and_importance(process_name, window_title)
        
        return username, process_name, window_title, category, topic, importance
        
    except Exception:
        return os.getlogin(), "idle", "Idle", "idle", "none", 0
