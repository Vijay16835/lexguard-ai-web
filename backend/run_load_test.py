import asyncio
import time
import json
import os
import sys
import math
import random
import io
import psutil
import aiohttp
import pandas as pd
import numpy as np
from datetime import datetime

# Configuration Constants
BASE_URL = "http://127.0.0.1:8000/api/v1"
CONCURRENT_VUS = 100
TEST_DURATION_SEC = 60
THINK_TIME_RANGE = (0.05, 0.2)  # Realistic think time between requests

# Sample test files in-memory
DUMMY_PDF_BYTES = b"%PDF-1.4\n1 0 obj\n<< /Title (Legal Contract) /Author (LexGuard) >>\nendobj\n2 0 obj\n<< /Type /Catalog /Pages 3 0 R >>\nendobj\n3 0 obj\n<< /Type /Pages /Count 1 /Kids [4 0 R] >>\nendobj\n4 0 obj\n<< /Type /Page /Parent 3 0 R /MediaBox [0 0 612 792] /Contents 5 0 R >>\nendobj\n5 0 obj\n<< /Length 120 >>\nstream\nBT\n/F1 12 Tf\n72 712 Td\n(THIS IS A CONFIDENTIAL MASTER SERVICES AGREEMENT BETWEEN PARTY A AND PARTY B.) Tj\nET\nendstream\nendobj\nxref\n0 6\n0000000000 65535 f\n0000000009 00000 n\n0000000074 00000 n\n0000000120 00000 n\n0000000179 00000 n\n0000000301 00000 n\ntrailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n470\n%%EOF\n"

class MetricsCollector:
    def __init__(self):
        self.records = []
        self.start_time = time.time()
        self.end_time = None
        self.bytes_sent = 0
        self.bytes_received = 0
        self.system_snapshots = []

    def record(self, endpoint, method, status, response_time_ms, bytes_sent, bytes_received, error_type=None):
        self.records.append({
            "timestamp": time.time() - self.start_time,
            "endpoint": endpoint,
            "method": method,
            "status": status,
            "response_time_ms": response_time_ms,
            "bytes_sent": bytes_sent,
            "bytes_received": bytes_received,
            "error_type": error_type
        })
        self.bytes_sent += bytes_sent
        self.bytes_received += bytes_received

    def snapshot_system(self):
        try:
            cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory().percent
            mem_mb = psutil.virtual_memory().used / (1024 * 1024)
            self.system_snapshots.append({
                "timestamp": time.time() - self.start_time,
                "cpu_percent": cpu,
                "mem_percent": mem,
                "mem_used_mb": mem_mb
            })
        except Exception:
            pass

collector = MetricsCollector()

async def system_monitor_loop(stop_event):
    psutil.cpu_percent(interval=None)
    while not stop_event.is_set():
        collector.snapshot_system()
        await asyncio.sleep(1.0)

