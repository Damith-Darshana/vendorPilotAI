const API_BASE = "http://localhost:8000/api/v1";

export interface Finding{
  id:string;
  field_name:string;
  severity:string;
  message:string;
  rule_id:string;
  page_number:number | null;

}

export interface CaseDetail{
  case_id:string;
  supplier_name:string;
  status:string;
  job_status : string | null ;
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


export async function submitDecision(
    caseId:string,
    decision:"approved"| "rejected",
    notes?:string
  ):Promise<void> {
    const res = await fetch(`${API_BASE}/cases/${caseId}/decision`,{
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body: JSON.stringify({ decision, reviewer_notes: notes }),
    });
    if(!res.ok) throw new Error(`Decision failed: ${res.statusText}`);
  }

  