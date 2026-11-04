import requests
import json

BASE = "http://localhost:8000"

# 1. Upload a PDF
print("=" * 60)
print("1. Uploading expired insurance PDF...")
print("=" * 60)

with open("data/sample_pdfs/doc_003_insurance_expired.pdf", "rb") as f:
    files = {"file": ("doc_003.pdf", f, "application/pdf")}
    data = {"supplier_name": "Apex Logistics Inc."}
    resp = requests.post(f"{BASE}/api/v1/cases", files=files, data=data)

print(f"Status: {resp.status_code}")
print(f"Response: {resp.json()}")

case_data = resp.json()
job_id = case_data["job_id"]

# 2. Check job status
print("\n" + "=" * 60)
print(f"2. Checking job status for {job_id}...")
print("=" * 60)

status_resp = requests.get(f"{BASE}/api/v1/jobs/{job_id}")
print(f"Status: {status_resp.json()}")

# 3. Stream SSE events (blocking read)
print("\n" + "=" * 60)
print("3. Streaming SSE events (Ctrl+C to stop)...")
print("=" * 60)

with requests.get(f"{BASE}/api/v1/jobs/{job_id}/stream", stream=True) as r:
    for line in r.iter_lines():
        if line:
            print(line.decode())