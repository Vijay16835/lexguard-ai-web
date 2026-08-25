"""
Comprehensive LexGuard AI Authentication & OTP Full Regression Test Suite
Validating:
1. Registration OTP Flow (Signup -> OTP -> Verification)
2. Forgot Password OTP Flow (Forgot Password -> OTP -> Verification -> New Password -> Login)
3. Wrong OTP Rejection
4. Expired OTP Rejection
5. OTP Reuse Prevention
6. Purpose Isolation (Registration vs Reset Password)
7. Multiple OTP Requests / Overwriting
8. Android API Flow
9. Web API Flow
"""

import sys
import os
import time
import uuid
import hashlib
from datetime import datetime, timedelta, timezone

# Load environment variables from .env if present
try:
    import dotenv
    dotenv.load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), ".env")))
except Exception:
    pass

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app
from app.services.firebase_service import firebase_service
from app.core.security import get_password_hash

client = TestClient(app)

print("======================================================================")
print("     LEXGUARD AI COMPLETE AUTH & OTP REGRESSION TEST SUITE            ")
print("======================================================================")

results = {
    "REGISTRATION_OTP": "FAIL",
    "FORGOT_PASSWORD_OTP": "FAIL",
    "WRONG_OTP": "FAIL",
    "EXPIRED_OTP": "FAIL",
    "OTP_REUSE": "FAIL",
    "PURPOSE_ISOLATION": "FAIL",
    "MULTIPLE_OTP": "FAIL",
    "ANDROID_AUTH": "FAIL",
    "WEB_AUTH": "FAIL"
}

db = firebase_service

def cleanup_user(email):
    conn = db._get_pg_conn()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM otp_verifications WHERE email = %s;", (email.lower().strip(),))
            cur.execute("DELETE FROM users WHERE email = %s;", (email.lower().strip(),))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"[Cleanup Warning] {e}")


# ----------------------------------------------------------------------
# 1. REGISTRATION OTP FLOW
# ----------------------------------------------------------------------
print("\n[TEST 1] Testing Registration OTP Flow (Signup -> OTP -> Verify)...")
reg_email = f"reg_test_{uuid.uuid4().hex[:8]}@gmail.com"
cleanup_user(reg_email)

signup_payload = {
    "full_name": "Registration Test User",
    "email": reg_email,
    "password": "Password123!",
    "date_of_birth": "1995-05-15"
}

res = client.post("/api/v1/auth/signup", json=signup_payload)
assert res.status_code == 200, f"Signup request failed: {res.text}"
assert res.json().get("success") is True

# Check user is NOT created yet
user_before = db.get_user_by_email(reg_email)
assert user_before is None, "User should NOT exist in database before OTP verification!"

# Get stored OTP from Supabase PostgreSQL
otp_record = db.get_otp(reg_email)
assert otp_record is not None, "OTP record should exist in database!"
assert otp_record.get("purpose") == "registration", f"Expected purpose='registration', got '{otp_record.get('purpose')}'"

# Fetch registration_data and verify hash
reg_data_str = otp_record.get("registration_data")
assert reg_data_str is not None, "registration_data must be stored in OTP record!"

# Compute raw OTP code for testing by trying digits (or we can inject known OTP)
# Let's override OTP in DB with known OTP hash for verification test
known_otp = "123456"
hashed_known_otp = hashlib.sha256(known_otp.encode()).hexdigest()
db.save_otp(
    email=reg_email,
    otp_code=hashed_known_otp,
    expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
    purpose="registration",
    registration_data=eval(reg_data_str) if isinstance(reg_data_str, dict) else __import__("json").loads(reg_data_str)
)

# Verify OTP
verify_res = client.post("/api/v1/auth/verify-otp", json={"email": reg_email, "otp": known_otp})
assert verify_res.status_code == 200, f"Verification failed: {verify_res.text}"
verify_data = verify_res.json()
assert verify_data.get("success") is True
assert "access_token" in verify_data

# Verify user IS created in database with is_verified=True
user_after = db.get_user_by_email(reg_email)
assert user_after is not None, "User must exist in database after successful verification!"
assert user_after.get("is_verified") is True, "User is_verified must be True!"

# Verify OTP record is deleted
otp_after = db.get_otp(reg_email)
assert otp_after is None, "OTP record must be deleted after verification!"

print(" -> [PASS] Registration OTP Flow completed successfully.")
results["REGISTRATION_OTP"] = "PASS"


# ----------------------------------------------------------------------
# 2. FORGOT PASSWORD OTP FLOW
# ----------------------------------------------------------------------
print("\n[TEST 2] Testing Forgot Password OTP Flow (Request -> Verify -> Reset -> Login)...")

# Request Reset OTP
reset_req = client.post("/api/v1/auth/send-reset-otp", json={"email": reg_email})
assert reset_req.status_code == 200, f"Send reset OTP failed: {reset_req.text}"
assert reset_req.json().get("success") is True

