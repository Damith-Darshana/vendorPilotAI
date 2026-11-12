import asyncio
import json
import time
import traceback
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

sys.path.append(str(Path(__file__).parent.parent))

from src.evaluation.async_extractor import extract_async
from src.validators.document_validator import validate_document
from src.schemas import ExtractedDocument

DATASET_DIR = Path("data/golden_dataset")
SEMAPHORE = asyncio.Semaphore(5)  # 5 concurrent cases, safe for Gemini 15 RPM & Groq 30 RPM

@dataclass
class CaseResult:
    case_id: str
    provider_used: str = "unknown"
    latency_ms: float = 0
    extraction_correct: bool = False
    findings_expected: list = field(default_factory=list)
    findings_actual: list = field(default_factory=list)
    outcome_expected: str = ""
    outcome_actual: str = ""
    error: Optional[str] = None
    extracted_fields: dict = field(default_factory=dict)

async def run_baseline(case: dict, doc: dict):
    """Single LLM call, no validation, no routing. Only extraction."""
    async with SEMAPHORE:
        start = time.time()
        try:
            extracted = await extract_async(doc["file_path"], provider="gemini")
            latency = (time.time() - start) * 1000
            return extracted, "gemini", latency, None
        except Exception as e:
            print(f"[BASELINE Gemini failed] {case['case_id']}: {e}")
            traceback.print_exc()
            # Fallback to Groq
            try:
                extracted = await extract_async(doc["file_path"], provider="groq")
                latency = (time.time() - start) * 1000
                return extracted, "groq_fallback", latency, None
            except Exception as e2:
                return None, "failed", 0, str(e2)

async def run_agentic(case: dict, doc: dict):
    """Full pipeline: extract → validate → route."""
    async with SEMAPHORE:
        start = time.time()
        try:
            extracted = await extract_async(doc["file_path"], provider="gemini")
            provider = "gemini"
        except Exception:
            try:
                extracted = await extract_async(doc["file_path"], provider="groq")
                provider = "groq_fallback"
            except Exception as e:
                print(f"[AGENTIC Groq failed] {case['case_id']}: {e}")
                traceback.print_exc()
                return None, [], "failed", 0, str(e)

        latency = (time.time() - start) * 1000

        # Validate
        doc_obj = ExtractedDocument(**extracted)
        findings = validate_document(doc_obj)
        findings_dicts = [
            {"rule_id": f.rule_id, "severity": f.severity.value} for f in findings
        ]

        # Route
        has_critical = any(f.severity.value == "critical" for f in findings)
        outcome = "human_review" if has_critical else "auto_approved"

        return extracted, findings_dicts, provider, latency, None

def compare_fields(expected: dict, actual: dict) -> dict:
    """Compare expected vs actual fields. Returns per-field correctness."""
    results = {}
    for field in ["company_name", "registration_number", "issue_date", "expiry_date", "insurance_limit"]:
        exp_val = expected.get(field)
        act_field = actual.get(field, {})
        act_val = act_field.get("value") if isinstance(act_field, dict) else None
        results[field] = (str(exp_val).strip() if exp_val else None) == (str(act_val).strip() if act_val else None)
    return results

async def main():
    case_files = sorted(DATASET_DIR.glob("eval_*.json"))
    print(f"Found {len(case_files)} cases")

    results_baseline = []
    results_agentic = []

    for cf in case_files:
        with open(cf) as f:
            case = json.load(f)

        # Each case has exactly one document in our dataset
        doc = case["documents"][0]

        print(f"Running {case['case_id']}...")
        # Baseline
        extracted_b, provider_b, lat_b, err_b = await run_baseline(case, doc)
        br = CaseResult(case_id=case["case_id"], provider_used=provider_b, latency_ms=lat_b, error=err_b)
        if extracted_b:
            br.extraction_correct = all(compare_fields(doc["expected_fields"], extracted_b).values())
            br.extracted_fields = {k: v.get("value") for k, v in extracted_b.items() if isinstance(v, dict) and "value" in v}
        results_baseline.append(br)

        # Agentic
        extracted_a, findings_a, provider_a, lat_a, err_a = await run_agentic(case, doc)
        ar = CaseResult(case_id=case["case_id"], provider_used=provider_a, latency_ms=lat_a, error=err_a)
        if extracted_a:
            ar.extraction_correct = all(compare_fields(doc["expected_fields"], extracted_a).values())
            ar.findings_actual = findings_a
            ar.findings_expected = case["expected_findings"]
            ar.outcome_expected = case["expected_outcome"]
            has_critical = any(f["severity"] == "critical" for f in findings_a)
            ar.outcome_actual = "human_review" if has_critical else "auto_approved"
            ar.extracted_fields = {k: v.get("value") for k, v in extracted_a.items() if isinstance(v, dict) and "value" in v}
        results_agentic.append(ar)

    # Print summary
    print("\n" + "="*60)
    print("BASELINE SUMMARY")
    print("="*60)
    correct_b = sum(1 for r in results_baseline if r.extraction_correct)
    print(f"Extraction accuracy: {correct_b}/{len(results_baseline)}")
    providers_b = {}
    for r in results_baseline:
        providers_b[r.provider_used] = providers_b.get(r.provider_used, 0) + 1
    print(f"Provider usage: {providers_b}")

    print("\n" + "="*60)
    print("AGENTIC SUMMARY")
    print("="*60)
    correct_a = sum(1 for r in results_agentic if r.extraction_correct)
    print(f"Extraction accuracy: {correct_a}/{len(results_agentic)}")
    providers_a = {}
    for r in results_agentic:
        providers_a[r.provider_used] = providers_a.get(r.provider_used, 0) + 1
    print(f"Provider usage: {providers_a}")

    # Finding metrics
    tp = fp = fn = 0
    for r in results_agentic:
        expected_rules = {f["rule_id"] for f in r.findings_expected}
        actual_rules = {f["rule_id"] for f in r.findings_actual}
        tp += len(expected_rules & actual_rules)
        fp += len(actual_rules - expected_rules)
        fn += len(expected_rules - actual_rules)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    print(f"Finding detection: precision={precision:.2f}, recall={recall:.2f}, f1={f1:.2f}")

    # Outcome accuracy
    outcome_correct = sum(1 for r in results_agentic if r.outcome_expected == r.outcome_actual)
    print(f"Outcome accuracy: {outcome_correct}/{len(results_agentic)}")

    # Write markdown report
    report = f"""# VendorPilot AI Evaluation Report

## Dataset
- 20 cases across 6 scenario families

## Provider Usage

| Pipeline | Gemini | Groq Fallback | Failed |
|----------|--------|---------------|--------|
| Baseline | {providers_b.get('gemini', 0)} | {providers_b.get('groq_fallback', 0)} | {providers_b.get('failed', 0)} |
| Agentic | {providers_a.get('gemini', 0)} | {providers_a.get('groq_fallback', 0)} | {providers_a.get('failed', 0)} |

## Extraction Accuracy
- Baseline: {correct_b}/{len(results_baseline)} ({100*correct_b/len(results_baseline):.0f}%)
- Agentic: {correct_a}/{len(results_agentic)} ({100*correct_a/len(results_agentic):.0f}%)

## Finding Detection (Agentic)
- Precision: {precision:.2f}
- Recall: {recall:.2f}
- F1: {f1:.2f}

## Outcome Accuracy (Agentic)
- {outcome_correct}/{len(results_agentic)} cases routed correctly
"""
    with open("data/evaluation_report.md", "w") as f:
        f.write(report)
    print("\nReport written to data/evaluation_report.md")

if __name__ == "__main__":
    asyncio.run(main())