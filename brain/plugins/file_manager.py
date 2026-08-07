import os
import subprocess

def scan_project(path):
    """Fungsi spesifik buat scan folder, bypass LLM biar kaga timeout"""
    if not os.path.exists(path):
        return f"Waduh blay, path {path} kagak ketemu di sistem lu."
    
    try:
        # Pake ls -p biar cepet, decode biar jadi string
        files = subprocess.check_output(f"ls -p '{path}'", shell=True).decode().strip().split("\n")
        
        if not files or files == [""]:
            return f"Folder {path} kosong melompong bray."
        
        result = f"Udah gw intip, ini isi folder {path}:\n"
        result += "\n".join([f"- {f}" for f in files if f])
        
        # Dibatasi 30 baris aja biar lu di terminal bacanya enak
        lines = result.split('\n')
        if len(lines) > 30:
            return "\n".join(lines[:30]) + f"\n\n... (ada {len(lines) - 30} file lagi, kepanjangan blay)."
            
        return result
    except Exception as e:
        return f"Gagal scan folder bray: {e}"