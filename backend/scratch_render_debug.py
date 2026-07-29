"""
Direct HTTP upload test against the Render production backend.
Simulates exactly what the Flutter app does:
  POST /api/v1/auth/login  -> get JWT
  POST /api/v1/documents/upload  (multipart) -> check response
"""
import sys, os, json, traceback
import urllib.request, urllib.parse

BASE_URL = "https://pdd-uw63.onrender.com/api/v1"
TEST_EMAIL = "debug_user@example.com"
TEST_PASSWORD = "Password@123"

def http_post_json(url, data):
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, method="POST",
                                  headers={"Content-Type": "application/json", "Accept": "application/json",
                                           "Origin": "http://localhost:3000"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.getcode(), json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())
    except Exception as ex:
        return None, str(ex)

print("=== RENDER PRODUCTION UPLOAD PIPELINE TEST ===\n")

# ── Step 1: Login ─────────────────────────────────────────────────────────────
print("Step 1: Login to Render backend...")
status, resp = http_post_json(f"{BASE_URL}/auth/login", {"email": TEST_EMAIL, "password": TEST_PASSWORD})
print(f"  Status: {status}")
if status == 200:
    token = resp.get("access_token")
    print(f"  Token obtained: {bool(token)}")
    print(f"  User ID: {resp.get('user', {}).get('id')}")
else:
    print(f"  Login failed: {resp}")
    token = None

if not token:
    print("\nCannot continue without a token. Check if user exists on Render.")
    sys.exit(1)

# ── Step 2: Upload sample.png via multipart ───────────────────────────────────
print("\nStep 2: Uploading sample.png to Render /documents/upload...")

# Build a minimal multipart/form-data request manually
file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_files", "sample.png")
if not os.path.exists(file_path):
    print(f"  ERROR: test file not found at {file_path}")
    sys.exit(1)

with open(file_path, "rb") as f:
    file_bytes = f.read()

boundary = "----FlutterFormBoundary7MA4YWxkTrZu0gW"
body_parts = []
body_parts.append(f"--{boundary}\r\n".encode())
body_parts.append(f'Content-Disposition: form-data; name="file"; filename="sample.png"\r\n'.encode())
body_parts.append(b"Content-Type: image/png\r\n\r\n")
body_parts.append(file_bytes)
body_parts.append(f"\r\n--{boundary}--\r\n".encode())
body = b"".join(body_parts)

req = urllib.request.Request(
    f"{BASE_URL}/documents/upload",
    data=body,
    method="POST",
    headers={
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Authorization": f"Bearer {token}",
        "Origin": "http://localhost:3000",
        "Accept": "application/json",
    }
)

try:
    with urllib.request.urlopen(req, timeout=60) as r:
        upload_status = r.getcode()
        upload_resp = r.read().decode()
        print(f"  Upload Status: {upload_status}")
        print(f"  Upload Response: {upload_resp}")
except urllib.error.HTTPError as e:
    print(f"  Upload HTTPError Status: {e.code}")
    print(f"  Upload Error Body: {e.read().decode()}")
except Exception as ex:
    print(f"  Upload Exception: {type(ex).__name__}: {ex}")
    traceback.print_exc()
