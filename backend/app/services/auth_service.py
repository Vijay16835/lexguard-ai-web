from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.auth import UserCreate, UserLogin, ChangePassword, GoogleAuth as GoogleAuthSchema
from app.core.security import get_password_hash, verify_password, create_access_token
from datetime import datetime, timezone
from typing import Optional
import logging

logger = logging.getLogger(__name__)

def signup_user(db, user_in: UserCreate):
    """Sign up a user via email credentials using FirebaseService."""
    email = user_in.email.lower().strip()
    user_data = db.get_user_by_email(email)
    
    if user_data:
        if user_data.get("is_verified"):
            raise HTTPException(status_code=400, detail="Email already registered")
        # Overwrite unverified user
        hashed_password = get_password_hash(user_in.password)
        db.update_user(user_data["id"], {
            "full_name": user_in.full_name,
            "hashed_password": hashed_password,
            "updated_at": datetime.now(timezone.utc).isoformat()
        })
        # Refetch
        user_data = db.get_user_by_id(user_data["id"])
    else:
        hashed_password = get_password_hash(user_in.password)
        user_data = db.create_user(
            email=email,
            password_hash=hashed_password,
            full_name=user_in.full_name,
            is_verified=False,
            auth_provider="email"
        )
        
    user = User(**user_data)
    access_token = create_access_token(subject=user.id)
    return user, access_token

def login_user(db, user_in: UserLogin):
    """Authenticate email & password via Firestore lookup."""
    email = user_in.email.lower().strip()
    logger.info(f"[AuthService] login_user called for email: {email}")
    
    user_data = db.get_user_by_email(email)
    if not user_data:
        logger.warning(f"[AuthService] user not found: {email}")
        raise HTTPException(status_code=401, detail="Incorrect email or password")
        
    hashed_password = user_data.get("hashed_password")
    if not hashed_password or not verify_password(user_in.password, hashed_password):
        logger.warning(f"[AuthService] password mismatch: {email}")
        raise HTTPException(status_code=401, detail="Incorrect email or password")
        
    if not user_data.get("is_verified"):
        logger.warning(f"[AuthService] login blocked, unverified: {email}")
        raise HTTPException(status_code=403, detail="Please verify your email first")
        
    user = User(**user_data)
    access_token = create_access_token(subject=user.id)
    logger.info(f"[AuthService] login success for: {user.id}")
    return user, access_token

def change_password(db, user_id: str, passwords: ChangePassword):
    """Update password in Firebase Auth and Firestore."""
    user_data = db.get_user_by_id(user_id)
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
        
    hashed_password = user_data.get("hashed_password")
    if not hashed_password or not verify_password(passwords.current_password, hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect current password")
        
    new_hash = get_password_hash(passwords.new_password)
    db.update_user_password(user_id, new_hash)
    return {"message": "Password changed successfully"}

def _verify_firebase_id_token(id_token: str) -> Optional[dict]:
    """
    Verify a Firebase ID token using the Firebase Admin SDK.
    Returns the decoded token claims, or None if verification fails.
    """
    try:
        from firebase_admin import auth as firebase_auth
        decoded = firebase_auth.verify_id_token(id_token)
        logger.info(f"[AuthService] ID token verified for uid={decoded.get('uid')}")
        return decoded
    except Exception as e:
        logger.warning(f"[AuthService] ID token verification failed: {e}")
        return None


def authenticate_google_user(db, google_in: GoogleAuthSchema):
    """
    Authenticate a Google Sign-In user against Firestore (acting as PostgreSQL layer).

    Flow:
      1. Optionally verify the Firebase ID token server-side.
      2. Look up user by firebase_uid (primary key for Google users).
      3. Fall back to email lookup (handles users created before firebase_uid was stored).
      4. If found  → update changed fields; backfill firebase_uid if missing.
      5. If not found → create new record with all required Google fields.
      6. Issue and return a JWT access token.

    Stored fields: firebase_uid, email, full_name, profile_image, auth_provider="google"
    """
    firebase_uid = google_in.firebase_uid
    email = google_in.email.lower().strip()

    # ── 1. Optional server-side ID token verification ─────────────────────
    if google_in.id_token:
        claims = _verify_firebase_id_token(google_in.id_token)
        if claims:
            # Cross-check UID from token with UID sent by client
            if claims.get("uid") != firebase_uid:
                logger.warning(
                    f"[AuthService] UID mismatch: token={claims.get('uid')} client={firebase_uid}"
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Firebase UID mismatch. Authentication rejected."
                )
        else:
            logger.warning("[AuthService] ID token could not be verified; proceeding without server-side check.")

    # ── 2. Look up by Firebase UID (primary lookup for Google users) ───────
    user_data = db.get_user_by_firebase_uid(firebase_uid)

    # ── 3. Fall back to email (migrates pre-existing email-registered users) ─
    if not user_data:
        user_data = db.get_user_by_email(email)

    if user_data:
        # ── 4a. Existing user — update changed profile fields ──────────────
        updates = {}

        # Backfill firebase_uid if not yet stored (legacy record)
        if not user_data.get("firebase_uid"):
            updates["firebase_uid"] = firebase_uid

        # Upgrade auth_provider to "google" if they previously signed up via email
        if user_data.get("auth_provider") != "google":
            updates["auth_provider"] = "google"

        if google_in.full_name and user_data.get("full_name") != google_in.full_name:
            updates["full_name"] = google_in.full_name

        if google_in.profile_image and user_data.get("profile_image") != google_in.profile_image:
            updates["profile_image"] = google_in.profile_image

        # Google users are always considered verified
        if not user_data.get("is_verified"):
            updates["is_verified"] = True

        if updates:
            db.update_user(user_data["id"], updates)
            user_data = db.get_user_by_id(user_data["id"])

        logger.info(f"[AuthService] Google login — existing user id={user_data['id']} email={email}")

    else:
        # ── 4b. New user — create record with all required Google fields ───
        logger.info(f"[AuthService] Google login — creating new user email={email} uid={firebase_uid}")
        user_data = db.create_user(
            email=email,
            password_hash="",          # No password for Google-auth users
            full_name=google_in.full_name,
            is_verified=True,
            auth_provider="google",
            firebase_uid=firebase_uid
        )
        # create_user already sets firebase_uid = user_id (the Firebase UID)
        # Patch profile_image separately (not a param of create_user)
        profile_updates = {}
        if google_in.profile_image:
            profile_updates["profile_image"] = google_in.profile_image
        if profile_updates:
            db.update_user(user_data["id"], profile_updates)
            user_data = db.get_user_by_id(user_data["id"])

    user = User(**user_data)
    access_token = create_access_token(subject=user.id)
    logger.info(f"[AuthService] Issued JWT for user id={user.id}")
    return user, access_token
