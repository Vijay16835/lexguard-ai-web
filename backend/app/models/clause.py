class Clause:
    def __init__(self, **kwargs):
        self.id = None
        self.document_id = None
        self.title = None
        self.content = None
        self.summary = None
        self.risk_level = None
        self.mitigation_advice = None
        self.created_at = None
        for k, v in kwargs.items():
            setattr(self, k, v)
