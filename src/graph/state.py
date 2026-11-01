from typing import TypedDict, Optional, List
from src.schemas import ExtractedDocument, Finding

class VendorPilotState(TypedDict,total=False):
  # inputs
  file_path: str
  case_id: str

  # intermediate results
  extracted_doc : Optional[ExtractedDocument]
  findings: List[Finding]

  # Routing flag
  requires_human_review:bool

  # human decision
  human_decision: Optional[str] # approved / rejected

  # Final status
  final_status: Optional[str]  # auto_approved / human_approved / human_rejected 

  error: Optional[str]

  