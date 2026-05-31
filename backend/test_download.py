import requests
import json
import time

url = "http://127.0.0.1:8001/api/v1"
body = {"email": "tvijay1098@gmail.com", "password": "1098Vijay"}
r = requests.post(f"{url}/auth/login", json=body)
token = r.json().get("access_token")

headers = {"Authorization": f"Bearer {token}"}
r = requests.get(f"{url}/documents/history", headers=headers)
docs = r.json().get("documents", [])

if docs:
    doc = docs[0]
    download_url = doc.get("path").replace("10.0.2.2", "127.0.0.1")
    
    r = requests.get(download_url, headers=headers)
    print("Download Status:", r.status_code)
    print("Response JSON:", r.json())
