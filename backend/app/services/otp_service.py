import random
import string
import json
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.models.otp import OTPVerification
from app.services.email_service import email_service

class OTPService:
    @staticmethod
    def generate_otp(length: int = 6) -> str:
        return "".join(random.choices(string.digits, k=length))

    @staticmethod
    def create_otp(db: Session, email: str, purpose: str = "registration", registration_data: dict = None) -> str:
        # Rate limiting: Check if an OTP was sent in the last 60 seconds
        last_otp = db.query(OTPVerification).filter(
            OTPVerification.email == email,
            OTPVerification.created_at > datetime.now(timezone.utc) - timedelta(seconds=60)
        ).first()
        
        if last_otp:
            # We skip sending if one was sent very recently to prevent spam
            print(f"OTP recently sent to {email}. Skipping new generation.")
            return last_otp.otp_code

        # Delete existing OTPs for this email to keep DB clean
        db.query(OTPVerification).filter(OTPVerification.email == email).delete()
        
        otp_code = OTPService.generate_otp()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
        
        reg_data_str = json.dumps(registration_data) if registration_data else None
        
        db_otp = OTPVerification(
            email=email,
            otp_code=otp_code,
            expires_at=expires_at,
            is_verified=False,
            purpose=purpose,
            registration_data=reg_data_str
        )
        db.add(db_otp)
        db.commit()
        db.refresh(db_otp)
        
        # Send Email based on purpose
        if purpose == "password_reset":
            email_sent = email_service.send_password_reset_email(email, otp_code)
        else:
            email_sent = email_service.send_otp_email(email, otp_code)

        if not email_sent:
            print(f"CRITICAL: Failed to send OTP email to {email}")
            raise Exception("Failed to send verification email. Please check your email address or try again later.")
            
        return otp_code

    @staticmethod
    def verify_otp(db: Session, email: str, otp_code: str) -> tuple[bool, str, dict]:
        db_otp = db.query(OTPVerification).filter(
            OTPVerification.email == email,
            OTPVerification.otp_code == otp_code,
            OTPVerification.is_verified == False,
            OTPVerification.expires_at > datetime.now(timezone.utc)
        ).first()
        
        if db_otp:
            db_otp.is_verified = True
            purpose = db_otp.purpose
            reg_data = json.loads(db_otp.registration_data) if db_otp.registration_data else None
            db.commit()
            return True, purpose, reg_data
        return False, None, None

otp_service = OTPService()
