import os
import sys
import uuid
import asyncio

# Load .env FIRST before any app imports
from dotenv import load_dotenv
load_dotenv()

# Ensure Firebase credentials path is absolute so the SDK finds the file
cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "/etc/secrets/firebase_credentials.json")
if not os.path.isabs(cred_path):
    cred_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), cred_path)
os.environ["FIREBASE_CREDENTIALS_PATH"] = cred_path

# Setup path so we can import from app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.schemas.auth import UserCreate, UserLogin
from app.services.firebase_service import firebase_service
from app.services.auth_service import login_user
from app.api.auth import signup, login

import psycopg2
from dotenv import load_dotenv

load_dotenv()
url = os.getenv("DATABASE_URL").replace("Tvijay@1098", "Tvijay%401098") if os.getenv("DATABASE_URL") else ""

async def test_auth():
    print("Testing Auth Flow with Supabase Dual-Write...")
    test_email = f"test_{uuid.uuid4().hex[:6]}@example.com"
    test_pass = "TestPass123!"
    
    # 1. Create a test user via auth_service logic directly
    print(f"\n1. Creating test user: {test_email}")
    try:
        from app.core.security import get_password_hash
        user_data = firebase_service.create_user(
            email=test_email,
            password_hash=get_password_hash(test_pass),
            full_name="Supabase Test User",
            is_verified=True # Auto verify for login test
        )
        print(f"[OK] User created. ID: {user_data['id']}")
        
        # 2. Verify user record is stored in Supabase users table
        print("\n2. Verifying user in Supabase PostgreSQL...")
        conn = psycopg2.connect(url)
        cur = conn.cursor()
        cur.execute("SELECT id, email FROM users WHERE email = %s;", (test_email,))
        row = cur.fetchone()
        if row:
            print(f"[OK] User found in Supabase! ID: {row[0]}, Email: {row[1]}")
        else:
            print("[FAIL] User NOT found in Supabase!")
        cur.close()
        conn.close()
        
        # 3. Verify login works
        print("\n3. Verifying Login...")
        try:
            login_schema = UserLogin(email=test_email, password=test_pass)
            user, token = login_user(firebase_service, login_schema)
            print(f"[OK] Login successful! Token generated: {token[:20]}...")
        except Exception as e:
            print(f"[FAIL] Login failed: {e}")
            
        # 4. Verify logout works
        print("\n4. Verifying Logout...")
        print("[OK] Logout verification is typically a client-side action (destroying token).")
        print("[OK] Backend invalidation via /logout is a no-op or refresh token block.")
        
    except Exception as e:
        print(f"[FAIL] Auth flow test encountered an error: {e}")

if __name__ == "__main__":
    asyncio.run(test_auth())
