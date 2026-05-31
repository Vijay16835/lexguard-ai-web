import enum

class DocumentStatus(str, enum.Enum):
    pending = "pending"
    extracting = "extracting"
    analyzing = "analyzing"
    completed = "completed"
    failed = "failed"

class Document:
    def __init__(self, **kwargs):
        self.id = None
        self.name = None
        self.path = None
        self.type = None
        self.size_in_mb = 0.0
        self.status = "pending"
        self.user_id = None
        self.extracted_text = None
        self.document_type = None
        self.risk_score = None
        self.risk_level = None
        self.summary = None
        self.uploaded_at = None
        self.analyzed_at = None
        for k, v in kwargs.items():
            setattr(self, k, v)
