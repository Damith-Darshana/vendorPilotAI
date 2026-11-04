import requests
import time

BASE = "http://localhost:8000"

# 1. Upload expired insurance
print("=" * 60)
print("1. Uploading expired insurance...")
print("=" * 60)

with open("data/sample_pdfs/doc_003_insurance_expired.pdf", "rb") as f:
    files = {"file": ("doc_003.pdf", f, "application/pdf")}
    data = {"supplier_name": "Apex Logistics Inc."}
    resp = requests.post(f"{BASE}/api/v1/cases", files=files, data=data)

case_data = resp.json()
case_id = case_data["case_id"]
job_id = case_data["job_id"]
print(f"Case: {case_id}, Job: {job_id}")

# 2. Wait for job to pause
print("\n" + "=" * 60)
print("2. Waiting for job to pause...")
print("=" * 60)

for _ in range(15):
    time.sleep(1)
    status = requests.get(f"{BASE}/api/v1/jobs/{job_id}").json()
    print(f"  Status: {status['status']}")
    if status["status"] == "paused":
        break

# 3. Check case details (findings should be persisted)
print("\n" + "=" * 60)
print("3. Case details:")
print("=" * 60)

case_detail = requests.get(f"{BASE}/api/v1/cases/{case_id}").json()
print(f"Supplier: {case_detail['supplier_name']}")
print(f"Status: {case_detail['status']}")
print(f"Findings: {len(case_detail['findings'])}")
for f in case_detail["findings"]:
    print(f"  [{f['severity'].upper()}] {f['rule_id']}: {f['message']}")

# 4. Submit approval
print("\n" + "=" * 60)
print("4. Submitting approval...")
print("=" * 60)

decision_resp = requests.post(
    f"{BASE}/api/v1/cases/{case_id}/decision",
    json={"decision": "approved", "reviewer_notes": "Expired insurance noted, but supplier provided updated certificate separately."}
)
print(f"Decision response: {decision_resp.json()}")

# 5. Wait for completion
print("\n" + "=" * 60)
print("5. Waiting for resume to complete...")
print("=" * 60)

for _ in range(15):
    time.sleep(1)
    status = requests.get(f"{BASE}/api/v1/jobs/{job_id}").json()
    print(f"  Status: {status['status']}")
    if status["status"] in ("completed", "failed"):
        break

# 6. Check final case status
print("\n" + "=" * 60)
print("6. Final case status:")
print("=" * 60)

final_case = requests.get(f"{BASE}/api/v1/cases/{case_id}").json()
print(f"Status: {final_case['status']}")