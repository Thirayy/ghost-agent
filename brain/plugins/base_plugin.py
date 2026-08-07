class BasePlugin:
    def metadata(self):
        return {"name": "Base Plugin", "description": "Template induk bray"}

    def can_handle(self, user_prompt):
        return False

    def execute(self, user_prompt, current_path):
        return None, current_path