import pymupdf
import os

# Ensure the output directory exists
OUTPUT_DIR = "data/sample_pdfs"
os.makedirs(OUTPUT_DIR,exist_ok=True)

def create_pdf(filename,title,content_lines):
  pdf = pymupdf()
  pdf.add_page()
  pdf.set_font("Arial",size=12)

  #add title
  pdf.set_font("Arial","B",size=16)
  pdf.cell(200,10,txt=title,ln=True,align="C")
  pdf.ln(10)

  #Add content
  pdf.set_font("Arial",size=12)
  for line in content_lines:
    pdf.multi_cell(0,10,txt=line)
    pdf.ln(2)

  filepath= os.path.join(OUTPUT_DIR,filename)
  pdf.output(filepath)
  print(f"Generated: {filepath}")





create_pdf(
    "doc_001_registration.pdf",
    "CERTIFICATE OF INCORPORATION",
    [
        "Company Name: Northstar Industrial Supplies Ltd.",
        "Registration Number: REG-2023-88491",
        "Issue Date: January 15, 2023",
        "Jurisdiction: Delaware, USA",
        "This document certifies that the above company is legally registered."
    ]
)

# --- Document 2: Valid Insurance Certificate ---
create_pdf(
    "doc_002_insurance_valid.pdf",
    "CERTIFICATE OF LIABILITY INSURANCE",
    [
        "Insured Name: Northstar Industrial Supplies Ltd.",
        "Policy Number: POL-9921-AA",
        "Effective Date: February 1, 2024",
        "Expiration Date: February 1, 2027",
        "Coverage Limit: $2,000,000 USD",
        "This certificate confirms active general liability coverage."
    ]
)

# --- Document 3: Expired Insurance Certificate ---
create_pdf(
    "doc_003_insurance_expired.pdf",
    "CERTIFICATE OF LIABILITY INSURANCE",
    [
        "Insured Name: Apex Logistics Inc.",
        "Policy Number: POL-7712-BB",
        "Effective Date: January 1, 2022",
        "Expiration Date: Octobor 30, 2026",
        "Coverage Limit: $1,000,000 USD",
        "WARNING: This policy has expired."
    ]
)