from __future__ import annotations

from typing import Any


class ResearchJobStore:
    def __init__(self):
        self._jobs: dict[str, dict[str, Any]] = {}

    def create(self, request_id: str, ticker: str) -> dict[str, Any]:
        job = {
            "request_id": request_id,
            "ticker": ticker,
            "status": "running",
            "message": "Research started.",
        }
        self._jobs[request_id] = job
        return job

    def update(self, request_id: str, payload: dict[str, Any]) -> None:
        self._jobs[request_id] = {**self._jobs.get(request_id, {}), **payload}

    def get(self, request_id: str) -> dict[str, Any] | None:
        return self._jobs.get(request_id)


job_store = ResearchJobStore()

