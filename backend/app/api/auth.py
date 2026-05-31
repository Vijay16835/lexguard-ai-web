from fastapi import APIRouter, Depends, HTTPException, status
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import UserCreate, UserLogin, Token, OTPVerify, ForgotPassword, ResetPassword, GoogleAuth, SendOTP, ChangePassword
from app.core.security import get_password_hash, create_access_token
from app.services.auth_service import signup_user, login_user, authenticate_google_user
from app.services.auth_service import change_password as change_pwd_service
from app.services.email_service import email_service
from app.api.deps import get_current_user
from datetime import datetime, timedelta, timezone
import random
import string
from app.services.document_service import get_user_storage_usage_mb

router = APIRouter()


@router.post("/signup")
async def signup(user_in: UserCreate, db = Depends(get_db)):
    try:
        email = user_in.email.lower().strip()
        # Check if user already exists in Firestore
        user_data = db.get_user_by_email(email)
        if user_data:
            if user_data.get("is_verified"):
                raise HTTPException(status_code=400, detail="User with this email already exists")
            # If not verified, overwrite password and full_name
            db.update_user(user_data["id"], {
                "full_name": user_in.full_name,
                "hashed_password": get_password_hash(user_in.password),
                "updated_at": datetime.now(timezone.utc).isoformat()
            })
            user_id = user_data["id"]
        else:
            # Create user in Firebase / Firestore
            user_data = db.create_user(
                email=email,
                password_hash=get_password_hash(user_in.password),
                full_name=user_in.full_name,
                is_verified=False,
                auth_provider="email"
            )
            user_id = user_data["id"]
        
        # Generate random 6-digit OTP
        otp_code = "".join(random.choices(string.digits, k=6))
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
        
        db.save_otp(
            email=email,
            otp_code=otp_code,
            expires_at=expires_at,
            purpose="registration"
        )
        
        # Send OTP via email
        email_sent = email_service.send_otp_email(email, otp_code)
        if not email_sent:
            raise Exception("Failed to send email via SMTP")
        
        return {"success": True, "message": "OTP sent to your email. Please verify to complete registration."}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Signup error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/login", response_model=Token)
async def login(user_in: UserLogin, db = Depends(get_db)):
    print(f"[Auth API] login request for email: {user_in.email}")
    try:
        user, access_token = login_user(db, user_in)
        print(f"[Auth API] login success for user id: {user.id}")
        
        created_at_val = None
        if user.created_at:
            if isinstance(user.created_at, datetime):
                created_at_val = user.created_at.isoformat()
            else:
                created_at_val = user.created_at
                
        storage_used_mb = get_user_storage_usage_mb(user.id)
                
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "is_verified": user.is_verified,
                "profile_image": user.profile_image,
                "created_at": created_at_val,
                "storage_used_mb": storage_used_mb,
                "storage_limit_mb": 20.0
            }
        }
    except Exception as e:
        print(f"Login error: {e}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/google-auth", response_model=Token)
async def google_auth_endpoint(google_in: GoogleAuth, db = Depends(get_db)):
    print(f"[Auth API] google-auth request for email: {google_in.email}")
    try:
        user, access_token = authenticate_google_user(db, google_in)
        print(f"[Auth API] google-auth success for user id: {user.id}")
        
        created_at_val = None
        if user.created_at:
            if isinstance(user.created_at, datetime):
                created_at_val = user.created_at.isoformat()
            else:
                created_at_val = user.created_at
                
        storage_used_mb = get_user_storage_usage_mb(user.id)
                
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "is_verified": user.is_verified,
                "profile_image": user.profile_image,
                "created_at": created_at_val,
                "storage_used_mb": storage_used_mb,
                "storage_limit_mb": 20.0
            }
        }
    except Exception as e:
        print(f"Google Auth error: {e}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/verify-otp")
