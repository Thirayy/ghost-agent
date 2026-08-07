import os

def read_file_content(file_path):
    """Fungsi khusus buat ngebaca isi file kodingan/teks Tijen (Aman buat file gede)"""
    if not os.path.exists(file_path):
        return f"Waduh blay, filenya kagak ada di: {file_path}"
        
    if os.path.isdir(file_path):
        return f"Itu folder blay ({file_path}), kalau mau liat isinya pake perintah scan."

    try:
        preview_lines = []
        total_lines = 0
        max_preview = 40  # Batas baris yang mau diintip

        # Pake pendekatan streaming (baca baris per baris, kaga langsung load semua ke RAM)
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                total_lines += 1
                if total_lines <= max_preview:
                    preview_lines.append(line)
                # Kalo file-nya gede banget (di atas 5000 baris), stop ngitung biar kaga lag loop-nya
                if total_lines > 5000:
                    break

        if total_lines == 0:
            return f"File `{os.path.basename(file_path)}` kosong melompong bray."

        content = "".join(preview_lines)
        result = f"Udah gw intip isi file `{os.path.basename(file_path)}`:\n\n```text\n{content}\n```"
        
        if total_lines > max_preview:
            if total_lines > 5000:
                result += f"\n\n... (dan ada ribuan baris lagi di bawah, kepanjangan blay, ogah w terusin)."
            else:
                result += f"\n\n... (ada {total_lines - max_preview} baris lagi di bawah, kepanjangan blay)."
            
        return result

    except Exception as e:
        return f"Gagal pas mau baca file bray: {e}"