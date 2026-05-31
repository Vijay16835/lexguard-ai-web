class Notification:
    def __init__(self, **kwargs):
        self.id = None
        self.user_id = None
        self.title = None
        self.message = None
        self.type = None
        self.is_read = False
        self.created_at = None
        for k, v in kwargs.items():
            setattr(self, k, v)