async def verify_otp(data: OTPVerify, db = Depends(get_db)):
    try:
        email = data.email.lower().strip()
        user_data = db.get_user_by_email(email)
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")
            
        if user_data.get("is_verified"):
            raise HTTPException(status_code=400, detail="User is already verified")
            
        otp_record = db.get_otp(email)
        if not otp_record or otp_record.get("otp_code") != data.otp:
            raise HTTPException(status_code=400, detail="Invalid OTP")
            
        expires_at_str = otp_record.get("expires_at")
        expires_at = datetime.fromisoformat(expires_at_str) if expires_at_str else None
        if not expires_at or expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="Expired OTP")
            
        # Verify user and delete OTP
        db.update_user(user_data["id"], {"is_verified": True})
        db.delete_otp_record(email)
        
        # Reload user
        updated_user_data = db.get_user_by_id(user_data["id"])
        user = User(**updated_user_data)
        
        access_token = create_access_token(subject=user.id)
        
        created_at_val = None
        if user.created_at:
            if isinstance(user.created_at, datetime):
                created_at_val = user.created_at.isoformat()
            else:
                created_at_val = user.created_at
                
        storage_used_mb = get_user_storage_usage_mb(user.id)
                
        return {
            "success": True,
            "message": "OTP verified successfully",
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "is_verified": user.is_verified,
                "profile_image": user.profile_image,
                "created_at": created_at_val,
                "storage_used_mb": storage_used_mb,
                "storage_limit_mb": 20.0
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Verify OTP Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during verification")


@router.post("/send-otp")
async def send_otp(data: SendOTP, db = Depends(get_db)):
    try:
        email = data.email.lower().strip()
        user_data = db.get_user_by_email(email)
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")
            
        otp_code = "".join(random.choices(string.digits, k=6))
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
        
        db.save_otp(
            email=email,
            otp_code=otp_code,
            expires_at=expires_at,
            purpose="registration"
        )
        
        email_sent = email_service.send_otp_email(email, otp_code)
        if not email_sent:
            raise Exception("Failed to send email via SMTP")
            
        return {"success": True, "message": "OTP resent successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Send OTP error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while resending OTP")


@router.post("/send-reset-otp")
async def send_reset_otp(data: ForgotPassword, db = Depends(get_db)):
    try:
        email = data.email.lower().strip()
        user_data = db.get_user_by_email(email)
        if not user_data:
            raise HTTPException(status_code=404, detail="No account found with this email address.")
        
        # Generate OTP
        otp_code = "".join(random.choices(string.digits, k=6))
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
        
        db.save_otp(
            email=email,
            otp_code=otp_code,
            expires_at=expires_at,
            purpose="password_reset"
        )
        
        email_sent = email_service.send_password_reset_email(email, otp_code)
        if not email_sent:
            raise Exception("Failed to send reset email")
            
        return {"success": True, "message": "Verification code sent to your email."}
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR: send-reset-otp failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/verify-reset-otp")
async def verify_reset_otp(data: OTPVerify, db = Depends(get_db)):
    try:
        email = data.email.lower().strip()
        user_data = db.get_user_by_email(email)
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")
            
        otp_record = db.get_otp(email)
        if not otp_record or otp_record.get("otp_code") != data.otp or otp_record.get("purpose") != "password_reset":
            raise HTTPException(status_code=400, detail="Invalid OTP")
            
        expires_at_str = otp_record.get("expires_at")
        expires_at = datetime.fromisoformat(expires_at_str) if expires_at_str else None
        if not expires_at or expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="Expired OTP")
        
        # Do NOT clear OTP yet, they need it for the final reset-password step!
        return {"success": True, "message": "Code verified successfully.", "email": email, "otp": data.otp}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Verify reset OTP Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/reset-password")
async def reset_password(data: ResetPassword, db = Depends(get_db)):
    try:
        email = data.email.lower().strip()
        user_data = db.get_user_by_email(email)
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found.")
            
        otp_record = db.get_otp(email)
        # Re-verify the OTP one last time
        if not otp_record or otp_record.get("otp_code") != data.otp or otp_record.get("purpose") != "password_reset":
            raise HTTPException(status_code=400, detail="Verification expired or invalid. Please request a new code.")
            
        expires_at_str = otp_record.get("expires_at")
        expires_at = datetime.fromisoformat(expires_at_str) if expires_at_str else None
        if not expires_at or expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="OTP Expired")
        
        # Update Password and delete OTP
        new_hash = get_password_hash(data.new_password)
        db.update_user_password(user_data["id"], new_hash)
        db.delete_otp_record(email)
        
        return {"success": True, "message": "Password updated successfully. You can now sign in."}
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR: reset-password failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/change-password")
async def change_password_endpoint(
    data: ChangePassword, 
    db = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    return change_pwd_service(db, current_user.id, data)


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    created_at_val = None
    if current_user.created_at:
        if isinstance(current_user.created_at, datetime):
            created_at_val = current_user.created_at.isoformat()
        else:
            created_at_val = current_user.created_at
            
    storage_used_mb = get_user_storage_usage_mb(current_user.id)
            
    return {
        "id": current_user.id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "is_verified": current_user.is_verified,
        "profile_image": current_user.profile_image,
        "created_at": created_at_val,
        "storage_used_mb": storage_used_mb,
        "storage_limit_mb": 20.0
    }