async def simulate_vu(vu_id, session, stop_event):
    # Each VU creates/logs in a user
    email = f"loadtest_vu_{vu_id}_{random.randint(1000, 9999)}@lexguard-test.com"
    password = "TestPassword123!"
    full_name = f"Load Test User {vu_id}"
    
    auth_header = {}
    doc_id = None
    
    # 1. Login / Signup flow
    start_t = time.time()
    try:
        payload = {"email": email, "password": password}
        req_body = json.dumps(payload).encode('utf-8')
        async with session.post(f"{BASE_URL}/auth/login", json=payload) as resp:
            dur = (time.time() - start_t) * 1000
            resp_bytes = len(await resp.read())
            collector.record("/auth/login", "POST", resp.status, dur, len(req_body), resp_bytes, None if resp.status == 200 else "AuthFailure")
            if resp.status == 200:
                data = await resp.json()
                token = data.get("access_token")
                if token:
                    auth_header = {"Authorization": f"Bearer {token}"}
    except Exception as e:
        dur = (time.time() - start_t) * 1000
        collector.record("/auth/login", "POST", 0, dur, 0, 0, type(e).__name__)

    # Fallback default login if new account login failed
    if not auth_header:
        try:
            start_t = time.time()
            async with session.post(f"{BASE_URL}/auth/login", json={"email": "ad658a001@gmail.com", "password": "Password123!"}) as resp:
                dur = (time.time() - start_t) * 1000
                resp_bytes = len(await resp.read())
                collector.record("/auth/login", "POST", resp.status, dur, 50, resp_bytes, None if resp.status == 200 else "AuthFailure")
                if resp.status == 200:
                    data = await resp.json()
                    token = data.get("access_token")
                    if token:
                        auth_header = {"Authorization": f"Bearer {token}"}
        except Exception:
            pass

    # VU workload loop
    endpoints_pool = [
        ("GET", "/auth/health", False, None),
        ("POST", "/auth/refresh-token", False, None),
        ("GET", "/user/me", True, None),
        ("GET", "/user/profile/stats", True, None),
        ("PATCH", "/user/settings", True, {"theme": "dark", "notifications": True}),
        ("PUT", "/profile", True, {"full_name": f"Updated User {vu_id}"}),
        ("GET", "/notifications/", True, None),
        ("GET", "/documents/history", True, None),
    ]

    while not stop_event.is_set():
        await asyncio.sleep(random.uniform(*THINK_TIME_RANGE))
        
        # Pick scenario
        scenario_choice = random.choices(["user_api", "doc_upload", "doc_ai"], weights=[60, 20, 20])[0]
        
        if scenario_choice == "user_api" or not auth_header:
            method, ep, needs_auth, body = random.choice(endpoints_pool)
            headers = auth_header if needs_auth else {}
            start_t = time.time()
            try:
                url = f"{BASE_URL}{ep}"
                req_data = json.dumps(body).encode('utf-8') if body else b""
                if method == "GET":
                    async with session.get(url, headers=headers) as resp:
                        dur = (time.time() - start_t) * 1000
                        resp_bytes = len(await resp.read())
                        collector.record(ep, method, resp.status, dur, len(req_data), resp_bytes, None if resp.status < 400 else f"HTTP_{resp.status}")
                elif method == "POST":
                    async with session.post(url, headers=headers, json=body) as resp:
                        dur = (time.time() - start_t) * 1000
                        resp_bytes = len(await resp.read())
                        collector.record(ep, method, resp.status, dur, len(req_data), resp_bytes, None if resp.status < 400 else f"HTTP_{resp.status}")
                elif method == "PATCH":
                    async with session.patch(url, headers=headers, json=body) as resp:
                        dur = (time.time() - start_t) * 1000
                        resp_bytes = len(await resp.read())
                        collector.record(ep, method, resp.status, dur, len(req_data), resp_bytes, None if resp.status < 400 else f"HTTP_{resp.status}")
                elif method == "PUT":
                    async with session.put(f"{BASE_URL}/user/profile", headers=headers, json=body) as resp:
                        dur = (time.time() - start_t) * 1000
                        resp_bytes = len(await resp.read())
                        collector.record("/user/profile", method, resp.status, dur, len(req_data), resp_bytes, None if resp.status < 400 else f"HTTP_{resp.status}")
            except Exception as e:
                dur = (time.time() - start_t) * 1000
                collector.record(ep, method, 0, dur, 0, 0, type(e).__name__)

        elif scenario_choice == "doc_upload" and auth_header:
            start_t = time.time()
            try:
                data = aiohttp.FormData()
                data.add_field('file', DUMMY_PDF_BYTES, filename=f"contract_vu_{vu_id}.pdf", content_type='application/pdf')
                async with session.post(f"{BASE_URL}/documents/upload", headers=auth_header, data=data) as resp:
                    dur = (time.time() - start_t) * 1000
                    resp_bytes = len(await resp.read())
                    status_code = resp.status
                    collector.record("/documents/upload", "POST", status_code, dur, len(DUMMY_PDF_BYTES), resp_bytes, None if status_code < 400 else f"HTTP_{status_code}")
                    if status_code == 200:
                        res_json = await resp.json()
                        if res_json.get("document"):
                            doc_id = res_json["document"].get("id")
            except Exception as e:
                dur = (time.time() - start_t) * 1000
                collector.record("/documents/upload", "POST", 0, dur, len(DUMMY_PDF_BYTES), 0, type(e).__name__)

        elif scenario_choice == "doc_ai" and auth_header:
            if not doc_id:
                # fetch document from history if available
                try:
                    async with session.get(f"{BASE_URL}/documents/history", headers=auth_header) as resp:
                        if resp.status == 200:
                            h_json = await resp.json()
                            docs = h_json.get("documents", [])
                            if docs:
                                doc_id = random.choice(docs)["id"]
                except Exception:
                    pass

            if doc_id:
                ai_action = random.choice(["status", "get_doc", "chat", "summary", "clauses", "export"])
                start_t = time.time()
                try:
                    if ai_action == "status":
                        ep = f"/documents/{doc_id}/status"
                        async with session.get(f"{BASE_URL}{ep}", headers=auth_header) as resp:
                            dur = (time.time() - start_t) * 1000
                            resp_b = len(await resp.read())
                            collector.record("/documents/{id}/status", "GET", resp.status, dur, 0, resp_b, None if resp.status < 400 else f"HTTP_{resp.status}")
                    elif ai_action == "get_doc":
                        ep = f"/documents/{doc_id}"
                        async with session.get(f"{BASE_URL}{ep}", headers=auth_header) as resp:
                            dur = (time.time() - start_t) * 1000
                            resp_b = len(await resp.read())
                            collector.record("/documents/{id}", "GET", resp.status, dur, 0, resp_b, None if resp.status < 400 else f"HTTP_{resp.status}")
                    elif ai_action == "chat":
                        ep = "/ai/chat"
                        req_b = {"document_id": doc_id, "query": "What is the key liability clause in this document?"}
                        async with session.post(f"{BASE_URL}{ep}", headers=auth_header, json=req_b) as resp:
                            dur = (time.time() - start_t) * 1000
                            resp_b = len(await resp.read())
                            collector.record("/ai/chat", "POST", resp.status, dur, len(json.dumps(req_b)), resp_b, None if resp.status < 400 else f"HTTP_{resp.status}")
                    elif ai_action == "summary":
                        ep = f"/ai/summary/{doc_id}"
                        async with session.post(f"{BASE_URL}{ep}", headers=auth_header) as resp:
                            dur = (time.time() - start_t) * 1000
                            resp_b = len(await resp.read())
                            collector.record("/ai/summary/{id}", "POST", resp.status, dur, 0, resp_b, None if resp.status < 400 else f"HTTP_{resp.status}")
                    elif ai_action == "clauses":
                        ep = f"/ai/clauses/{doc_id}"
                        async with session.post(f"{BASE_URL}{ep}", headers=auth_header) as resp:
                            dur = (time.time() - start_t) * 1000
                            resp_b = len(await resp.read())
                            collector.record("/ai/clauses/{id}", "POST", resp.status, dur, 0, resp_b, None if resp.status < 400 else f"HTTP_{resp.status}")
                    elif ai_action == "export":
                        ep = f"/documents/{doc_id}/export?format=txt"
                        async with session.get(f"{BASE_URL}{ep}", headers=auth_header) as resp:
                            dur = (time.time() - start_t) * 1000
                            resp_b = len(await resp.read())
                            collector.record("/documents/{id}/export", "GET", resp.status, dur, 0, resp_b, None if resp.status < 400 else f"HTTP_{resp.status}")
                except Exception as e:
                    dur = (time.time() - start_t) * 1000
                    collector.record("/ai_feature", "REQUEST", 0, dur, 0, 0, type(e).__name__)

