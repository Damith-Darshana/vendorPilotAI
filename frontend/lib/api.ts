const API_BASE = "http://localhost:8000/api/v1";

export interface Finding{
  id:string;
  field_name:string;
  severity:string;
  message:string;
  rule_id:string;

}

export interface CaseDetail{
  case_id:string;
  supplier_name:string;
  status:string;
  findings:Finding[];
  created_at:string;
}

export async function getCase(caseId:string): Promise<CaseDetail>{
  const res = await fetch(`${API_BASE}/cases/${caseId}`,{cache:"no-store"});
  if (!res.ok) throw new Error(`Failed to fetch case: ${res.statusText}` );
  return res.json();
}

export async function listCases(): Promise<CaseDetail[]>{
  return []; // we don't have a proper list endpoint yet in the v1
}