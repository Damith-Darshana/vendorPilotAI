import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.extractors.document_extractor import extract_document


# Test on our sample PDFs
test_files = [
  "data/sample_pdfs/doc_001_registration.pdf",
  "data/sample_pdfs/doc_002_insurance_valid.pdf",
  "data/sample_pdfs/doc_003_insurance_expired.pdf",

]

for file_path in test_files:
    print(f"\n{'='*60}")
    print(f"Extracting: {file_path}\n")
    print('='*60)
    
    try:
        result = extract_document(file_path,use_fallback=True)
        print(f"Document Type: {result.document_type}")
        print(f"Company Name: {result.company_name.value}")
        print(f"  Evidence: page {result.company_name.evidence.page_number if result.company_name.evidence else 'N/A'}")
        print(f"Registration: {result.registration_number.value}")
        print(f"Issue Date: {result.issue_date.value}")
        print(f"Expiry Date: {result.expiry_date.value}")
        print(f"Insurance Limit: {result.insurance_limit.value}")
    except Exception as e:
        print(f" Broo ERROR: {e}")