reset_otp_rec = db.get_otp(reg_email)
assert reset_otp_rec is not None, "Reset OTP record missing!"
assert reset_otp_rec.get("purpose") == "password_reset", f"Expected purpose='password_reset', got '{reset_otp_rec.get('purpose')}'"

# Inject known OTP for testing
reset_otp = "654321"
db.save_otp(
    email=reg_email,
    otp_code=hashlib.sha256(reset_otp.encode()).hexdigest(),
    expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
    purpose="password_reset"
)

# Verify Reset OTP
v_reset_res = client.post("/api/v1/auth/verify-reset-otp", json={"email": reg_email, "otp": reset_otp})
assert v_reset_res.status_code == 200, f"Verify reset OTP failed: {v_reset_res.text}"

# Reset Password to New Password
new_pass = "NewStrongPassword123!"
reset_pass_res = client.post("/api/v1/auth/reset-password", json={
    "email": reg_email,
    "otp": reset_otp,
    "new_password": new_pass
})
assert reset_pass_res.status_code == 200, f"Reset password failed: {reset_pass_res.text}"

# Verify OTP record is now deleted
assert db.get_otp(reg_email) is None, "Reset OTP record must be deleted after password reset!"

# Login with OLD password -> must fail 401
old_login = client.post("/api/v1/auth/login", json={"email": reg_email, "password": "Password123!"})
assert old_login.status_code == 401, "Login with old password should fail!"

# Login with NEW password -> must succeed 200
new_login = client.post("/api/v1/auth/login", json={"email": reg_email, "password": new_pass})
assert new_login.status_code == 200, f"Login with new password failed: {new_login.text}"
assert "access_token" in new_login.json()

print(" -> [PASS] Forgot Password OTP Flow completed successfully.")
results["FORGOT_PASSWORD_OTP"] = "PASS"


# ----------------------------------------------------------------------
# 3. WRONG OTP REJECTION
# ----------------------------------------------------------------------
print("\n[TEST 3] Testing Wrong OTP Rejection...")
wrong_email = f"wrong_otp_{uuid.uuid4().hex[:8]}@gmail.com"
cleanup_user(wrong_email)

# Setup OTP record
db.save_otp(
    email=wrong_email,
    otp_code=hashlib.sha256("111111".encode()).hexdigest(),
    expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
    purpose="registration",
    registration_data={"full_name": "Wrong OTP User", "password_hash": "hash", "date_of_birth": "1990-01-01"}
)

wrong_res = client.post("/api/v1/auth/verify-otp", json={"email": wrong_email, "otp": "999999"})
assert wrong_res.status_code == 400, f"Expected 400 for wrong OTP, got {wrong_res.status_code}"
assert "Invalid verification code" in wrong_res.json()["detail"]

print(" -> [PASS] Wrong OTP correctly rejected.")
results["WRONG_OTP"] = "PASS"


# ----------------------------------------------------------------------
# 4. EXPIRED OTP REJECTION
# ----------------------------------------------------------------------
print("\n[TEST 4] Testing Expired OTP Rejection...")
exp_email = f"exp_otp_{uuid.uuid4().hex[:8]}@gmail.com"
cleanup_user(exp_email)

# Save expired OTP
db.save_otp(
    email=exp_email,
    otp_code=hashlib.sha256("222222".encode()).hexdigest(),
    expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
    purpose="registration",
    registration_data={"full_name": "Expired User", "password_hash": "hash", "date_of_birth": "1990-01-01"}
)

exp_res = client.post("/api/v1/auth/verify-otp", json={"email": exp_email, "otp": "222222"})
assert exp_res.status_code == 400, f"Expected 400 for expired OTP, got {exp_res.status_code}"
assert "expired" in exp_res.json()["detail"].lower()

print(" -> [PASS] Expired OTP correctly rejected.")
results["EXPIRED_OTP"] = "PASS"


# ----------------------------------------------------------------------
# 5. OTP REUSE PREVENTION
# ----------------------------------------------------------------------
print("\n[TEST 5] Testing OTP Reuse Prevention...")
# Attempting to use the registration OTP for reg_email after it was deleted
reuse_res = client.post("/api/v1/auth/verify-otp", json={"email": reg_email, "otp": known_otp})
assert reuse_res.status_code == 400, f"Expected 400 for reused OTP, got {reuse_res.status_code}"
assert "No verification code found" in reuse_res.json()["detail"]

print(" -> [PASS] Reused OTP correctly rejected.")
results["OTP_REUSE"] = "PASS"


# ----------------------------------------------------------------------
# 6. PURPOSE ISOLATION
# ----------------------------------------------------------------------
print("\n[TEST 6] Testing Purpose Isolation (Registration vs Reset Password)...")
iso_email = f"iso_test_{uuid.uuid4().hex[:8]}@gmail.com"
cleanup_user(iso_email)

