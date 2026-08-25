import urllib.request
import json
import uuid
import time

BASE_URL = "https://pdd-uw63.onrender.com/api/v1"

def test_live_render_signup_flow():
    print("==================================================")
    print("   LIVE RENDER PRODUCTION AUTH & SIGNUP TEST       ")
    print("==================================================")
    
    # 1. Health Check
    try:
        req = urllib.request.urlopen(f"{BASE_URL}/auth/health", timeout=10)
        health_data = json.loads(req.read().decode())
        print(f"[HEALTH CHECK] Status: {health_data.get('status')}, Commit: {health_data.get('commit')}")
    except Exception as e:
        print(f"[HEALTH CHECK FAILED]: {e}")
        return False
        
    unique_id = uuid.uuid4().hex[:6]
    test_email = f"produser_{unique_id}@gmail.com"
    password = "TestUser@123456"
    full_name = "Production Verifier"
    dob = "1997-04-20"

    print(f"\n[SIGNUP REQUEST] Email: {test_email}")
    payload = {
        "email": test_email,
        "password": password,
        "full_name": full_name,
        "date_of_birth": dob
    }
    
    req = urllib.request.Request(
        f"{BASE_URL}/auth/signup",
        data=json.dumps(payload).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )
    
    try:
        res = urllib.request.urlopen(req, timeout=15)
        res_data = json.loads(res.read().decode())
        print(f"[SIGNUP SUCCESS] HTTP {res.status}: {res_data}")
        print("  -> OTP database write: SUCCESS (No Firestore 400 error!)")
        return True
    except urllib.error.HTTPError as he:
        err_body = he.read().decode()
        print(f"[SIGNUP HTTP ERROR] HTTP {he.code}: {err_body}")
        return False
    except Exception as e:
        print(f"[SIGNUP FAILED]: {e}")
        return False

if __name__ == "__main__":
    test_live_render_signup_flow()
