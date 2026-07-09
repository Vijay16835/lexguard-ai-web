import os
import sys
import unittest
import time
from unittest.mock import MagicMock, patch

# Add current directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Pre-set mock environment variables
os.environ["DATABASE_URL"] = "postgresql://mock_user:mock_pass@localhost:5432/mock_db"
os.environ["FIREBASE_CREDENTIALS_PATH"] = "backend/firebase_credentials.json"
os.environ["FIREBASE_STORAGE_BUCKET"] = "lexguard-ai.appspot.com"

# Create a mock psycopg2 pool and connection
mock_conn = MagicMock()
mock_cur = MagicMock()
mock_conn.cursor.return_value = mock_cur
# Mock SQL select response to return status, error_message, extracted_text
mock_cur.fetchone.return_value = ("completed", None, "Mock extracted text")

# Import firebase_service
from app.services.firebase_service import firebase_service
firebase_service._get_pg_conn = MagicMock(return_value=mock_conn)

# In-memory database mock
_in_memory_db = {}

def mock_create_document(doc_data):
    doc_id = doc_data["id"]
    _in_memory_db[doc_id] = doc_data.copy()
    print(f"[MOCK FIRESTORE] Created document {doc_id}")
    return True

def mock_get_document(doc_id):
    doc = _in_memory_db.get(doc_id)
    if doc:
        print(f"[MOCK FIRESTORE] Found document {doc_id}")
        return doc.copy()
    print(f"[MOCK FIRESTORE] Document {doc_id} NOT found")
    return None

def mock_update_document(doc_id, updates):
    if doc_id in _in_memory_db:
        _in_memory_db[doc_id].update(updates)
        print(f"[MOCK FIRESTORE] Updated document {doc_id} with {updates.get('status') or updates}")
        return True
    print(f"[MOCK FIRESTORE] Update failed: document {doc_id} not found")
    return False

def mock_save_analysis(doc_id, analysis_data):
    print(f"[MOCK FIRESTORE] Saved analysis for document {doc_id}")
    return True

def mock_delete_document_clauses(doc_id):
    print(f"[MOCK FIRESTORE] Deleted clauses for document {doc_id}")
    return True

def mock_save_clause(clause_data):
    print(f"[MOCK FIRESTORE] Saved clause: {clause_data.get('title')}")
    return True

firebase_service.create_document = mock_create_document
firebase_service.get_document = mock_get_document
firebase_service.update_document = mock_update_document
firebase_service.save_analysis = mock_save_analysis
firebase_service.delete_document_clauses = mock_delete_document_clauses
firebase_service.save_clause = mock_save_clause

# Mock Groq Service
from app.services.groq_service import groq_service
async def mock_analyze_document(text):
    print("[MOCK GROQ] Analyzing document text...")
    return {
        "risk_score": 35,
        "risk_level": "Medium",
        "summary": "This is a mock contract summary.",
        "document_type": "NDA",
        "clauses": [
            {
                "title": "Confidentiality Clause",
                "content": "All information shared must be kept confidential.",
                "risk_level": "Low",
                "explanation": "Standard confidentiality obligation.",
                "mitigation_advice": "No action needed."
            }
        ]
    }
groq_service.analyze_document = mock_analyze_document

# Mock Supabase
class MockStorageBucket:
    def upload(self, file, path, file_options=None):
        print(f"[MOCK SUPABASE] Uploaded to {path}")
        return True
    def get_public_url(self, path):
        print(f"[MOCK SUPABASE] Public URL for {path}")
        return f"http://mock-supabase/storage/{path}"
    def download(self, path):
        print(f"[MOCK SUPABASE] Downloaded {path}")
        # The path is users/{user_id}/documents/{document_id}.{extension}
        doc_id = path.split("/")[-1].split(".")[0]
        ext = path.split("/")[-1].split(".")[-1]
        local_upload_path = os.path.join("uploads", f"{doc_id}.{ext}")
        if os.path.exists(local_upload_path):
            with open(local_upload_path, "rb") as f:
                return f.read()
        return b"Mock file content"

class MockStorage:
    def from_(self, bucket_name):
        return MockStorageBucket()

class MockSupabaseClient:
    def __init__(self):
        self.storage = MockStorage()

