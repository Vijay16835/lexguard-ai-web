class Analysis:
    def __init__(self, **kwargs):
        self.id = None
        self.document_id = None
        self.risk_level = None
        self.risk_score = None
        self.summary = None
        self.ai_confidence = 0.85
        self.parties = []
        self.important_dates = []
        self.recommendations = []
        self.raw_analysis_data = {}
        self.created_at = None
        for k, v in kwargs.items():
            setattr(self, k, v)
