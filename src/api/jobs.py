import uuid
import json
import asyncio
from datetime import datetime
from typing import Optional
from src.db.database import SessionLocal
from src.db.models import Job, Case, CaseStatus
from src.graph.workflow import build_graph
from langgraph.types import Command


# In-memory registry of running jobs and their SSE queues
# Key: job_id, Value: asyncio.Queue for SSE frames
_job_queues: dict[str, asyncio.Queue] = {}
_job_tasks: dict[str, asyncio.Task] = {}

async def run_case_job(job_id: str, case_id: str, file_path: str, checkpointer):
    """
    Background task: run the LangGraph for a case, emit SSE events.
    """
    queue = _job_queues.get(job_id)
    if not queue:
        return

    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = "running"
            db.commit()

        await queue.put({"event": "job_started", "data": {"job_id": job_id, "case_id": case_id}})

        # Build graph using the app's checkpointer
        app = build_graph(checkpointer=checkpointer)

        config = {"configurable": {"thread_id": case_id}}

        try:
            result = await app.ainvoke(
                {"file_path": file_path, "case_id": case_id},
                config=config,
            )

            if result.get("__interrupt__"):
                await queue.put({
                    "event": "hitl_required",
                    "data": {"message": "Case requires human review", "case_id": case_id}
                })
                if job:
                    job.status = "paused"
                    db.commit()
            else:
                final_status = result.get("final_status", "completed")
                await queue.put({
                    "event": "job_completed",
                    "data": {"final_status": final_status, "case_id": case_id}
                })
                if job:
                    job.status = "completed"
                    db.commit()

        except Exception as e:
            if job:
                job.status = "failed"
                job.error_message = str(e)
                db.commit()
            await queue.put({"event": "error", "data": {"message": str(e)}})

    finally:
        db.close()
        await queue.put(None)


def create_job(case_id: str, file_path: str, checkpointer) -> str:
    """Create a job record and start the background task. Returns job_id."""
    job_id = f"job_{uuid.uuid4().hex[:12]}"

    db = SessionLocal()
    try:
        job = Job(id=job_id, case_id=case_id, status="queued")
        db.add(job)
        db.commit()
    finally:
        db.close()

    queue = asyncio.Queue()
    _job_queues[job_id] = queue

    task = asyncio.create_task(run_case_job(job_id, case_id, file_path, checkpointer))
    _job_tasks[job_id] = task

    return job_id


def get_job_queue(job_id: str) -> Optional[asyncio.Queue]:
    return _job_queues.get(job_id)


async def resume_job(job_id:str, case_id:str,decision:str,checkpointer):
    """
    Resume a paused graph with a human decision.
    Emits SSE events as the graph continues to completion.
    """

    queue = _job_queues.get(job_id)
    if not queue:
        # Queue was closed create a new one for this resume
        queue = asyncio.Queue()
        _job_queues[job_id] = queue

    db = SessionLocal()

    try:
        job = db.query(Job).filter(Job.id==job_id).first()
        if not job:
            await queue.put({"event":"error","data":{"message":"Job not found"}})
            await queue.put(None)
            return

        job.status = "running"
        db.commit()

        await queue.put({"event":"resuming","data":{"case_id":case_id,"decision":decision}})
        app = build_graph(checkpointer= checkpointer)
        config = {"configurable":{"thread_id":case_id}}

        try:
            result = await app.ainvoke(Command(resume=decision),config = config)

            final_status = result.get("final_status","unknown")
            await queue.put({
                "event":"job_completed",
                "data":{"final_status":final_status,"case_id":case_id}
            })
            job.status = "completed"
            db.commit()


        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            db.commit()
            await queue.put({"event":"error","data":{"mesage":str(e)}})

    finally :
        db.close()
        await queue.put(None)

















