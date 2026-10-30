import os
from pathlib import Path
from langchain.chat_models import init_chat_model
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import Optional, Literal

# Import our schemas
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from src.schemas import ExtractedDocument
from src.config import Settings

# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------
PRIMARY_PROVIDER = "google_genai"
PRIMARY_MODEL = "gemini-3.8-flash"

FALLBACK_PROVIDER = "groq"
FALLBACK_MODEL = "llama-3.3-70b-versatile"

def get_extraction_model(use_fallback: bool = False):
    """
    Returns a model configured for structured output extraction.
    Primary: Gemini (better long-context + structured output)
    Fallback: Groq (faster, but structured output limitations)
    """
    if use_fallback:
        # Groq fallback - note: strict structured output has limitations
        # but works for pure extraction (no tools in same call)
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=FALLBACK_MODEL,
            temperature=0,
            api_key=Settings.GROQ_API_KEY,
        ).with_structured_output(ExtractedDocument)
    else:
        # Primary: Gemini
        return ChatGoogleGenerativeAI(
            model=PRIMARY_MODEL,
            temperature=0,
            api_key=Settings.GOOGLE_API_KEY,
        ).with_structured_output(ExtractedDocument)


# ---------------------------------------------------------
# Extraction prompt
# ---------------------------------------------------------
EXTRACTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a document extraction specialist for supplier onboarding.

Extract the requested fields from the provided document text.

RULES:
- For each field, provide the exact text snippet from the document that proves the value.
- Page numbers start at 1.
- If a field is not present, set value to null and evidence to null.
- For dates, use YYYY-MM-DD format.
- For insurance_limit, extract the numeric amount only (no currency symbols).
- Classify document_type as one of: business_registration, insurance_certificate, tax_form, security_questionnaire, unknown.
- Be conservative: if you are unsure, set confidence_score below 0.7 and flag it.

Document text:
{document_text}
"""),
    ("human", "Extract the structured fields from this document."),
])


# ---------------------------------------------------------
# Extraction function
# ---------------------------------------------------------
def extract_document(file_path: str, use_fallback: bool = False) -> ExtractedDocument:
    """
    Extract structured fields from a PDF file.
    
    Note: For simplicity, we're reading PDF text via a basic method.
    In production, use a proper PDF loader (PyPDFLoader from langchain_community).
    """
    from fpdf import FPDF  # We'll use a simple text extraction for now
    
    # For now, read the PDF as text (fpdf2-generated PDFs are simple)
    # In the next iteration, we'll add proper PDF parsing
    import fitz  # PyMuPDF - we'll add this to requirements
    
    doc = fitz.open(file_path)
    full_text = ""
    for page_num, page in enumerate(doc, start=1):
        text = page.get_text()
        full_text += f"\n--- PAGE {page_num} ---\n{text}"
    doc.close()
    
    if not full_text.strip():
        raise ValueError(f"No text could be extracted from {file_path}")
    
    # Get model with structured output
    model = get_extraction_model(use_fallback=use_fallback)
    
    # Build and invoke chain
    chain = EXTRACTION_PROMPT | model
    result = chain.invoke({"document_text": full_text})
    
    return result