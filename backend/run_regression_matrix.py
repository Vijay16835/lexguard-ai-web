import os
import sys
import time
import json
import traceback

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from app.main import app
from app.services.firebase_service import firebase_service
from app.core.config import settings

client = TestClient(app)

TEST_FILES = [
    ("sample.pdf", "application/pdf"),
    ("simple.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    ("large.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    ("small.txt", "text/plain"),
    ("large.txt", "text/plain"),
    ("sample.jpg", "image/jpeg"),
    ("sample.jpeg", "image/jpeg"),
    ("sample.png", "image/png"),
    ("sample.webp", "image/webp"),
    ("sample.tiff", "image/tiff"),
    ("sample.bmp", "image/bmp"),
]

def run_matrix():
    print("==================================================")
    print("      LEXGUARD REGRESSION MATRIX VALIDATION       ")
    print("==================================================")

    # 1. Authenticate user
    test_email = "regression_user@example.com"
    test_password = "Password@123"

    user_data = firebase_service.get_user_by_email(test_email)
    if not user_data:
        from app.core.security import get_password_hash
        user_data = firebase_service.create_user(
            email=test_email,
            password_hash=get_password_hash(test_password),
            full_name="Regression User",
            is_verified=True,
            auth_provider="email",
            date_of_birth="1995-05-05",
            age=31
        )
    
    login_res = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"email": test_email, "password": test_password}
    )
    if login_res.status_code != 200:
        print(f"Login failed: {login_res.text}")
        return
    
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Clean up old test user documents to prevent storage quota limits
    try:
        user_docs = firebase_service.get_user_documents(user_data["id"])
        for doc in user_docs:
            firebase_service.delete_document(doc["id"])
    except Exception as cleanup_err:
        print(f"Pre-test document cleanup warning: {cleanup_err}")

    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_files": len(TEST_FILES),
        "passed": 0,
        "failed": 0,
        "details": []
    }

    test_files_dir = os.path.join(backend_dir, "test_files")

    for filename, mime_type in TEST_FILES:
        filepath = os.path.join(test_files_dir, filename)
        if not os.path.exists(filepath):
            print(f"[-] File missing: {filename}")
            report["details"].append({
                "file": filename,
                "status": "failed",
                "error": "File not found on disk"
            })
            report["failed"] += 1
            continue

        print(f"\n[+] Testing: {filename} ({mime_type})")
        t0 = time.time()
        
        try:
            with open(filepath, "rb") as f:
                up_res = client.post(
                    f"{settings.API_V1_STR}/documents/upload",
                    headers=headers,
                    files={"file": (filename, f, mime_type)}
                )

            if up_res.status_code != 200:
                print(f"    Upload failed: HTTP {up_res.status_code} - {up_res.text}")
                report["details"].append({
                    "file": filename,
                    "status": "failed",
                    "error": f"Upload HTTP {up_res.status_code}"
                })
                report["failed"] += 1
                continue

            doc_id = up_res.json()["document"]["id"]
            print(f"    Uploaded successfully. Document ID: {doc_id}")

            # Poll for status
            final_status = "pending"
            final_data = {}
            for poll in range(30):
                time.sleep(1)
                st_res = client.get(
                    f"{settings.API_V1_STR}/documents/{doc_id}/status",
                    headers=headers
                )
                if st_res.status_code == 200:
                    st_data = st_res.json()
                    final_status = st_data.get("status", "pending")
                    final_data = st_data
                    if final_status in ("completed", "failed"):
                        break
            
            elapsed = time.time() - t0

            if final_status == "completed":
                print(f"    STATUS: COMPLETED in {elapsed:.2f}s | Risk Score: {final_data.get('risk_score')}")
                report["passed"] += 1
                report["details"].append({
                    "file": filename,
                    "mime_type": mime_type,
                    "status": "PASSED",
                    "processing_time_seconds": round(elapsed, 2),
                    "risk_score": final_data.get("risk_score"),
                    "risk_level": final_data.get("risk_level")
                })
            else:
                err_msg = final_data.get("error_message", "Timeout / incomplete")
                print(f"    STATUS: FAILED in {elapsed:.2f}s | Error: {err_msg}")
                report["failed"] += 1
                report["details"].append({
                    "file": filename,
                    "mime_type": mime_type,
                    "status": "FAILED",
                    "processing_time_seconds": round(elapsed, 2),
                    "error_message": err_msg
                })

        except Exception as e:
            elapsed = time.time() - t0
            print(f"    EXCEPTION: {e}")
            report["failed"] += 1
            report["details"].append({
                "file": filename,
                "mime_type": mime_type,
                "status": "FAILED",
                "processing_time_seconds": round(elapsed, 2),
                "error_message": str(e)
            })

    print("\n==================================================")
    print(f" SUMMARY: {report['passed']}/{report['total_files']} Passed, {report['failed']} Failed")
    print("==================================================")

    report_path = os.path.join(backend_dir, "validation_report.json")
    with open(report_path, "w", encoding="utf-8") as rf:
        json.dump(report, rf, indent=2)

    print(f"Validation report saved to: {report_path}")
    return report["failed"] == 0

if __name__ == "__main__":
    success = run_matrix()
    sys.exit(0 if success else 1)
