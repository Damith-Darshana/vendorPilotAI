from pydantic import BaseModel, Field
from typing import List,Optional,Literal
from enum import Enum

# ---------------------------------------------------------
# 1. AI EXTRACTION SCHEMAS (What the LLM outputs)
# ---------------------------------------------------------


class SourceEvidence(BaseModel):
  page_number: int = Field(description="The page Number where this data as found. Starts at 1.")
  text_snippet:str = Field(description="The exact sntnce of phrase from the document that proves this field.")
  confidence_score:float = Field(description="Confidence from 0.0 to 1.0")

class ExtractedField(BaseModel):
  value: Optional[str] = Field(description = "The extracted value. Null if not found.")
  evidence: Optional[SourceEvidence] = Field(description="Where the value as found.")

class ExtractedDocument(BaseModel):
  document_type:Literal["business_registration","insurance_certificate","tax_form","security_questionnaire","unknown"] = Field(description = "The classification of the document.")
  company_name:ExtractedField = Field(description="The name of the supplier company.")
  registration_number:ExtractedField = Field(description="The business registration or tax ID number.")
  issue_date: ExtractedField = Field(description="The date the document was issued (YYYY-MM-DD).")
  expiry_date: ExtractedField = Field(description="The date the document expires (YYYY-MM-DD). Null if no expiry.")
  insurance_limit: ExtractedField = Field(description="The coverage amount in USD. Null if not applicable.")


class FlatExtractedDocument(BaseModel):
  """Flat schema for providers that struggle with nested models like Groq"""
  document_type:str = Field(description = "business_registration,insurance_certificate,tax_form,security_questionnaire,unknown")
  company_name:Optional[str] = Field(default=None,description="Company_name")
  registration_number: Optional[str] = Field(default=None, description="Registration or tax ID")
  issue_date: Optional[str] = Field(default=None, description="YYYY-MM-DD")
  expiry_date: Optional[str] = Field(default=None, description="YYYY-MM-DD, null if no expiry")
  insurance_limit: Optional[str] = Field(default=None, description="Numeric amount only")
  company_name_page: Optional[int] = Field(default=None, description="Page number where company_name was found")
  registration_number_page: Optional[int] = Field(default=None, description="Page number where registration_number was found")
  issue_date_page: Optional[int] = Field(default=None, description="Page number where issue_date was found")
  expiry_date_page: Optional[int] = Field(default=None, description="Page number where expiry_date was found")
  insurance_limit_page: Optional[int] = Field(default=None, description="Page number where insurance_limit was found")


# ---------------------------------------------------------
# 2. GOLDEN DATASET SCHEMA (What we manually write for testing)
# ---------------------------------------------------------

class GoldenDocument(BaseModel):
  document_id:str = Field(description="Unique ID for this file, e.g., doc_001")
  filename:str = Field(description = "The name of the PDF File")
  expected_document_type:str
  expected_fields: ExtractedDocument # we reuse the extraction schema for the expctd truth
  known_issue: List[str] = Field(description="e.g., 'expired_insurance','missing_tax_id','conflicting_name'")


class GoldenCase(BaseModel):
   case_id: str = Field(description="Unique ID for this test case, e.g., case_001")
   supplier_name: str
   description: str = Field(description="Brief explanation of what this test case checks")
   documents: List[GoldenDocument]


class FindingSeverity(str,Enum):
  CRITICAL = "critical"
  HIGH = "high"
  MEDIUM = "medium"
  LOW = "low"

class Finding(BaseModel):
  finding_id: str = Field(description = "Unique ID for this finding")
  field_name: str = Field(description="Which field triggered this, e.g., 'expiry_date")
  severity:FindingSeverity
  message:str = Field(description="Human-readable explanation")
  rule_id:str = Field(description = "Which determistic rule fired, e.g., 'EXPIRED_DATE'")

