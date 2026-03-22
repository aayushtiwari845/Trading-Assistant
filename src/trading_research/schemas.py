from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


AnalysisStatus = Literal["pending", "running", "completed", "failed"]


class ResearchRequest(BaseModel):
    ticker: str = Field(..., description="Ticker symbol such as AAPL")
    query: str | None = Field(default=None, description="Natural language research request")
    research_depth: Literal["quick", "standard", "deep"] = "standard"
    include_agents: list[str] | None = None


class AgentResult(BaseModel):
    status: AnalysisStatus = "pending"
    summary: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None


class ResearchStateModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    request_id: str
    query: str
    ticker: str
    research_depth: Literal["quick", "standard", "deep"] = "standard"
    research_plan: str = ""
    current_agent: str = "supervisor"
    completed_agents: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

    data_collection: AgentResult = Field(default_factory=AgentResult)
    fundamental_analysis: AgentResult = Field(default_factory=AgentResult)
    technical_analysis: AgentResult = Field(default_factory=AgentResult)
    sentiment_analysis: AgentResult = Field(default_factory=AgentResult)
    risk_assessment: AgentResult = Field(default_factory=AgentResult)
    report_generation: AgentResult = Field(default_factory=AgentResult)

    final_report_markdown: str = ""
    final_report_path: str | None = None
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None


class ResearchResponse(BaseModel):
    request_id: str
    status: AnalysisStatus
    ticker: str
    message: str


class ResearchResult(BaseModel):
    request_id: str
    ticker: str
    status: AnalysisStatus
    state: ResearchStateModel
    execution_time_seconds: float = 0.0
    cost_estimate_usd: float = 0.0


class ReportArtifacts(BaseModel):
    markdown_path: str | None = None
    pdf_path: str | None = None


class ResearchResultSummary(BaseModel):
    request_id: str
    ticker: str
    status: AnalysisStatus
    current_agent: str
    completed_agents: list[str] = Field(default_factory=list)
    execution_time_seconds: float = 0.0
    cost_estimate_usd: float = 0.0
    report_artifacts: ReportArtifacts = Field(default_factory=ReportArtifacts)


@dataclass
class CostLedger:
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    by_component: dict[str, float] = field(default_factory=dict)

    def add(self, component: str, tokens: int, cost_usd: float) -> None:
        self.total_tokens += tokens
        self.total_cost_usd += cost_usd
        self.by_component[component] = self.by_component.get(component, 0.0) + cost_usd
