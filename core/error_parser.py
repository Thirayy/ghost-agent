import os
import re

def get_error_context_from_log(log_string):
    """
    Fungsi asli buat membedah string log dari Terminal_Monitor,
    nyari file fisiknya, terus ngambil potongan kode yang bikin crash.
    """
    try:
        # 1. Ekstrak nama file ama baris pake regex sakti
        match = re.search(r'File "([^"]+)", line (\d+)', log_string)
        if not match:
            return "Format log error kagak valid bray."
            
        file_path = match.group(1)
        line_num = int(match.group(2))
        
        # 2. Cek apakah filenya beneran ada di laptop lu
        if not os.path.exists(file_path):
            return f"Filenya kagak ketemu di path: {file_path}"
            
        # 3. Buka file fisiknya, ambil baris kodingan yang jahanam
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
        # Ambil baris target (index Python mulai dari 0, makanya -1)
        if 0 < line_num <= len(lines):
            target_line = lines[line_num - 1].strip()
            return {
                "file": file_path,
                "line": line_num,
                "snippet": target_line
            }
        else:
            return f"Baris ke-{line_num} kagak ada di file itu, ketinggian jirr."
            
    except Exception as e:
        return f"Gagal total pas nyoba bedah file kodingan: {e}"