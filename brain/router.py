import os
import sys
import importlib
import inspect

# Pastiin manggilnya pake gaya panjang absolut bray
from brain.plugins.base_plugin import BasePlugin

class GhostRouter:
    def __init__(self, llm_brain=None):
        self.plugins = []
        self.llm_brain = llm_brain
        self.load_plugins()

    def load_plugins(self):
        """Otomatis nge-load semua plugin dari folder brain/plugins"""
        plugins_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'plugins')
        
        # JANGAN append plugins_dir ke sys.path lagi biar ga bentrok path pendek bray!

        for file in os.listdir(plugins_dir):
            if file.endswith('.py') and file != '__init__.py' and file != 'base_plugin.py':
                module_name = file[:-3]
                try:
                    # Load pake full package path absolut
                    module = importlib.import_module(f"brain.plugins.{module_name}")
                    importlib.reload(module)
                    
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if issubclass(obj, BasePlugin) and obj != BasePlugin:
                            self.plugins.append(obj())
                except Exception as e:
                    print(f"[Router Error]: Gagal load plugin {module_name}: {e}")

    def route_intent(self, user_prompt, current_path):
        # 1. CEK SEMUA PLUGIN DULU
        for plugin in self.plugins:
            if plugin.can_handle(user_prompt):
                return plugin.execute(user_prompt, current_path)
           
        # 2. KALO SUDAH SELESAI LOOPING (KELUAR DARI FOR LOOP), BARU CEK LLM
        if self.llm_brain:
            ai_response = self.llm_brain.generate_response(user_prompt)
            return ai_response, current_path
        
        # 3. KALO LLM GAK ADA, BALIKIN NONE
        return None, current_path
        