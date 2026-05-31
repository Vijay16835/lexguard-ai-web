"""
Setup: Create and verify a test user for document workflow testing.
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase_credentials.json")
if not os.path.isabs(cred_path):
    cred_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), cred_path)
os.environ["FIREBASE_CREDENTIALS_PATH"] = cred_path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.firebase_service import firebase_service
from app.core.security import get_password_hash, verify_password

TEST_EMAIL    = "doctest@lexguard.dev"
TEST_PASSWORD = "DocTest123!"

def setup_test_user():
    print(f"Setting up test user: {TEST_EMAIL}")
    
    # Check if already exists
    existing = firebase_service.get_user_by_email(TEST_EMAIL)
    if existing:
        print(f"User already exists (ID: {existing['id']}). Marking as verified and updating password.")
        firebase_service.update_user(existing["id"], {
            "hashed_password": get_password_hash(TEST_PASSWORD),
            "is_verified": True
        })
        user_id = existing["id"]
    else:
        user_data = firebase_service.create_user(
            email=TEST_EMAIL,
            password_hash=get_password_hash(TEST_PASSWORD),
            full_name="Doc Workflow Tester",
            is_verified=True,
            auth_provider="email"
        )
        user_id = user_data["id"]
        print(f"[OK] Created test user. ID: {user_id}")

    # Verify login works
    fetched = firebase_service.get_user_by_email(TEST_EMAIL)
    if fetched and verify_password(TEST_PASSWORD, fetched.get("hashed_password", "")):
        print(f"[OK] Password verified. Test user is ready.")
    else:
        print(f"[FAIL] Password verification failed!")

if __name__ == "__main__":
    setup_test_user()