async def run_load_test():
    print(f"=== Starting LexGuard AI Backend Load Test ===")
    print(f"Target VUs: {CONCURRENT_VUS} | Duration: {TEST_DURATION_SEC}s | Base URL: {BASE_URL}")
    
    stop_event = asyncio.Event()
    collector.start_time = time.time()
    
    # Create asyncio connector with high connection limits
    conn = aiohttp.TCPConnector(limit=300, limit_per_host=300, ttl_dns_cache=300)
    timeout = aiohttp.ClientTimeout(total=30)
    
    async with aiohttp.ClientSession(connector=conn, timeout=timeout) as session:
        # Start system monitor
        monitor_task = asyncio.create_task(system_monitor_loop(stop_event))
        
        # Start VUs concurrently
        vu_tasks = [asyncio.create_task(simulate_vu(i, session, stop_event)) for i in range(CONCURRENT_VUS)]
        
        print("All 100 Virtual Users launched. Continuous request stream executing...")
        
        # Run test duration
        start_run = time.time()
        while time.time() - start_run < TEST_DURATION_SEC:
            elapsed = int(time.time() - start_run)
            req_count = len(collector.records)
            rps = req_count / max(1, elapsed)
            sys.stdout.write(f"\rProgress: {elapsed}/{TEST_DURATION_SEC}s | Total Requests: {req_count} | RPS: {rps:.1f}")
            sys.stdout.flush()
            await asyncio.sleep(1.0)
            
        print("\nStopping Virtual Users and gathering metrics...")
        stop_event.set()
        collector.end_time = time.time()
        
        await asyncio.gather(*vu_tasks, return_exceptions=True)
        monitor_task.cancel()

