class TranslatedSummary:
    def __init__(self, **kwargs):
        self.id = None
        self.document_id = None
        self.language = "English"
        self.summary = None
        self.created_at = None
        for k, v in kwargs.items():
            setattr(self, k, v)
