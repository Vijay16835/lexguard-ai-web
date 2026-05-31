class ChatHistory:
    def __init__(self, **kwargs):
        self.id = None
        self.document_id = None
        self.user_id = None
        self.query = None
        self.response = None
        self.language = "English"
        self.created_at = None
        for k, v in kwargs.items():
            setattr(self, k, v)
