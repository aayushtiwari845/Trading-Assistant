from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import FileResponse

from trading_research.agents.workflow import execute_research
from trading_research.logging_utils import configure_logging
from trading_research.schemas import (
    ReportArtifacts,
    ResearchRequest,
    ResearchResponse,
    ResearchResult,
    ResearchResultSummary,
)

from .store import job_store

configure_logging()
app = FastAPI(title="Trading Research API", version="0.1.0")


def _build_result_summary(result_payload: dict) -> ResearchResultSummary:
    result = ResearchResult.model_validate(result_payload)
    report_payload = result.state.report_generation.payload
    return ResearchResultSummary(
        request_id=result.request_id,
        ticker=result.ticker,
        status=result.status,
        current_agent=result.state.current_agent,
        completed_agents=result.state.completed_agents,
        execution_time_seconds=result.execution_time_seconds,
        cost_estimate_usd=result.cost_estimate_usd,
        report_artifacts=ReportArtifacts(
            markdown_path=report_payload.get("markdown_path"),
            pdf_path=report_payload.get("pdf_path"),
        ),
    )


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
    compact_job = {key: value for key, value in job.items() if key != "result"}
    if job.get("result"):
        compact_job["summary"] = _build_result_summary(job["result"]).model_dump(mode="json")
    return compact_job


@app.get("/api/research/{request_id}/full")
def get_research_full(request_id: str) -> dict:
    job = job_store.get(request_id)
    if not job:
        raise HTTPException(status_code=404, detail="Research request not found")
    return job


def _serve_report(request_id: str, report_key: str, media_type: str, filename_suffix: str) -> FileResponse:
    job = job_store.get(request_id)
    if not job or not job.get("result"):
        raise HTTPException(status_code=404, detail="Research result not found")

    report_payload = job["result"]["state"]["report_generation"]["payload"]
    report_path = report_payload.get(report_key)
    if not report_path:
        raise HTTPException(status_code=404, detail="Requested report artifact is unavailable")

    resolved_path = Path(report_path)
    if not resolved_path.is_absolute():
        resolved_path = Path.cwd() / resolved_path
    if not resolved_path.exists():
        raise HTTPException(status_code=404, detail="Requested report artifact was not found on disk")

    ticker = job["result"]["ticker"]
    return FileResponse(
        path=resolved_path,
        media_type=media_type,
        filename=f"{ticker}_{filename_suffix}",
    )


@app.get("/api/research/{request_id}/report/markdown")
def download_markdown_report(request_id: str) -> FileResponse:
    return _serve_report(request_id, "markdown_path", "text/markdown", "report.md")


@app.get("/api/research/{request_id}/report/pdf")
def download_pdf_report(request_id: str) -> FileResponse:
    return _serve_report(request_id, "pdf_path", "application/pdf", "report.pdf")
