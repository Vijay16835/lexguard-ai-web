class OTPVerification:
    def __init__(self, **kwargs):
        self.id = None
        self.email = None
        self.otp_code = None
        self.expires_at = None
        self.is_verified = False
        self.purpose = "registration"
        self.registration_data = None
        self.created_at = None
        for k, v in kwargs.items():
            setattr(self, k, v)
