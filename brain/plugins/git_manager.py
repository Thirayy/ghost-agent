import subprocess
import os

def check_git_status(repo_path):
    """Ngecek status git secara lokal di folder saat ini"""
    if not os.path.exists(os.path.join(repo_path, '.git')):
        return f"Folder `{repo_path}` ini bukan repository Git bray."
        
    try:
        # Ambil branch aktif
        branch = subprocess.run("git branch --show-current", shell=True, cwd=repo_path, capture_output=True, text=True).stdout.strip()
        # Ambil status singkat
        status = subprocess.run("git status -s", shell=True, cwd=repo_path, capture_output=True, text=True).stdout.strip()
        
        res = f"📌 **Git Branch**: `{branch}`\n"
        if status:
            res += f"⚠️ **File Berubah**:\n```\n{status}\n```"
        else:
            res += "✅ Repo bersih bray, kaga ada uncommitted changes."
        return res
    except Exception as e:
        return f"Gagal eksekusi git status: {e}"

def get_latest_commit(repo_path):
    """Ngeliat log commit terakhir"""
    if not os.path.exists(os.path.join(repo_path, '.git')):
        return "Kaga ada folder .git di sini blay."
    try:
        commit = subprocess.run("git log -1 --oneline --decorate", shell=True, cwd=repo_path, capture_output=True, text=True).stdout.strip()
        return f"Log Commit Terakhir:\n`{commit}`"
    except Exception as e:
        return f"Gagal ngambil commit: {e}"