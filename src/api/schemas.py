from pydantic import BaseModel
from typing import Optional, List, Dict,Any

class CaseCreateRequest(BaseModel):
  supplier_name:str

class CaseCreateResponse(BaseModel):
  case_id:str
  job_id:str
  status:str

class JobStatusResponse(BaseModel):
  job_id:str
  case_id:str
  status:str
  error_message:Optional[str] = None

class SSEEvent(BaseModel):
  event:str
  data:Dict[str,Any]


