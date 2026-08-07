import subprocess
import os
import re
from brain.plugins.base_plugin import BasePlugin

class TerminalPlugin(BasePlugin):
    def metadata(self):
        return {
            "name": "Dynamic Backend Executor",
            "description": "Nge-run semua jenis backend secara otomatis.",
            "version": "2.0"
        }

    def can_handle(self, user_prompt):
        prompt_lower = user_prompt.lower()
        trigger_words = ['jalanin backend', 'run backend', 'docker ps', 'matiin backend', 'stop backend']
        return any(word in prompt_lower for word in trigger_words)

    def execute(self, user_prompt, current_path):
        prompt_lower = user_prompt.lower()
        
        # 1. Ekstrak target path
        folder_target = None
        match = re.search(r'(?:backend|folder)\s+([a-zA-Z0-9_-]+)', prompt_lower)
        if match and match.group(1) not in ['di', 'run', 'jalanin']:
            folder_target = match.group(1)

        target_path = current_path
        if folder_target:
            for f in os.listdir("/home/zar"):
                if f.lower() == folder_target.lower():
                    target_path = os.path.join("/home/zar", f)
                    break
        
        if 'matiin backend' in prompt_lower or 'stop backend' in prompt_lower:
            subprocess.run(["pkill", "-f", "uvicorn"])
            subprocess.run(["pkill", "-f", "main.py"])
            subprocess.run(["pkill", "-f", "artisan"])
            subprocess.run(["pkill", "-f", "npm"])
            
            return "Backend udah w matiin blay. Aman!", current_path
        
        if not os.path.exists(target_path):
            return f"Folder `{target_path}` kaga ketemu blay.", current_path

        # 2. Fitur Docker
        if 'docker ps' in prompt_lower:
            try:
                res = subprocess.check_output(["docker", "ps", "--format", "table {{.Names}}\t{{.Status}}"], text=True)
                return f"Ini status container lu blay:\n```text\n{res}```", current_path
            except Exception as e:
                return f"Gagal nge-cek docker: {e}", current_path

        # 3. Fitur Backend
        if 'jalanin backend' in prompt_lower or 'run backend' in prompt_lower:
            log_path = os.path.join(target_path, "backend_ghost.log")
            log_file = open(log_path, "a")

            # Deteksi PHP
            if os.path.exists(os.path.join(target_path, "artisan")):
                subprocess.Popen(["php", "artisan", "serve"], cwd=target_path, stdout=log_file, stderr=log_file)
                return "Backend Laravel/PHP udah jalan blay.", target_path

            # Deteksi Node
            if os.path.exists(os.path.join(target_path, "package.json")):
                subprocess.Popen(["npm", "run", "dev"], cwd=target_path, stdout=log_file, stderr=log_file)
                return "Backend Node.js udah jalan blay.", target_path

            # Deteksi Python
            found_main = "main.py" if os.path.exists(os.path.join(target_path, "main.py")) else None
            if not found_main and os.path.exists(os.path.join(target_path, "app", "main.py")):
                found_main = "app/main.py"
            
            if found_main:
                cmd = ["uvicorn", "app.main:app", "--port", "8000"] if "app" in found_main else ["python3", found_main]
                subprocess.Popen(cmd, cwd=target_path, stdout=log_file, stderr=log_file)
                return f"Sip! Backend Python di `{os.path.basename(target_path)}` udah jalan.", target_path
            
            return f"Waduh blay, kaga ada file main.py/artisan/package.json di {target_path}.", target_path


        return None, current_path