mock_supabase = MockSupabaseClient()
import app.services.document_service
app.services.document_service.get_supabase = MagicMock(return_value=mock_supabase)
import app.api.documents
app.api.documents.get_supabase = MagicMock(return_value=mock_supabase)

# Import TestClient and app
from fastapi.testclient import TestClient
from app.main import app
from app.api.deps import get_current_user
from app.models.user import User

# Mock user dependency
mock_user = User(
    id="test-user-uuid",
    email="test_user@lexguard.ai",
    full_name="Test Legal Auditor"
)
app.dependency_overrides[get_current_user] = lambda: mock_user

# Setup self-contained test config
TEST_DIR = os.path.join(os.path.dirname(__file__), "test_files")
files_to_test = {
    "txt_small": (os.path.join(TEST_DIR, "small.txt"), "This is a small legal text document for testing."),
    "txt_large": (os.path.join(TEST_DIR, "large.txt"), "This is a large legal text document for testing. " * 300),
    "docx_simple": (os.path.join(TEST_DIR, "simple.docx"), "This is a simple contract document created in DOCX format."),
    "docx_large": (os.path.join(TEST_DIR, "large.docx"), "This is a large contract document created in DOCX format.\n" * 150),
    "pdf_text": (os.path.join(TEST_DIR, "text.pdf"), "This is a standard PDF document with actual selectable text layers for contract analysis."),
    "pdf_scanned": (os.path.join(TEST_DIR, "scanned.pdf"), "This is a scanned PDF document with no text layer. It requires OCR fallback to extract the text."),
    "jpg_image": (os.path.join(TEST_DIR, "sample.jpg"), "This is a JPEG image representing a contract clause. It requires OCR extraction."),
    "jpeg_image": (os.path.join(TEST_DIR, "sample.jpeg"), "This is a JPEG image representing a second contract clause. It requires OCR extraction."),
    "png_image": (os.path.join(TEST_DIR, "sample.png"), "This is a PNG image representing a legal agreement. It requires OCR extraction."),
}

def run_mocked_tests():
    os.makedirs("uploads", exist_ok=True)
    client = TestClient(app)
    print("\nStarting MOCKED test matrix execution...\n")
    
    success_count = 0
    total_count = len(files_to_test)
    
    for name, (path, _) in files_to_test.items():
        print("=" * 60)
        print(f"TESTING FILE: {os.path.basename(path)} ({name})")
        print("=" * 60)
        
        if not os.path.exists(path):
            print(f"Skipping {name} as the file could not be prepared.")
            continue
            
        try:
            with open(path, "rb") as f:
                response = client.post(
                    "/api/v1/documents/upload",
                    files={"file": (os.path.basename(path), f)}
                )
            
            print(f"Upload Status Code: {response.status_code}")
            if response.status_code != 200:
                print(f"Upload failed: {response.json()}")
                continue
                
            res_json = response.json()
            doc_id = res_json["document"]["id"]
            print(f"Document ID generated: {doc_id}")
            
            # Wait a short moment to let background task run
            time_spent = 0
            status_fs = None
            err_fs = None
            
            while time_spent < 15:
                doc_fs = mock_get_document(doc_id)
                status_fs = doc_fs.get("status") if doc_fs else None
                err_fs = doc_fs.get("error_message") if doc_fs else None
                if status_fs in ["completed", "failed"]:
                    break
                time.sleep(0.5)
                time_spent += 0.5
                
            print(f"Firestore Document Status: {status_fs} (Error: {err_fs})")
            
            if status_fs == "completed":
                print("SUCCESS: Document processed fully through the pipeline!")
                success_count += 1
            elif status_fs == "failed":
                print(f"FAILED: Document status is failed. Error: {err_fs}")
            else:
                print(f"WARNING: Document status is: FS={status_fs}")
                
        except Exception as e:
            print(f"Error testing {name}: {e}")
            import traceback
            traceback.print_exc()
            
    print("=" * 60)
    print(f"MOCKED TEST RESULTS: {success_count}/{total_count} passed.")
    print("=" * 60)
    
    if success_count == total_count:
        print("ALL TESTS PASSED SUCCESSFULLY!")
        sys.exit(0)
    else:
        print("SOME TESTS FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    run_mocked_tests()
