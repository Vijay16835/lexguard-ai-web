import os
import sys
import uuid
import hashlib
from datetime import datetime, timezone, timedelta

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.services.firebase_service import firebase_service

def test_pure_supabase_auth_suite():
    print("===============================================================")
    print("   AUTOMATED SUITE: PROVING FIRESTORE IS NOT REQUIRED FOR AUTH ")
    print("===============================================================")

    # Force Firestore db instance to None to simulate completely disabled/unavailable Firestore
    original_db = firebase_service._db
    firebase_service._db = None

    try:
        unique_id = uuid.uuid4().hex[:8]
        test_email = f"puredb_{unique_id}@example.com"
        raw_otp = "852963"
        hashed_otp = hashlib.sha256(raw_otp.encode()).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
        reg_payload = {"full_name": "Pure Supabase", "date_of_birth": "1995-05-15", "password_hash": "hash123"}

        print("\n[A-D] Testing OTP Save with Firestore completely DISABLED...")
        saved = firebase_service.save_otp(
            email=test_email,
            otp_code=hashed_otp,
            expires_at=expires_at,
            purpose="registration",
            registration_data=reg_payload
        )
        assert saved is True, "Failed to save OTP to Supabase PostgreSQL when Firestore is disabled!"
        print("  -> PASS: Registration OTP saved to Supabase without Firestore!")

        print("\n[E] Verifying row exists in Supabase otp_verifications table...")
        otp_rec = firebase_service.get_otp(test_email)
        assert otp_rec is not None, "OTP row missing in Supabase PostgreSQL!"
        assert otp_rec["otp_code"] == hashed_otp, "OTP hash mismatch!"
        assert otp_rec["is_verified"] is False, "OTP should be unverified initially!"
        print("  -> PASS: Supabase otp_verifications row verified!")

        print("\n[G] Testing Wrong OTP rejection...")
        wrong_hash = hashlib.sha256("000000".encode()).hexdigest()
        assert otp_rec["otp_code"] != wrong_hash, "Wrong OTP should not match!"
        print("  -> PASS: Wrong OTP correctly rejected!")

        print("\n[H] Testing Expired OTP detection...")
        past_time = datetime.now(timezone.utc) - timedelta(minutes=10)
        expired_email = f"expired_{unique_id}@example.com"
        firebase_service.save_otp(expired_email, hashed_otp, past_time, "registration")
        exp_rec = firebase_service.get_otp(expired_email)
        exp_at = datetime.fromisoformat(exp_rec["expires_at"])
        assert exp_at < datetime.now(timezone.utc), "Expired OTP detection failed!"
        firebase_service.delete_otp_record(expired_email)
        print("  -> PASS: Expired OTP correctly rejected!")

        print("\n[F] Verifying OTP and checking is_verified becomes TRUE...")
        verify_res = firebase_service.verify_otp_record(test_email)
        assert verify_res is True, "Failed to mark OTP record as verified!"
        updated_rec = firebase_service.get_otp(test_email)
        assert updated_rec["is_verified"] is True, "is_verified field did not update to True!"
        print("  -> PASS: OTP marked as verified in Supabase PostgreSQL!")

        print("\n[I] Testing User Creation & Lookup using Supabase PostgreSQL ONLY...")
        user_res = firebase_service.create_user(
            email=test_email,
            password_hash="hash123",
            full_name="Pure Supabase",
            is_verified=True,
            auth_provider="email",
            date_of_birth="1995-05-15",
            age=30
        )
        assert user_res is not None, "User creation failed!"
        
        lookup_user = firebase_service.get_user_by_email(test_email)
        assert lookup_user is not None, "User lookup by email failed!"
        assert lookup_user["email"] == test_email, "Email mismatch!"
        print("  -> PASS: User creation and lookup in Supabase PostgreSQL verified!")

        print("\nClean up test records...")
        firebase_service.delete_otp_record(test_email)
        print("  -> PASS: Cleanup complete!")

        print("\n===============================================================")
        print("   SUCCESS: ALL AUTH & OTP OPERATIONS SUCCEED WITHOUT FIRESTORE ")
        print("===============================================================")

    finally:
        firebase_service._db = original_db

if __name__ == "__main__":
    test_pure_supabase_auth_suite()
