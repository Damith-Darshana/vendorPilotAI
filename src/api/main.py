import uuid
import json
import asyncio
from pathlib import Path
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from src.api.schemas import CaseCreateResponse, JobStatusResponse
from src.api.jobs import create_job, get_job_queue
from src.db.database import SessionLocal
from src.db.models import Case, Job

from contextlib import asynccontextmanager
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from src.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize checkpointer once at startup
    async with AsyncPostgresSaver.from_conn_string(settings.DATABASE_URL) as checkpointer:
        await checkpointer.setup()
        app.state.checkpointer = checkpointer
        yield

app = FastAPI(title="VendorPilot AI API", lifespan=lifespan)

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
        db.commit()
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