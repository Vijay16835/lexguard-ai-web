from pydantic import BaseModel, EmailStr
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

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

class ChangePassword(BaseModel):
    current_password: str
    new_password: str

class GoogleAuth(BaseModel):
    firebase_uid: str                      # Firebase UID from google_sign_in
    id_token: Optional[str] = None        # Firebase ID token for server-side verification
    email: EmailStr
    full_name: str
    profile_image: Optional[str] = None