# Create reset_password OTP
db.save_otp(
    email=iso_email,
    otp_code=hashlib.sha256("333333".encode()).hexdigest(),
    expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
    purpose="password_reset"
)

# Attempt to verify it on registration endpoint /verify-otp
iso_res1 = client.post("/api/v1/auth/verify-otp", json={"email": iso_email, "otp": "333333"})
assert iso_res1.status_code == 400, f"Expected 400 for purpose mismatch, got {iso_res1.status_code}"
assert "Invalid verification code" in iso_res1.json()["detail"]

# Create registration OTP
db.save_otp(
    email=iso_email,
    otp_code=hashlib.sha256("444444".encode()).hexdigest(),
    expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
    purpose="registration",
    registration_data={"full_name": "Iso User", "password_hash": "hash", "date_of_birth": "1990-01-01"}
)

# Attempt to verify registration OTP on reset endpoint /verify-reset-otp
iso_res2 = client.post("/api/v1/auth/verify-reset-otp", json={"email": iso_email, "otp": "444444"})
assert iso_res2.status_code == 400, f"Expected 400 for purpose mismatch, got {iso_res2.status_code}"
assert "Invalid verification code" in iso_res2.json()["detail"]

print(" -> [PASS] Purpose isolation verified between registration and password_reset.")
results["PURPOSE_ISOLATION"] = "PASS"


# ----------------------------------------------------------------------
# 7. MULTIPLE OTP REQUESTS / OVERWRITING
# ----------------------------------------------------------------------
print("\n[TEST 7] Testing Multiple OTP Requests & Overwriting...")
multi_email = f"multi_otp_{uuid.uuid4().hex[:8]}@gmail.com"
cleanup_user(multi_email)

# First request
db.save_otp(
    email=multi_email,
    otp_code=hashlib.sha256("111111".encode()).hexdigest(),
    expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
    purpose="registration",
    registration_data={"full_name": "Multi User", "password_hash": "hash", "date_of_birth": "1990-01-01"}
)

# Second request (overwrite)
db.save_otp(
    email=multi_email,
    otp_code=hashlib.sha256("999999".encode()).hexdigest(),
    expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
    purpose="registration",
    registration_data={"full_name": "Multi User", "password_hash": "hash", "date_of_birth": "1990-01-01"}
)

# Verify old OTP fails
m_res1 = client.post("/api/v1/auth/verify-otp", json={"email": multi_email, "otp": "111111"})
assert m_res1.status_code == 400

# Verify new OTP succeeds
m_res2 = client.post("/api/v1/auth/verify-otp", json={"email": multi_email, "otp": "999999"})
assert m_res2.status_code == 200

print(" -> [PASS] Multiple OTP overwriting verified.")
results["MULTIPLE_OTP"] = "PASS"


# ----------------------------------------------------------------------
# 8. ANDROID AUTH API FLOW
# ----------------------------------------------------------------------
print("\n[TEST 8] Testing Android API Flow...")
android_headers = {
    "User-Agent": "LexGuard-Android/1.0 (Android 14; Mobile; Pixel 7)",
    "Content-Type": "application/json"
}

# Login request with Android headers
android_res = client.post(
    "/api/v1/auth/login",
    json={"email": reg_email, "password": new_pass},
    headers=android_headers
)
assert android_res.status_code == 200, f"Android login failed: {android_res.text}"
assert "access_token" in android_res.json()

print(" -> [PASS] Android Auth API Flow verified successfully.")
results["ANDROID_AUTH"] = "PASS"


# ----------------------------------------------------------------------
# 9. WEB AUTH API FLOW
# ----------------------------------------------------------------------
print("\n[TEST 9] Testing Web API Flow...")
web_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Content-Type": "application/json"
}

web_res = client.post(
    "/api/v1/auth/login",
    json={"email": reg_email, "password": new_pass},
    headers=web_headers
)
assert web_res.status_code == 200, f"Web login failed: {web_res.text}"
assert "access_token" in web_res.json()

print(" -> [PASS] Web Auth API Flow verified successfully.")
results["WEB_AUTH"] = "PASS"


# Cleanup test user
cleanup_user(reg_email)
cleanup_user(wrong_email)
cleanup_user(exp_email)
cleanup_user(iso_email)
cleanup_user(multi_email)

print("\n======================================================================")
print("               FINAL REGRESSION TEST RESULTS SUMMARY                  ")
print("======================================================================")
for k, v in results.items():
    print(f"  {k:<25}: {v}")
print("======================================================================")

if all(v == "PASS" for v in results.values()):
    print("ALL AUTHENTICATION REGRESSION TESTS PASSED (100% SUCCESS)")
    sys.exit(0)
else:
    print("SOME REGRESSION TESTS FAILED")
    sys.exit(1)
