#an updated version of ExtractedDocument for async operations

import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from src.schemas import ExtractedDocument, FlatExtractedDocument

load_dotenv()
print("Groq key loaded:", bool(os.getenv("GROQ_API_KEY")))
print("Gemini key loaded:", bool(os.getenv("GOOGLE_API_KEY")))






EXTRACTION_PROMOT = ChatPromptTemplate.from_messages([
  ("system","""Extract the requested fields from the provided document text.
For each field, provide the exact text snippet that proves the value.
Page numbers start at 1. If a field is not present, set value to null.
Dates in YYYY-MM-DD format. Insurance limit: numeric only.
Classify document_type as: business_registration, insurance_certificate, tax_form, security_questionnaire, unknown.
Be conservative: if unsure, set confidence below 0.7."""),
("human","Document text: \n{document_text}"),
])

def _build_gemini():
  return ChatGoogleGenerativeAI(
    model = "gemini-3.8-flash",
    temperature=0,
    api_key = os.getenv("GOOGLE_API_KEY"),

  ).with_structured_output(ExtractedDocument,method="json_schema")

def _build_groq():
  #llama-3.3-70b-versatile does not support json_schema strict mode
  return ChatGroq(
    model= "qwen/qwen3.8-27b",
    temperature = 0,
    api_key = os.getenv("GROQ_API_KEY"),
  ).with_structured_output(FlatExtractedDocument,method="json_schema")

async def extract_async(file_path:str,provider:str="gemini"):
  """Extract structured fields from a PDF. returns a dict(JSON-safe)"""
  import fitz
  doc = fitz.open(file_path)
  full_text  = ""
  for page_num,page in enumerate(doc,start=1):
    text = page.get_text()
    full_text += f"\n---PAGE {page_num} ---\n{text}"
  doc.close()

  if not full_text.strip():
    raise ValueError(f"No text extracted from {file_path}")

  if provider == "gemini":
    model = _build_gemini()
  else:
    model = _build_groq()

  chain = EXTRACTION_PROMOT | model
  result = await chain.ainvoke({"document_text":full_text})
  if provider == "groq":
    flat = result
    return {
        "document_type": flat.document_type,
        "company_name": {"value": flat.company_name, "evidence": {"page_number": flat.company_name_page, "text_snippet": "", "confidence_score": 0.8} if flat.company_name_page else None},
        "registration_number": {"value": flat.registration_number, "evidence": {"page_number": flat.registration_number_page, "text_snippet": "", "confidence_score": 0.8} if flat.registration_number_page else None},
        "issue_date": {"value": flat.issue_date, "evidence": {"page_number": flat.issue_date_page, "text_snippet": "", "confidence_score": 0.8} if flat.issue_date_page else None},
        "expiry_date": {"value": flat.expiry_date, "evidence": {"page_number": flat.expiry_date_page, "text_snippet": "", "confidence_score": 0.8} if flat.expiry_date_page else None},
        "insurance_limit": {"value": flat.insurance_limit, "evidence": {"page_number": flat.insurance_limit_page, "text_snippet": "", "confidence_score": 0.8} if flat.insurance_limit_page else None},
    }
  return result.model_dump(mode="json")

