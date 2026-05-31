class UserSettings:
    def __init__(self, **kwargs):
        self.user_id = None
        self.is_dark_mode = True
        self.notifications_enabled = True
        self.selected_language = "English"
        self.ai_model = "LexGuard AI Engine v2.0"
        self.analysis_depth = "Comprehensive"
        self.voice_speed = 1.0
        self.voice_response_enabled = False
        self.updated_at = None
        for k, v in kwargs.items():
            setattr(self, k, v)
