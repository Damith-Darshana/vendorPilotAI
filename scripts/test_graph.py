import sys
from pathlib import Path
from langgraph.types import Command
sys.path.append(str(Path(__file__).parent.parent))

from src.graph.workflow import build_graph
app = build_graph()

print("=" * 60)
print("Test 1: Clean registration → expect auto_approved")
print("=" * 60)

config = {"configurable":{"thread_id":"test-clean-001"}}
result = app.invoke(
  {"file_path":"data/sample_pdfs/doc_001_registration.pdf","case_id":"case_001"},
  config = config,
)
print(f'Final status: {result.get("final_status")}')
print(f"Findings: {len(result.get('findings', []))}")

# Test 2: expired insurance → pause at human_review
print("\n" + "=" * 60)
print("Test 2: Expired insurance → expect pause at human_review")
print("=" * 60)

config2 = {"configurable": {"thread_id": "test-expired-002"}}
result2 = app.invoke(
    {"file_path": "data/sample_pdfs/doc_003_insurance_expired.pdf", "case_id": "case_002"},
    config=config2,
)
print(f"Interrupt triggered. Final status: {result2.get('final_status')}")

# Simulate human approval, resume graph
print("\nResuming with human decision: approved")
resumed = app.invoke(Command(resume="approved"), config=config2)
print(f"Resumed final status: {resumed.get('final_status')}")
print(f"Human decision: {resumed.get('human_decision')}")
