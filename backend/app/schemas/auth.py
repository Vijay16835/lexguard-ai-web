from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
import re

PASSWORD_REGEX = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$')

def validate_strong_password(v: str) -> str:
    if len(v) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if len(v.encode('utf-8')) > 72:
        raise ValueError("Password cannot be longer than 72 bytes")
    if not PASSWORD_REGEX.match(v):
        raise ValueError(
            "Password must contain at least one uppercase letter, one lowercase letter, "
            "one number, and one special character (@$!%*?&)."
        )
    return v

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    date_of_birth: str

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        return validate_strong_password(v)

    @field_validator('date_of_birth')
    @classmethod
    def validate_dob(cls, v: str) -> str:
        from datetime import datetime
        try:
            dob = datetime.strptime(v, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Invalid date of birth format. Use YYYY-MM-DD.")
        if dob > datetime.now().date():
            raise ValueError("Date of birth cannot be in the future.")
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

    @field_validator('password')
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if len(v.encode('utf-8')) > 72:
            raise ValueError("Password cannot be longer than 72 bytes")
        return v

class SendOTP(BaseModel):
    email: EmailStr

class OTPVerify(BaseModel):
    email: EmailStr
    otp: str

class ForgotPassword(BaseModel):
    email: EmailStr

class ResetPassword(BaseModel):
    email: EmailStr
    otp: str
    new_password: str

    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        return validate_strong_password(v)

class ChangePassword(BaseModel):
    current_password: str
    new_password: str

    @field_validator('current_password')
    @classmethod
    def validate_current_password_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if len(v.encode('utf-8')) > 72:
            raise ValueError("Password cannot be longer than 72 bytes")
        return v

    @field_validator('new_password')
    @classmethod
    def validate_new_password_strength(cls, v: str) -> str:
        return validate_strong_password(v)

class GoogleAuth(BaseModel):
    firebase_uid: str                      # Firebase UID from google_sign_in
    id_token: Optional[str] = None        # Firebase ID token for server-side verification
    email: EmailStr
    full_name: str
    profile_image: Optional[str] = None
