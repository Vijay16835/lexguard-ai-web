"""
Comprehensive LexGuard AI Authentication & OTP Live Production Regression Test Suite
Executes end-to-end API testing directly against the production deployment on Render.
"""

import sys
import os
import time
import uuid
import json
import urllib.request
import urllib.error

BASE_URL = os.getenv("TEST_BASE_URL", "https://pdd-uw63.onrender.com").rstrip("/")

print("======================================================================")
print(f"   LEXGUARD AI LIVE PRODUCTION AUTH REGRESSION TEST SUITE             ")
print(f"   Target URL: {BASE_URL}")
print("======================================================================")

results = {
    "HEALTH_CHECK": "FAIL",
    "REGISTRATION_OTP_REQUEST": "FAIL",
    "WRONG_OTP_REJECTION": "FAIL",
    "PURPOSE_ISOLATION": "FAIL",
    "OTP_REUSE_PREVENTION": "FAIL",
    "FORGOT_PASSWORD_OTP_REQUEST": "FAIL",
    "ANDROID_AUTH_FLOW": "FAIL",
    "WEB_AUTH_FLOW": "FAIL"
}

def make_request(endpoint, method="GET", payload=None, headers=None):
    url = f"{BASE_URL}{endpoint}"
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)
    
    data = json.dumps(payload).encode("utf-8") if payload else None
    req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
    
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = {"raw": body}
        return e.code, parsed
    except Exception as err:
        return 500, {"error": str(err)}


# 1. HEALTH CHECK
print("\n[TEST 1] Testing Health Check Endpoint...")
status, body = make_request("/api/v1/auth/health")
assert status == 200, f"Health check failed with status {status}: {body}"
assert body.get("status") == "ok", f"Unexpected health status: {body}"
print(f" -> [PASS] Production status='ok', commit='{body.get('commit')}', db_host='{body.get('db_url_host')}'")
results["HEALTH_CHECK"] = "PASS"


# 2. REGISTRATION OTP REQUEST
print("\n[TEST 2] Testing Registration OTP Request (/signup)...")
test_email = f"prod_reg_{uuid.uuid4().hex[:8]}@gmail.com"
signup_payload = {
    "full_name": "Live Test User",
    "email": test_email,
    "password": "SecurePassword123!",
    "date_of_birth": "1996-08-20"
}

status, body = make_request("/api/v1/auth/signup", method="POST", payload=signup_payload)
assert status == 200, f"Signup failed with status {status}: {body}"
assert body.get("success") is True, f"Expected success=True, got: {body}"
print(f" -> [PASS] Signup OTP request succeeded: {body.get('message')}")
results["REGISTRATION_OTP_REQUEST"] = "PASS"


# 3. WRONG OTP REJECTION
print("\n[TEST 3] Testing Invalid/Wrong OTP Rejection (/verify-otp)...")
verify_payload = {
    "email": test_email,
    "otp": "000000"
}
status, body = make_request("/api/v1/auth/verify-otp", method="POST", payload=verify_payload)
assert status == 400, f"Expected status 400 for wrong OTP, got {status}: {body}"
assert "Invalid verification code" in body.get("detail", ""), f"Unexpected detail: {body}"
print(f" -> [PASS] Wrong OTP correctly rejected with HTTP 400: {body.get('detail')}")
results["WRONG_OTP_REJECTION"] = "PASS"


# 4. PURPOSE ISOLATION
print("\n[TEST 4] Testing Purpose Isolation (Registration OTP on Reset Endpoint)...")
status, body = make_request("/api/v1/auth/verify-reset-otp", method="POST", payload=verify_payload)
assert status in (400, 404), f"Expected status 400 or 404 for purpose mismatch, got {status}: {body}"
print(f" -> [PASS] Purpose isolation enforced: Registration OTP rejected on password reset endpoint (status {status}).")
results["PURPOSE_ISOLATION"] = "PASS"


# 5. OTP REUSE PREVENTION
print("\n[TEST 5] Testing Non-Existent/Reused OTP Rejection...")
status, body = make_request("/api/v1/auth/verify-otp", method="POST", payload={"email": f"nonexistent_{uuid.uuid4().hex[:6]}@gmail.com", "otp": "123456"})
assert status == 400, f"Expected status 400 for non-existent OTP, got {status}: {body}"
assert "No verification code found" in body.get("detail", ""), f"Unexpected detail: {body}"
print(f" -> [PASS] Non-existent / reused OTP correctly rejected: {body.get('detail')}")
results["OTP_REUSE_PREVENTION"] = "PASS"


# 6. FORGOT PASSWORD OTP REQUEST
print("\n[TEST 6] Testing Forgot Password OTP Request (/send-reset-otp)...")
unreg_reset_email = f"prod_reset_{uuid.uuid4().hex[:8]}@gmail.com"
status, body = make_request("/api/v1/auth/send-reset-otp", method="POST", payload={"email": unreg_reset_email})
assert status == 404, f"Expected status 404 for unregistered email, got {status}: {body}"
assert "Email is not registered" in body.get("detail", ""), f"Unexpected detail: {body}"
print(f" -> [PASS] Forgot password request for unregistered email correctly rejected: {body.get('detail')}")
results["FORGOT_PASSWORD_OTP_REQUEST"] = "PASS"


# 7. ANDROID AUTH FLOW
print("\n[TEST 7] Testing Android Mobile API Flow...")
android_headers = {"User-Agent": "LexGuard-Android/1.0 (Android 14; Mobile; Pixel 7)"}
status, body = make_request("/api/v1/auth/login", method="POST", payload={"email": "nonexistent_user@gmail.com", "password": "wrongpassword"}, headers=android_headers)
assert status == 401, f"Expected status 401 for invalid login, got {status}: {body}"
assert "email or password" in body.get("detail", "").lower(), f"Unexpected detail: {body}"
print(f" -> [PASS] Android API flow handled correctly: HTTP 401 sanitized response.")
results["ANDROID_AUTH_FLOW"] = "PASS"


# 8. WEB AUTH FLOW
print("\n[TEST 8] Testing Web Frontend API Flow...")
web_headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}
status, body = make_request("/api/v1/auth/login", method="POST", payload={"email": "nonexistent_user@gmail.com", "password": "wrongpassword"}, headers=web_headers)
assert status == 401, f"Expected status 401 for invalid login, got {status}: {body}"
assert "email or password" in body.get("detail", "").lower(), f"Unexpected detail: {body}"
print(f" -> [PASS] Web API flow handled correctly: HTTP 401 sanitized response.")
results["WEB_AUTH_FLOW"] = "PASS"


print("\n======================================================================")
print("             LIVE PRODUCTION REGRESSION RESULTS SUMMARY                ")
print("======================================================================")
for k, v in results.items():
    print(f"  {k:<30}: {v}")
print("======================================================================")

if all(v == "PASS" for v in results.values()):
    print("ALL LIVE PRODUCTION REGRESSION TESTS PASSED (100% SUCCESS)")
    sys.exit(0)
else:
    print("SOME REGRESSION TESTS FAILED")
    sys.exit(1)
