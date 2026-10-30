import uuid
from datetime import datetime, date
from typing import List
from src.schemas import ExtractedDocument, Finding, FindingSeverity


# Business ruled: which fields are mandatory for which document types
REQUIRED_FIELDS = {
  "business_registration": ["company_name","registration_number","issue_date"],
  "insurance_certificate":["company_name","expiry_date","insurance_limit"],
  "tax_form":["company_name","registration_number"],
}

def _create_finding(field_name:str,severity:FindingSeverity,message:str,rule_id:str)->Finding:
  return Finding(
    finding_id = f"find_{uuid.uuid4().hex[:8]}",
    field_name=field_name,
    severity = severity,
    message = message,
    rule_id=rule_id,
  )

def validate_document(doc:ExtractedDocument)->List[Finding]:
  """
    Deterministic validation. No LLM involved.
    Returns a list of findings (empty = clean).
  """
  findings: List[Finding] = []
  doc_type = doc.document_type

  # ---Rule 1: Missing required fields ----
  required = REQUIRED_FIELDS.get(doc_type,[])
  for field_name in required:
    field_obj = getattr(doc,field_name,None)
    if field_obj is None or field_obj.value is None or str(field_obj.value).strip()=="":
      findings.append(_create_finding(
        field_name=field_name,
        severity = FindingSeverity.HIGH,
        message = f"Required field '{field_name}' is missing for document type '{doc_type}'.",
        rule_id = "MISSING_REQUIRED_FIELD",
      ))

  # ---Rule 2: Expired document check ----
  if doc.expiry_date and doc.expiry_date.value:
    try:
      expiry = datetime.strptime(doc.expiry_date.value, "%Y-%m-%d").date()
      if expiry< date.today():
        findings.append(_create_finding(
          field_name="expiry_date",
          severity=FindingSeverity.CRITICAL,
          message=f"Document expired on {expiry.isoformat()}.Today is {date.today().isoformat()}.",
          rule_id="EXPIRED_DOCUMENT", 
        ))

    except ValueError:
      findings.append(_create_finding(
        field_name=field_name,
        severity=FindingSeverity.MEDIUM,
        message = f"Expiry date '{doc.expiry_date.value}' could not be parsed as YYYY-MM-DD.",
        rule_id = "INVALID_DATE_FORMAT",
      ))

  # --- Rule 3: Low confidence warning ---
  critical_fields = ["company_name", "registration_number", "expiry_date"]
  for field_name in critical_fields:
      field_obj = getattr(doc, field_name, None)
      if field_obj and field_obj.evidence:
          if field_obj.evidence.confidence_score < 0.7:
              findings.append(_create_finding(
                  field_name=field_name,
                  severity=FindingSeverity.MEDIUM,
                  message=f"Low confidence ({field_obj.evidence.confidence_score:.2f}) for '{field_name}'. Verify manually.",
                  rule_id="LOW_CONFIDENCE",
              ))

  return findings

  