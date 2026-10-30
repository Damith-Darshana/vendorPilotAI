import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.extractors.document_extractor import extract_document
from src.validators.document_validator import validate_document

test_files = [
    "data/sample_pdfs/doc_001_registration.pdf",
    "data/sample_pdfs/doc_002_insurance_valid.pdf",
    "data/sample_pdfs/doc_003_insurance_expired.pdf",
]

for file_path in test_files:
    print(f"\n{'='*60}")
    print(f"Validating: {file_path}")
    print('='*60)

    doc = extract_document(file_path,use_fallback=True)
    findings = validate_document(doc)

    if not findings:
        print("✅ No findings. Document is clean.")
    else:
        for f in findings:
            print(f"[{f.severity.value.upper()}] {f.rule_id}: {f.message}")