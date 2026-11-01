from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt,Command

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
  return {"findings":findings}

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
  has_critical = any(f.severity == FindingSeverity.CRITICAL for f in findings)

  if has_critical:
    return "human_review"

  return "auto_approve"

def auto_approve_node(state:VendorPilotState)->dict:
  """No critical issues; auto-complete"""

  return {"final_status":"auto_approved"}

def human_review_node(state: VendorPilotState) ->dict:
  """
    Pause and wait for human decision.
    Uses interrupt(); when resumed, the human input is injected.
  """
  decision = interrupt({
    "message":"Case requires human review",
    "findings":[
      {"severity":f.severity.value, "rule":f.rule_id,"message":f.message} for f in state.get("findings",[])

    ],
    "case_id":state.get("case_id"),
  })

  #when resumed, decision is the human input
  return {"human_decision":decision,"final_status":f"human_{decision}"}

# ---------------------------------------------------------
# Build Graph
# ---------------------------------------------------------

def build_graph():
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

  #checkpointer: in memory for now
  checkpointer = InMemorySaver()

  return builder.compile(checkpointer=checkpointer)