def analyze_and_generate_reports():
    df = pd.DataFrame(collector.records)
    total_duration = collector.end_time - collector.start_time
    total_requests = len(df)
    
    if total_requests == 0:
        print("ERROR: No requests recorded.")
        return

    successful_requests = len(df[df['status'].between(200, 299)])
    failed_requests = total_requests - successful_requests
    error_rate = (failed_requests / total_requests) * 100
    avg_rps = total_requests / total_duration
    
    resp_times = df['response_time_ms'].values
    min_rt = np.min(resp_times)
    avg_rt = np.mean(resp_times)
    max_rt = np.max(resp_times)
    p50_rt = np.percentile(resp_times, 50)
    p90_rt = np.percentile(resp_times, 90)
    p95_rt = np.percentile(resp_times, 95)
    p99_rt = np.percentile(resp_times, 99)
    
    data_sent_mb = collector.bytes_sent / (1024 * 1024)
    data_received_mb = collector.bytes_received / (1024 * 1024)
    tps = successful_requests / total_duration
    
    sys_df = pd.DataFrame(collector.system_snapshots)
    avg_cpu = sys_df['cpu_percent'].mean() if not sys_df.empty else 0
    max_cpu = sys_df['cpu_percent'].max() if not sys_df.empty else 0
    avg_mem = sys_df['mem_used_mb'].mean() if not sys_df.empty else 0
    max_mem = sys_df['mem_used_mb'].max() if not sys_df.empty else 0

    # API-wise metrics
    api_summary = []
    for endpoint, group in df.groupby('endpoint'):
        ep_total = len(group)
        ep_success = len(group[group['status'].between(200, 299)])
        ep_failed = ep_total - ep_success
        ep_err_rate = (ep_failed / ep_total) * 100
        ep_rts = group['response_time_ms'].values
        api_summary.append({
            "Endpoint": endpoint,
            "Method": group['method'].iloc[0],
            "Total Requests": ep_total,
            "Success Requests": ep_success,
            "Failed Requests": ep_failed,
            "Error Rate (%)": round(ep_err_rate, 2),
            "Min RT (ms)": round(np.min(ep_rts), 2),
            "Avg RT (ms)": round(np.mean(ep_rts), 2),
            "P95 RT (ms)": round(np.percentile(ep_rts, 95), 2),
            "P99 RT (ms)": round(np.percentile(ep_rts, 99), 2),
            "Max RT (ms)": round(np.max(ep_rts), 2),
            "RPS": round(ep_total / total_duration, 2)
        })
    api_df = pd.DataFrame(api_summary)

    # 1. Output JSON results
    json_results = {
        "metadata": {
            "application": "LexGuard AI – Legal Document Analyzer",
            "test_type": "Baseline Load Test",
            "timestamp": datetime.now().isoformat(),
            "virtual_users": CONCURRENT_VUS,
            "test_duration_seconds": round(total_duration, 2)
        },
        "summary": {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "requests_per_second": round(avg_rps, 2),
            "transactions_per_second": round(tps, 2),
            "error_rate_percent": round(error_rate, 4),
            "response_time_ms": {
                "min": round(min_rt, 2),
                "avg": round(avg_rt, 2),
                "max": round(max_rt, 2),
                "p50": round(p50_rt, 2),
                "p90": round(p90_rt, 2),
                "p95": round(p95_rt, 2),
                "p99": round(p99_rt, 2)
            },
            "throughput": {
                "data_sent_mb": round(data_sent_mb, 2),
                "data_received_mb": round(data_received_mb, 2),
                "total_throughput_mb": round(data_sent_mb + data_received_mb, 2)
            },
            "system_resources": {
                "avg_cpu_percent": round(avg_cpu, 2),
                "max_cpu_percent": round(max_cpu, 2),
                "avg_memory_mb": round(avg_mem, 2),
                "max_memory_mb": round(max_mem, 2)
            },
            "performance_rating": "EXCELLENT" if avg_rt < 500 and error_rate < 1.0 else "GOOD" if avg_rt < 1000 else "NEEDS_IMPROVEMENT"
        },
        "api_metrics": api_summary
    }

    output_json_path = os.path.join(os.getcwd(), "performance_results.json")
    with open(output_json_path, "w") as f:
        json.dump(json_results, f, indent=2)
    print(f"\n[Artifact Created] JSON Results: {output_json_path}")

    # 2. Output Excel Report (`Performance_Report.xlsx`)
    output_excel_path = os.path.join(os.getcwd(), "Performance_Report.xlsx")
    with pd.ExcelWriter(output_excel_path, engine='openpyxl') as writer:
        # Summary Sheet
        summary_data = [
            {"Metric": "Virtual Users (VUs)", "Value": CONCURRENT_VUS},
            {"Metric": "Test Duration (Seconds)", "Value": round(total_duration, 2)},
            {"Metric": "Total Requests Executed", "Value": total_requests},
            {"Metric": "Successful Requests", "Value": successful_requests},
            {"Metric": "Failed Requests", "Value": failed_requests},
            {"Metric": "Requests Per Second (RPS)", "Value": round(avg_rps, 2)},
            {"Metric": "Transactions Per Second (TPS)", "Value": round(tps, 2)},
            {"Metric": "Error Rate (%)", "Value": round(error_rate, 4)},
            {"Metric": "Minimum Response Time (ms)", "Value": round(min_rt, 2)},
            {"Metric": "Average Response Time (ms)", "Value": round(avg_rt, 2)},
            {"Metric": "P90 Response Time (ms)", "Value": round(p90_rt, 2)},
            {"Metric": "P95 Response Time (ms)", "Value": round(p95_rt, 2)},
            {"Metric": "P99 Response Time (ms)", "Value": round(p99_rt, 2)},
            {"Metric": "Maximum Response Time (ms)", "Value": round(max_rt, 2)},
            {"Metric": "Data Sent (MB)", "Value": round(data_sent_mb, 2)},
            {"Metric": "Data Received (MB)", "Value": round(data_received_mb, 2)},
            {"Metric": "Avg CPU Usage (%)", "Value": round(avg_cpu, 2)},
            {"Metric": "Avg Memory Usage (MB)", "Value": round(avg_mem, 2)},
            {"Metric": "Overall Performance Rating", "Value": json_results["summary"]["performance_rating"]}
        ]
        pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
        api_df.to_excel(writer, sheet_name='API Performance', index=False)
        df[['timestamp', 'endpoint', 'method', 'status', 'response_time_ms', 'bytes_sent', 'bytes_received', 'error_type']].head(5000).to_excel(writer, sheet_name='Raw Request Logs', index=False)
        sys_df.to_excel(writer, sheet_name='System Resources', index=False)
    print(f"[Artifact Created] Excel Performance Report: {output_excel_path}")

    # 3. Output HTML Performance Dashboard (`performance_dashboard.html`)
    output_html_path = os.path.join(os.getcwd(), "performance_dashboard.html")
    
    api_rows_html = ""
    for item in api_summary:
        status_badge = '<span style="color: #10b981; font-weight: bold;">PASS</span>' if item['Error Rate (%)'] < 1.0 else '<span style="color: #ef4444; font-weight: bold;">WARN</span>'
        api_rows_html += f"""
        <tr>
            <td style="font-weight: 600;">{item['Endpoint']}</td>
            <td><span class="method-badge">{item['Method']}</span></td>
            <td>{item['Total Requests']}</td>
            <td>{item['Success Requests']}</td>
            <td style="color: {'#ef4444' if item['Failed Requests'] > 0 else '#6b7280'};">{item['Failed Requests']}</td>
            <td>{item['Error Rate (%)']}%</td>
            <td>{item['Min RT (ms)']} ms</td>
            <td style="font-weight: 600; color: #3b82f6;">{item['Avg RT (ms)']} ms</td>
            <td>{item['P95 RT (ms)']} ms</td>
            <td>{item['P99 RT (ms)']} ms</td>
            <td>{item['RPS']}</td>
            <td>{status_badge}</td>
        </tr>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LexGuard AI – Backend Performance Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg: #0f172a;
            --card-bg: #1e293b;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent-blue: #38bdf8;
            --accent-green: #34d399;
            --accent-purple: #c084fc;
            --accent-red: #f87171;
            --border: #334155;
        }}
        body {{
            font-family: 'Inter', sans-serif;
            background-color: var(--bg);
            color: var(--text-main);
            margin: 0;
            padding: 30px;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--border);
            margin-bottom: 30px;
        }}
        .header h1 {{
            font-size: 28px;
            margin: 0;
            background: linear-gradient(135deg, #38bdf8, #818cf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .badge {{
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
            background: rgba(52, 211, 153, 0.15);
            color: var(--accent-green);
            border: 1px solid var(--accent-green);
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .card {{
            background: var(--card-bg);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid var(--border);
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        }}
        .card-title {{
            font-size: 13px;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }}
        .card-value {{
            font-size: 28px;
            font-weight: 700;
            color: var(--text-main);
        }}
        .card-sub {{
            font-size: 12px;
            color: var(--text-muted);
            margin-top: 6px;
        }}
        .section-title {{
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 16px;
            color: var(--accent-blue);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: var(--card-bg);
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid var(--border);
            margin-bottom: 30px;
        }}
        th, td {{
            padding: 14px 18px;
            text-align: left;
            font-size: 14px;
            border-bottom: 1px solid var(--border);
        }}
        th {{
            background: #111827;
            color: var(--text-muted);
            font-weight: 600;
            text-transform: uppercase;
            font-size: 12px;
        }}
        tr:hover {{
            background: rgba(255, 255, 255, 0.02);
        }}
        .method-badge {{
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 700;
            background: #334155;
            color: #cbd5e1;
        }}
        .recommendation-box {{
            background: var(--card-bg);
            border-left: 4px solid var(--accent-blue);
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
            border: 1px solid var(--border);
        }}
        .recommendation-box h3 {{
            margin-top: 0;
            color: var(--accent-blue);
        }}
        ul {{
            margin: 0;
            padding-left: 20px;
            color: var(--text-muted);
        }}
        li {{
            margin-bottom: 8px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1>LexGuard AI – Backend Performance Dashboard</h1>
            <div style="color: var(--text-muted); font-size: 14px; margin-top: 4px;">Execution Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        </div>
        <div class="badge">RATING: {json_results["summary"]["performance_rating"]}</div>
    </div>

    <div class="grid">
        <div class="card">
            <div class="card-title">Virtual Users</div>
            <div class="card-value" style="color: var(--accent-purple);">{CONCURRENT_VUS} VUs</div>
            <div class="card-sub">Concurrent Workload</div>
        </div>
        <div class="card">
            <div class="card-title">Requests / Sec (RPS)</div>
            <div class="card-value" style="color: var(--accent-blue);">{avg_rps:.1f}</div>
            <div class="card-sub">Continuous Generation</div>
        </div>
        <div class="card">
            <div class="card-title">Avg Response Time</div>
            <div class="card-value" style="color: #38bdf8;">{avg_rt:.1f} ms</div>
            <div class="card-sub">Target: &lt; 500 ms</div>
        </div>
        <div class="card">
            <div class="card-title">P95 Response Time</div>
            <div class="card-value" style="color: #facc15;">{p95_rt:.1f} ms</div>
            <div class="card-sub">Target: &lt; 1000 ms</div>
        </div>
        <div class="card">
            <div class="card-title">Total Requests</div>
            <div class="card-value">{total_requests:,}</div>
            <div class="card-sub">Completed Requests</div>
        </div>
        <div class="card">
            <div class="card-title">Error Rate</div>
            <div class="card-value" style="color: {'var(--accent-green)' if error_rate < 1.0 else 'var(--accent-red)'};">{error_rate:.2f}%</div>
            <div class="card-sub">Target: &lt; 1.0%</div>
        </div>
    </div>

    <div class="section-title">API Endpoint Performance Analysis</div>
    <table>
        <thead>
            <tr>
                <th>Endpoint</th>
                <th>Method</th>
                <th>Total Req</th>
                <th>Success</th>
                <th>Failed</th>
                <th>Error Rate</th>
                <th>Min RT</th>
                <th>Avg RT</th>
                <th>P95 RT</th>
                <th>P99 RT</th>
                <th>RPS</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
            {api_rows_html}
        </tbody>
    </table>

    <div class="section-title">System Resource Utilization & Throughput</div>
    <div class="grid">
        <div class="card">
            <div class="card-title">Data Transferred</div>
            <div class="card-value">{data_sent_mb + data_received_mb:.2f} MB</div>
            <div class="card-sub">Sent: {data_sent_mb:.2f} MB | Recv: {data_received_mb:.2f} MB</div>
        </div>
        <div class="card">
            <div class="card-title">CPU Utilization</div>
            <div class="card-value">{avg_cpu:.1f}%</div>
            <div class="card-sub">Max Peak: {max_cpu:.1f}%</div>
        </div>
        <div class="card">
            <div class="card-title">Memory Utilization</div>
            <div class="card-value">{avg_mem:.1f} MB</div>
            <div class="card-sub">Max Peak: {max_mem:.1f} MB</div>
        </div>
    </div>

    <div class="recommendation-box">
        <h3>Performance Bottlenecks & Optimization Recommendations</h3>
        <ul>
            <li><strong>Database Connection Pool Optimization:</strong> Enforce connection pooling with max size=50 in PostgreSQL to avoid thread blockages during concurrent uploads and user profile stats queries.</li>
            <li><strong>Asynchronous Task Offloading:</strong> Document text extraction and Groq AI analysis run as background tasks. Ensure Celery / Redis queue is enabled for extreme high-concurrency production deployments to prevent event loop delay.</li>
            <li><strong>Client-Side & Redis Caching:</strong> User profile stats (`/user/profile/stats`) and notifications should be cached with a 60-second TTL in Redis to eliminate redundant PostgreSQL queries during high load.</li>
        </ul>
    </div>
</body>
</html>
"""
    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"[Artifact Created] HTML Dashboard: {output_html_path}")

    # Summary Output to Console
    print("\n" + "="*60)
    print("        LEXGUARD AI - LOAD TEST EXECUTION SUMMARY")
    print("="*60)
    print(f"Total Virtual Users     : {CONCURRENT_VUS}")
    print(f"Total Test Duration     : {total_duration:.2f} seconds")
    print(f"Total Requests          : {total_requests:,}")
    print(f"Successful Requests     : {successful_requests:,}")
    print(f"Failed Requests         : {failed_requests:,}")
    print(f"Requests Per Second     : {avg_rps:.2f} req/sec")
    print(f"Transactions Per Sec    : {tps:.2f} tps")
    print(f"Error Rate              : {error_rate:.4f} %")
    print(f"Min Response Time       : {min_rt:.2f} ms")
    print(f"Average Response Time   : {avg_rt:.2f} ms")
    print(f"P50 Response Time       : {p50_rt:.2f} ms")
    print(f"P95 Response Time       : {p95_rt:.2f} ms")
    print(f"P99 Response Time       : {p99_rt:.2f} ms")
    print(f"Max Response Time       : {max_rt:.2f} ms")
    print(f"Data Sent / Received    : {data_sent_mb:.2f} MB / {data_received_mb:.2f} MB")
    print(f"Average CPU / Memory    : {avg_cpu:.1f}% / {avg_mem:.1f} MB")
    print(f"Overall Rating          : {json_results['summary']['performance_rating']}")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(run_load_test())
    analyze_and_generate_reports()
