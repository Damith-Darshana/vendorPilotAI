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






EXTRACTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a document extraction specialist. Your job is to find and extract specific values from the document text.

        CRITICAL RULES:
        1. You MUST extract the actual values from the document. Do NOT return null unless the field is genuinely absent.
        2. For company_name: look for "Company Name:", "Insured Name:", or similar labels.
        3. For registration_number: look for "Registration Number:", "Reg No:", or similar.
        4. For issue_date: look for "Issue Date:", "Effective Date:", or similar. Dates must be in YYYY-MM-DD format (e.g., 2024-01-01, not 20240101).
        5. For expiry_date: look for "Expiration Date:", "Expiry Date:", or similar. Dates must be in YYYY-MM-DD format (e.g., 2024-01-01, not 20240101).
        6. For insurance_limit: look for "Coverage Limit:", "Limit:", or similar. Return numbers only.
        7. For document_type: classify based on the document title.

        If you return null for a field that is clearly present in the text, you have failed the task."""),
            ("human", "Document text:\n{document_text}"),
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
    model= "openai/gpt-oss-20b",
    temperature = 0,
    api_key = os.getenv("GROQ_API_KEY"),
  ).with_structured_output(FlatExtractedDocument,method="json_schema", strict=True)

def _flat_to_nested(flat:FlatExtractedDocument) -> dict:
  """Convert Groq's flat output to the nested ExtractedDocument Shape"""
  def make_field(value,page):
    if value is None:
      return None
    return{
      "value": str(value),
      "evidence":{
        "page_number":page if isinstance(page,int) else (int(page) if page and str(page).isdigit() else 1),
        "text_snippet":"",
        "confidence_score":0.8,
      },

    }
  return{
      "document_type": flat.document_type,
      "company_name": make_field(flat.company_name, flat.company_name_page),
      "registration_number": make_field(flat.registration_number, flat.registration_number_page),
      "issue_date": make_field(flat.issue_date, flat.issue_date_page),
      "expiry_date": make_field(flat.expiry_date, flat.expiry_date_page),
      "insurance_limit": make_field(flat.insurance_limit, flat.insurance_limit_page),
  }


async def extract_async(file_path:str,provider:str="gemini"):
  """Extract structured fields from a PDF. returns Nested dict matching ExtractedDocument shape, a dict(JSON-safe)"""
  import pymupdf

  doc = pymupdf.open(file_path)
  full_text  = ""
  
  for page_num,page in enumerate(doc,start=1):
    text = page.get_text()
    full_text += f"\n---PAGE {page_num} ---\n{text}"
  doc.close()

  if not full_text.strip():
    raise ValueError(f"No text extracted from {file_path}")

  if provider == "gemini":
    model = _build_gemini()
    chain = EXTRACTION_PROMPT | model
    result = await chain.ainvoke({"document_text":full_text})
    return result.model_dump(mode="json")
  elif provider == "groq":
    model = _build_groq()
    chain = EXTRACTION_PROMPT | model
    result = await chain.ainvoke({"document_text":full_text})
    return _flat_to_nested(result)

  else:
    raise ValueError(f"Unknown Provider : {provider}")

