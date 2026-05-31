"""
Document Workflow Verification Script
Tests: Upload PDF/DOCX/TXT, Supabase Storage, Supabase PostgreSQL metadata, History, Download
Runs against the live FastAPI backend via HTTP requests.
"""
import os
import requests
import psycopg2
from dotenv import load_dotenv
from io import BytesIO

load_dotenv()

BASE_URL      = "http://127.0.0.1:8000/api/v1"
DB_URL        = os.getenv("DATABASE_URL", "").replace("Tvijay@1098", "Tvijay%401098")
TEST_EMAIL    = "doctest@lexguard.dev"
TEST_PASSWORD = "DocTest123!"


# --- Step 0: Login to get a JWT -----------------------------------------------
def get_token():
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }, timeout=15)
    if resp.status_code == 200:
        token = resp.json().get("access_token")
        print(f"[OK] Logged in as {TEST_EMAIL}. Token: {token[:20]}...")
        return token
    print(f"[FAIL] Login failed ({resp.status_code}): {resp.text[:200]}")
    return None


# --- Step 1-3: Upload documents ------------------------------------------------
def upload_file(token, filename, content, mime_type):
    headers = {"Authorization": f"Bearer {token}"}
    files   = {"file": (filename, BytesIO(content), mime_type)}
    resp    = requests.post(f"{BASE_URL}/documents/upload", headers=headers, files=files, timeout=30)
    if resp.status_code == 200:
        doc_id = resp.json()["document"]["id"]
        print(f"[OK] Uploaded '{filename}'. Doc ID: {doc_id}")
        return doc_id
    print(f"[FAIL] Upload '{filename}' failed ({resp.status_code}): {resp.text[:200]}")
    return None


# --- Step 4-5: Verify Supabase Storage URL + PostgreSQL metadata ---------------
def verify_supabase(doc_id, filename):
    try:
        conn = psycopg2.connect(DB_URL)
        cur  = conn.cursor()
        cur.execute("SELECT id, name, path, status FROM documents WHERE id = %s;", (doc_id,))
        row  = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            has_url = bool(row[2]) and row[2].startswith("http")
            print(f"[OK] PostgreSQL: '{filename}' found. Status={row[3]}, StorageURL={'YES' if has_url else 'MISSING'}")
            return True
        print(f"[FAIL] PostgreSQL: '{filename}' record NOT found!")
        return False
    except Exception as e:
        print(f"[FAIL] PostgreSQL query failed: {e}")
        return False


# --- Step 6: Verify document appears in History --------------------------------
def verify_history(token, doc_ids):
    headers = {"Authorization": f"Bearer {token}"}
    resp    = requests.get(f"{BASE_URL}/documents/history", headers=headers, timeout=15)
    if resp.status_code == 200:
        docs    = resp.json().get("documents", [])
        ids     = {d["id"] for d in docs}
        found   = [d for d in doc_ids if d in ids]
        missing = [d for d in doc_ids if d not in ids]
        print(f"[OK] History returned {len(docs)} document(s). Uploaded docs found: {len(found)}/{len(doc_ids)}")
        if missing:
            print(f"[WARN] Missing from history: {missing}")
        return docs
    print(f"[FAIL] History endpoint failed ({resp.status_code}): {resp.text[:200]}")
    return []


# --- Step 7: Verify download endpoint -----------------------------------------
def verify_download(token, doc_id, filename):
    headers = {"Authorization": f"Bearer {token}"}
    resp    = requests.get(f"{BASE_URL}/documents/{doc_id}/download", headers=headers, timeout=15)
    if resp.status_code == 200 and len(resp.content) > 0:
        print(f"[OK] Download '{filename}': {len(resp.content)} bytes received.")
        return True
    print(f"[FAIL] Download '{filename}' failed ({resp.status_code}): {resp.text[:200]}")
    return False


# --- Main ---------------------------------------------------------------------
def main():
    print("=" * 60)
    print("Document Workflow Verification")
    print("=" * 60)

    token = get_token()
    if not token:
        print("\n[ABORT] Cannot proceed without a valid token.")
        return

    test_files = [
        ("test_contract.pdf",
         b"%PDF-1.4 1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 612 792]>>endobj xref 0 4 trailer<</Size 4/Root 1 0 R>>startxref 9 %%EOF",
         "application/pdf"),
        ("test_agreement.docx",
         b"PK\x03\x04" + b"\x00" * 26 + b"[Content_Types].xml" + b"\x00" * 100,
         "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        ("test_terms.txt",
         b"TERMS AND CONDITIONS\nThis is a test legal document for LexGuard AI verification.",
         "text/plain"),
    ]

    doc_ids = {}
    print("\n--- Upload Tests ---")
    for filename, content, mime in test_files:
        doc_id = upload_file(token, filename, content, mime)
        if doc_id:
            doc_ids[filename] = doc_id

    print("\n--- Supabase Storage + PostgreSQL Verification ---")
    for filename, doc_id in doc_ids.items():
        verify_supabase(doc_id, filename)

    print("\n--- History Verification ---")
    verify_history(token, list(doc_ids.values()))

    print("\n--- Download Verification ---")
    for filename, doc_id in doc_ids.items():
        verify_download(token, doc_id, filename)

    print("\n" + "=" * 60)
    print(f"Summary: {len(doc_ids)}/3 documents uploaded successfully.")
    print("=" * 60)


if __name__ == "__main__":
    main()
