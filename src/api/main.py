import uuid
import json
import asyncio
from pathlib import Path
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from src.api.schemas import CaseCreateResponse, JobStatusResponse
from src.api.jobs import create_job, get_job_queue, resume_job
from src.db.database import SessionLocal
from src.db.models import Case, Job, Finding, Document as DocumentModel

from contextlib import asynccontextmanager
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from src.config import settings
from pydantic import BaseModel
from typing import Optional

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize checkpointer once at startup
    async with AsyncPostgresSaver.from_conn_string(settings.DATABASE_URL) as checkpointer:
        await checkpointer.setup()
        app.state.checkpointer = checkpointer
        yield

app = FastAPI(title="VendorPilot AI API", lifespan=lifespan)
# Add CORS middleware right after app initialization
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify ["http://localhost:3000", "http://10.4.2.2:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DecisionRequest(BaseModel):
    decision: str  # "approved" or "rejected"
    reviewer_notes: Optional[str] = None

class CaseDetailResponse(BaseModel):
    case_id: str
    supplier_name: str
    status: str
    findings: list
    created_at: str





UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@app.post("/api/v1/cases", response_model=CaseCreateResponse)
async def create_case(supplier_name: str = Form(...), file: UploadFile = File(...)):
    """
    Create a case, save the uploaded PDF, start background processing.
    Returns immediately with job_id.
    """
    case_id = f"case_{uuid.uuid4().hex[:8]}"

    # Save uploaded file
    file_path = UPLOAD_DIR / f"{case_id}_{file.filename}"
    content = await file.read()
    file_path.write_bytes(content)

    # Create case record
    db = SessionLocal()
    try:
        case = Case(id=case_id, supplier_name=supplier_name, status="queued")
        db.add(case)
   
        #adding the original PDF file as well to the db
        doc_record = DocumentModel(
            id=f"doc_{uuid.uuid4().hex[:8]}",
            case_id = case_id,
            filename = file_path.name,
        )
        db.add(doc_record)
        db.commit()
    except Exception:
        db.rollback()  
        raise
    finally:
        db.close()

    # Start background job
    job_id = create_job(case_id, str(file_path),app.state.checkpointer)

    return CaseCreateResponse(case_id=case_id, job_id=job_id, status="queued")


@app.get("/api/v1/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return JobStatusResponse(
            job_id=job.id,
            case_id=job.case_id,
            status=job.status,
            error_message=job.error_message,
        )
    finally:
        db.close()


@app.get("/api/v1/jobs/{job_id}/stream")
async def stream_job(job_id: str):
    """
    SSE endpoint: stream progress events for a job.
    Client connects once and receives frames until the queue sends None.
    """
    queue = get_job_queue(job_id)
    if not queue:
        raise HTTPException(status_code=404, detail="Job not found or already streamed")

    async def event_generator():
        while True:
            try:
                item = await asyncio.wait_for(queue.get(), timeout=30.0)
                if item is None:
                    break
                yield {
                    "event": item["event"],
                    "data": json.dumps(item["data"]),
                }
            except asyncio.TimeoutError:
                # Heartbeat to keep connection alive
                yield {"event": "heartbeat", "data": "{}"}

    return EventSourceResponse(event_generator())


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/v1/cases/{case_id}/decision")
async def submit_decision(case_id: str, body: DecisionRequest):
    """
    Submit a human decision for a paused case and resume the graph.
    """
    if body.decision not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="Decision must be 'approved' or 'rejected'")

    db = SessionLocal()
    try:
        # Find the most recent job for this case
        job = db.query(Job).filter(Job.case_id == case_id).order_by(Job.created_at.desc()).first()
        if not job:
            raise HTTPException(status_code=404, detail="No job found for this case")

        if job.status != "paused":
            raise HTTPException(status_code=400, detail=f"Job is not paused (current: {job.status})")

        job_id = job.id
    finally:
        db.close()

    # Start resume as background task
    asyncio.create_task(resume_job(job_id, case_id, body.decision, app.state.checkpointer))

    return {"status": "resuming", "job_id": job_id, "case_id": case_id}


@app.get("/api/v1/cases/{case_id}", response_model=CaseDetailResponse)
async def get_case(case_id: str):
    """Retrieve case details including findings."""
    db = SessionLocal()
    try:
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        findings = db.query(Finding).filter(Finding.case_id == case_id).all()
        findings_list = [
            {
                "id": f.id, 
                "field_name": f.field_name, 
                "severity": f.severity, 
                "message": f.message, 
                "rule_id": f.rule_id,
                "page_number":f.page_number,
            }
            for f in findings
        ]

        latest_job = db.query(Job).filter(Job.case_id == case_id).order_by(Job.created_at.desc()).first()
        job_status = latest_job.status if latest_job else None

        return CaseDetailResponse(
            case_id=case.id,
            supplier_name=case.supplier_name,
            status=case.status.value if hasattr(case.status, "value") else case.status,
            job_status = job_status,
            findings=findings_list,
            created_at=case.created_at.isoformat(),
        )
    finally:
        db.close()


from fastapi.responses import FileResponse

@app.get("/api/v1/cases/{case_id}/document")
async def get_case_document(case_id:str):
    """Return the Original PDF file for a case"""
    db = SessionLocal()
    try:

        doc = db.query(DocumentModel).filter(DocumentModel.case_id == case_id).first()

        if not doc:
            raise HTTPException(status_code=404, detail = " No document found for this case")

        file_path = Path("data/uploads")/doc.filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail = "File not found on disk")
        return FileResponse(path=str(file_path),media_type="application/pdf")
    finally:
        db.close()

