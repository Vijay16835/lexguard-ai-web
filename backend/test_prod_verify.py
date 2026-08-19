import httpx
import time
import os
import sys

BASE_URL = 'https://pdd-uw63.onrender.com/api/v1'
print(f'Checking Production Render API: {BASE_URL}')

with httpx.Client(timeout=90.0) as client:
    # 1. Health check
    try:
        r = client.get(f'{BASE_URL}/auth/health')
        print(f'Health Check: HTTP {r.status_code} - {r.text}')
    except Exception as e:
        print(f'Health Check failed: {e}')

    # 2. Authenticate test user via google-auth
    print('Authenticating test user on prod via google-auth...')
    r_auth = client.post(f'{BASE_URL}/auth/google-auth', json={
        'firebase_uid': 'prod_verifier_uid_9999',
        'email': 'prod_verifier@example.com',
        'full_name': 'Production Verifier'
    })
    print(f'Google-auth status: {r_auth.status_code}')

    if r_auth.status_code != 200:
        print(f'Prod auth failed: {r_auth.text}')
        sys.exit(1)

    token = r_auth.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    print('Prod authenticated successfully!')

    # 3. Upload test files & poll for result
    test_files = [
        ('sample.pdf', 'application/pdf'),
        ('simple.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
        ('small.txt', 'text/plain'),
        ('sample.jpg', 'image/jpeg'),
        ('sample.png', 'image/png'),
    ]

    prod_results = {}

    for fname, mime in test_files:
        fpath = os.path.join('backend', 'test_files', fname)
        if not os.path.exists(fpath):
            fpath = os.path.join('test_files', fname)
        
        print(f'\n--- Prod Upload Test: {fname} ---')
        t0 = time.time()
        with open(fpath, 'rb') as f:
            up_res = client.post(f'{BASE_URL}/documents/upload', headers=headers, files={'file': (fname, f, mime)})
        print(f'Upload response HTTP {up_res.status_code}')
        
        if up_res.status_code == 200:
            doc_id = up_res.json()['document']['id']
            print(f'Document ID: {doc_id}. Polling status...')
            final_status = 'pending'
            err_msg = None
            for poll in range(45):
                time.sleep(2)
                st_res = client.get(f'{BASE_URL}/documents/{doc_id}/status', headers=headers)
                if st_res.status_code == 200:
                    st_data = st_res.json()
                    final_status = st_data.get('status')
                    err_msg = st_data.get('error_message')
                    print(f'[{poll+1}] Status: {final_status} | Error: {err_msg}')
                    if final_status in ('completed', 'failed'):
                        break
            
            elapsed = round(time.time() - t0, 2)
            prod_results[fname] = {
                'status': final_status,
                'elapsed': elapsed,
                'error': err_msg
            }
        else:
            prod_results[fname] = {
                'status': 'upload_failed',
                'elapsed': 0,
                'error': up_res.text
            }

    print('\n========================================')
    print(' LIVE RENDER PROD MATRIX RESULTS SUMMARY')
    print('========================================')
    for fname, res in prod_results.items():
        print(f"{fname:12s} | Status: {res['status']} | Time: {res['elapsed']}s | Error: {res['error']}")
