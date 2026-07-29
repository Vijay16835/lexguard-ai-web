import os
import sys
import json
import traceback

# Add backend directory to PYTHONPATH
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from app.main import app
from app.services.firebase_service import firebase_service
from app.core.config import settings

client = TestClient(app)

def run_debug():
    print("=== UPLOAD PIPELINE DEBUG INVESTIGATION ===")
    
    # 1. Check database connectivity
    print("\n--- Step 1: Database/Firebase connectivity check ---")
    try:
        conn = firebase_service._get_pg_conn()
        if conn:
            print("PostgreSQL connection pool: SUCCESS")
            cur = conn.cursor()
            cur.execute("SELECT 1;")
            print("PostgreSQL SELECT 1: SUCCESS")
            cur.close()
            conn.close()
        else:
            print("PostgreSQL connection pool: FAILED (Returned None)")
    except Exception as e:
        print(f"PostgreSQL Connection Error: {e}")
        traceback.print_exc()

    try:
        users = firebase_service.db.collection("users").limit(1).get()
        print("Firestore connectivity: SUCCESS")
    except Exception as e:
        print(f"Firestore Connection Error: {e}")
        traceback.print_exc()

    # 2. Get or create a test user
    print("\n--- Step 2: Getting/Creating Test User ---")
    test_email = "debug_user@example.com"
    test_password = "Password@123"
    
    # Ensure test user exists
    user_data = firebase_service.get_user_by_email(test_email)
    if not user_data:
        print(f"Creating test user {test_email}...")
        try:
            from app.core.security import get_password_hash
            user_data = firebase_service.create_user(
                email=test_email,
                password_hash=get_password_hash(test_password),
                full_name="Debug User",
                is_verified=True,
                auth_provider="email",
                date_of_birth="1999-01-01",
                age=27
            )
            print("Test user created successfully.")
        except Exception as e:
            print(f"Failed to create test user: {e}")
            traceback.print_exc()
            return
    else:
        print(f"Test user already exists: {user_data['id']}")

    # 3. Log in to get access token
    print("\n--- Step 3: Authenticating and getting JWT token ---")
    token = None
    try:
        response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": test_email, "password": test_password}
        )
        print(f"Login status code: {response.status_code}")
        print(f"Login response body: {response.json()}")
        token = response.json().get("access_token")
    except Exception as e:
        print(f"Login failed: {e}")
        traceback.print_exc()
        return

    if not token:
        print("Could not obtain access token. Aborting.")
        return

    # 4. Perform upload request simulation
    print("\n--- Step 4: Simulating HTTP Multipart Upload ---")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Let's use small.txt or sample.png
    file_path = os.path.join(backend_dir, "test_files", "sample.png")
    print(f"Target file path: {file_path}")
    print(f"File exists: {os.path.exists(file_path)}")
    if os.path.exists(file_path):
        print(f"File size: {os.path.getsize(file_path)} bytes")
        print(f"File permissions: {oct(os.stat(file_path).st_mode)}")
    else:
        print("Error: test file sample.png does not exist!")
        return

    try:
        with open(file_path, "rb") as f:
            files = {"file": ("sample.png", f, "image/png")}
            print("Sending POST request to /upload...")
            response = client.post(
                f"{settings.API_V1_STR}/documents/upload",
                headers=headers,
                files=files
            )
            print(f"Upload HTTP status code: {response.status_code}")
            print(f"Upload response body: {response.text}")
    except Exception as e:
        print(f"Upload request execution failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    run_debug()
