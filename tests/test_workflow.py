from trading_research.agents.workflow import execute_research
from trading_research.schemas import ResearchRequest


def test_execute_research_completes():
    result = execute_research(ResearchRequest(ticker="AAPL"))
    assert "report_generation" in result.completed_agents
    assert result.final_report_markdown.startswith("# Investment Research Report")
