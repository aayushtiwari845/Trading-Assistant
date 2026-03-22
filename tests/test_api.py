from trading_research.api.main import _build_result_summary
from trading_research.schemas import AgentResult, ResearchResult, ResearchStateModel


def test_build_result_summary_returns_compact_payload():
    state = ResearchStateModel(
        request_id="req-1",
        query="Research AAPL",
        ticker="AAPL",
        current_agent="FINISH",
        completed_agents=["data_collection", "report_generation"],
        report_generation=AgentResult(
            status="completed",
            payload={"markdown_path": "reports/AAPL_report.md", "pdf_path": "reports/AAPL_report.pdf"},
        ),
    )
    result = ResearchResult(
        request_id="req-1",
        ticker="AAPL",
        status="completed",
        state=state,
        execution_time_seconds=12.3,
        cost_estimate_usd=0.21,
    )

    summary = _build_result_summary(result.model_dump(mode="json"))

    assert summary.request_id == "req-1"
    assert summary.execution_time_seconds == 12.3
    assert summary.report_artifacts.markdown_path == "reports/AAPL_report.md"
    assert summary.completed_agents == ["data_collection", "report_generation"]
