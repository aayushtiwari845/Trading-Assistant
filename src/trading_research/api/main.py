from __future__ import annotations

from datetime import datetime, timezone
from time import perf_counter
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI, HTTPException

from trading_research.agents.workflow import execute_research
from trading_research.logging_utils import configure_logging
from trading_research.schemas import ResearchRequest, ResearchResponse, ResearchResult

from .store import job_store

configure_logging()
app = FastAPI(title="Trading Research API", version="0.1.0")


def _run_job(request_id: str, request: ResearchRequest) -> None:
    started = perf_counter()
    try:
        state = execute_research(request)
        state.request_id = request_id
        job_store.update(
            request_id,
            {
                "status": "completed",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "result": ResearchResult(
                    request_id=request_id,
                    ticker=request.ticker.upper(),
                    status="completed",
                    state=state,
                    execution_time_seconds=round(perf_counter() - started, 2),
                    cost_estimate_usd=round(state.estimated_cost_usd, 6),
                ).model_dump(mode="json"),
            },
        )
    except Exception as exc:
        job_store.update(
            request_id,
            {
                "status": "failed",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "error": str(exc),
            },
        )


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Trading Research API", "version": "0.1.0"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/research", response_model=ResearchResponse)
def create_research(request: ResearchRequest, background_tasks: BackgroundTasks) -> ResearchResponse:
    request_id = str(uuid4())
    job_store.create(request_id, request.ticker.upper())
    background_tasks.add_task(_run_job, request_id, request)
    return ResearchResponse(
        request_id=request_id,
        status="running",
        ticker=request.ticker.upper(),
        message="Research started. Poll /api/research/{request_id} for completion.",
    )


@app.get("/api/research/{request_id}")
def get_research(request_id: str) -> dict:
    job = job_store.get(request_id)
    if not job:
        raise HTTPException(status_code=404, detail="Research request not found")
    return job
