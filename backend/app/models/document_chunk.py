class DocumentChunk:
    def __init__(self, **kwargs):
        self.id = None
        self.document_id = None
        self.chunk_index = None
        self.content = None
        self.created_at = None
        for k, v in kwargs.items():
            setattr(self, k, v)
