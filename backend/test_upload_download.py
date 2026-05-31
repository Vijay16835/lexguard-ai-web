import requests
import json
import time

url = "http://127.0.0.1:8001/api/v1"
body = {"email": "tvijay1098@gmail.com", "password": "1098Vijay"}
r = requests.post(f"{url}/auth/login", json=body)
token = r.json().get("access_token")

headers = {"Authorization": f"Bearer {token}"}

# Create a dummy pdf
with open("dummy.pdf", "wb") as f:
    f.write(b"%PDF-1.4\n1 0 obj\n<<\n/Title (Dummy PDF)\n>>\nendobj\ntrailer\n<<\n/Root 1 0 R\n>>\n%%EOF")

# Upload
files = {"file": ("dummy.pdf", open("dummy.pdf", "rb"), "application/pdf")}
print("Uploading...")
r = requests.post(f"{url}/documents/upload", headers=headers, files=files)
print("Upload status:", r.status_code)
print("Upload response:", r.json())
doc_id = r.json()["document"]["id"]

print("Waiting for AI analysis...")
time.sleep(5)

# Check history
r = requests.get(f"{url}/documents/history", headers=headers)
print("History Status:", r.status_code)
docs = r.json().get("documents", [])

for doc in docs:
    if doc.get("id") == doc_id:
        print(f"Found in history! Path: {doc.get('path')}")
        download_url = doc.get("path").replace("10.0.2.2", "127.0.0.1")
        print(f"Downloading from: {download_url}")
        r = requests.get(download_url, headers=headers)
        print("Download Status:", r.status_code)
        if r.status_code != 200:
            print("Download error:", r.json())
        break
