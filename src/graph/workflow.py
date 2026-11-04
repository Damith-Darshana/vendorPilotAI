from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt,Command
from src.config import settings

from src.graph.state import VendorPilotState
from src.extractors.document_extractor import extract_document
from src.validators.document_validator import validate_document
from src.schemas import FindingSeverity


# ---------------------------------------------------------
# Nodes
# ---------------------------------------------------------

def extract_node(state: VendorPilotState) -> dict:
  """Node 1 : Extract structured data from PDF."""
  try:
    doc = extract_document(state["file_path"],use_fallback=True)
    return {"extracted_doc":doc,"error":None}
  except Exception as e:
    return {"error":str(e)}

def validate_node(state: VendorPilotState) -> dict:
  """Node 2: Run deterministic validation"""
  if state.get("error"):
    return {}
  findings = validate_document(state["extracted_doc"])
  findings_dicts = [
    {
      "finding_id":f.finding_id,
      "field_name":f.field_name,
      "severity":f.severity.value,
      "message":f.message,
      "rule_id":f.rule_id,

    }
    for f in findings
  ]
  return {"findings":findings_dicts}

def route_decision(state:VendorPilotState)->str:
  """
    Conditional routing:
    - Extraction error → human_review
    - CRITICAL finding → human_review
    - Otherwise → auto_approve
  """

  if state.get("error"):
    return "human_review"
  findings = state.get("findings",[])
  has_critical = any(f.get("severity") == "critical" for f in findings)
  return "human_review" if has_critical else "auto_approve"

def auto_approve_node(state:VendorPilotState)->dict:
  """No critical issues; auto-complete"""

  return {"final_status":"auto_approved"}



from src.db.database import SessionLocal
from src.db.models import AuditLog,Case,CaseStatus

def human_review_node(state: VendorPilotState) ->dict:
  """
    Pause and wait for human decision.
    Uses interrupt(); when resumed, the human input is injected.
  """
  decision = interrupt({
    "message":"Case requires human review",
    "findings": state.get("findings",[]),
    "case_id":state.get("case_id"),
  })
  db = SessionLocal()
  try:
    case_id = state.get("case_id")
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
      case = Case(id=case_id,supplier_name="unknown",status=CaseStatus.QUEUED)
      db.add(case)
      db.flush()

    log = AuditLog(
      case_id = case_id,
      actor = "human_reviewer",
      action = f"human_{decision}",
      details = {"findings_count":len(state.get("findings",[]))},

    )
    db.add(log)

    #update case status
    case.status = CaseStatus.APPROVED if decision =="approved" else CaseStatus.REJECTED
    db.commit()

  except Exception:
    db.rollback()
    raise

  finally:
    db.close()

  #when resumed, decision is the human input
  return {"human_decision":decision,"final_status":f"human_{decision}"}

# ---------------------------------------------------------
# Build Graph
# ---------------------------------------------------------

def build_graph(checkpointer):
  builder = StateGraph(VendorPilotState)

  #Add nodes
  builder.add_node("extract",extract_node)
  builder.add_node("validate",validate_node)
  builder.add_node("auto_approve",auto_approve_node)
  builder.add_node("human_review",human_review_node)

  #edges
  builder.add_edge(START,"extract")
  builder.add_edge("extract","validate")

  builder.add_conditional_edges(
    "validate",
    route_decision,
    {"auto_approve":"auto_approve", "human_review":"human_review"},
  )
  builder.add_edge("auto_approve",END)
  builder.add_edge("human_review",END)

 
  return builder.compile(checkpointer=checkpointer)


# def build_persistent_graph():
#     """Returns (app, checkpointer and context manager) using PostgresSaver. Caller must close checkpointer."""
#     checkpointer_context = PostgresSaver.from_conn_string(settings.DATABASE_URL)
#     checkpointer = checkpointer_context.__enter__()  # Manually enter context manager
#     checkpointer.setup()
#     app = build_graph(checkpointer=checkpointer)
#     return app, checkpointer, checkpointer_context  # Also return context for closing
   
