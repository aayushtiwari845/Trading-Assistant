from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, TypedDict
import uuid

from trading_research.analytics.fundamental import calculate_financial_ratios
from trading_research.analytics.risk import calculate_risk_metrics
from trading_research.analytics.sentiment import aggregate_news_sentiment
from trading_research.analytics.technical import calculate_technical_indicators
from trading_research.config import settings
from trading_research.costs import add_usage
from trading_research.llm import LLMService
from trading_research.providers.market_data import fetch_market_data, price_history_frame
from trading_research.providers.news import fetch_recent_news
from trading_research.providers.sec import fetch_recent_filings
from trading_research.rag.store import ResearchVectorStore
from trading_research.reports.generator import build_markdown_report, export_report_markdown, export_report_pdf
from trading_research.schemas import CostLedger, ResearchRequest, ResearchStateModel

try:
    from langgraph.graph import END, StateGraph
except ImportError:  # pragma: no cover
    END = "__end__"
    StateGraph = None


WORKFLOW_ORDER = [
    "data_collection",
    "fundamental_analysis",
    "technical_analysis",
    "sentiment_analysis",
    "risk_assessment",
    "report_generation",
]

VECTOR_STORE = ResearchVectorStore()


class ResearchGraphState(TypedDict, total=False):
    request_id: str
    query: str
    ticker: str
    research_depth: str
    research_plan: str
    current_agent: str
    completed_agents: list[str]
    errors: list[str]
    data_collection: dict[str, Any]
    fundamental_analysis: dict[str, Any]
    technical_analysis: dict[str, Any]
    sentiment_analysis: dict[str, Any]
    risk_assessment: dict[str, Any]
    report_generation: dict[str, Any]
    final_report_markdown: str
    final_report_path: str | None
    total_tokens: int
    estimated_cost_usd: float


def initialize_state(request: ResearchRequest) -> ResearchGraphState:
    return {
        "request_id": str(uuid.uuid4()),
        "query": request.query or f"Research {request.ticker.upper()} for investment potential",
        "ticker": request.ticker.upper(),
        "research_depth": request.research_depth,
        "research_plan": "Collect market data, analyze fundamentals/technicals/sentiment/risk, then synthesize a report.",
        "current_agent": "supervisor",
        "completed_agents": [],
        "errors": [],
        "data_collection": {},
        "fundamental_analysis": {},
        "technical_analysis": {},
        "sentiment_analysis": {},
        "risk_assessment": {},
        "report_generation": {},
        "final_report_markdown": "",
        "final_report_path": None,
        "total_tokens": 0,
        "estimated_cost_usd": 0.0,
    }


def supervisor_node(state: ResearchGraphState) -> ResearchGraphState:
    completed = set(state.get("completed_agents", []))
    for agent_name in WORKFLOW_ORDER:
        if agent_name not in completed:
            state["current_agent"] = agent_name
            return state
    state["current_agent"] = "FINISH"
    return state


def route_from_supervisor(state: ResearchGraphState) -> str:
    current = state.get("current_agent", "FINISH")
    return END if current == "FINISH" else current


def _append_completed(state: ResearchGraphState, agent_name: str) -> None:
    state["completed_agents"] = list(state.get("completed_agents", [])) + [agent_name]


def _narrative(system_prompt: str, user_prompt: str, component: str, ledger: CostLedger) -> str:
    llm = LLMService(model=settings.default_model, temperature=0.2)
    output = llm.invoke(system_prompt, user_prompt)
    add_usage(ledger, component, settings.default_model, output.prompt_tokens, output.completion_tokens)
    return output.content


def data_collection_agent(state: ResearchGraphState) -> ResearchGraphState:
    bundle = fetch_market_data(state["ticker"])
    news = fetch_recent_news(state["ticker"], bundle.company_info.get("longName"))
    filings = fetch_recent_filings(state["ticker"])
    price_frame = price_history_frame(bundle.price_history)
    latest_close = float(price_frame["Close"].iloc[-1]) if not price_frame.empty else 0.0

    state["data_collection"] = {
        "status": "completed",
        "summary": "Collected market, financial, news, analyst, and filing data.",
        "payload": {
            "company_info": bundle.company_info,
            "price_history": bundle.price_history,
            "financials": bundle.financials,
            "analyst_ratings": bundle.analyst_ratings,
            "news": news,
            "sec_filings": filings,
            "snapshot": {
                "current_price": round(latest_close, 2),
                "52_week_high": round(float(price_frame["Close"].max()), 2),
                "52_week_low": round(float(price_frame["Close"].min()), 2),
                "avg_volume": round(float(price_frame["Volume"].mean()), 2),
                "market_cap": bundle.company_info.get("marketCap"),
            },
        },
    }
    _append_completed(state, "data_collection")
    return state


def fundamental_analysis_agent(state: ResearchGraphState) -> ResearchGraphState:
    payload = state["data_collection"]["payload"]
    ratios = calculate_financial_ratios(payload["financials"], payload["company_info"])
    rag_hits = VECTOR_STORE.similarity_search(f"fundamental analysis for {state['ticker']}", ticker=state["ticker"])
    rag_context = "\n\n".join(doc.content[:400] for doc in rag_hits) or "No prior research context."
    ledger = CostLedger()
    narrative = _narrative(
        "You are a CFA-style fundamental analyst.",
        f"Ticker: {state['ticker']}\nRatios: {ratios}\nHistorical context: {rag_context}\nWrite a structured assessment with valuation, growth, and quality-of-earnings commentary.",
        "fundamental_analysis",
        ledger,
    )
    state["fundamental_analysis"] = {
        "status": "completed",
        "summary": "Generated ratio-driven fundamental analysis.",
        "payload": {"ratios": ratios, "narrative": narrative},
    }
    state["total_tokens"] += ledger.total_tokens
    state["estimated_cost_usd"] += ledger.total_cost_usd
    _append_completed(state, "fundamental_analysis")
    return state


def technical_analysis_agent(state: ResearchGraphState) -> ResearchGraphState:
    price_frame = price_history_frame(state["data_collection"]["payload"]["price_history"])
    indicators = calculate_technical_indicators(price_frame)
    ledger = CostLedger()
    narrative = _narrative(
        "You are a technical research analyst.",
        f"Ticker: {state['ticker']}\nIndicators: {indicators}\nExplain trend, momentum, support/resistance, and trading levels.",
        "technical_analysis",
        ledger,
    )
    state["technical_analysis"] = {
        "status": "completed",
        "summary": "Computed technical indicators and generated interpretation.",
        "payload": {"indicators": indicators, "narrative": narrative},
    }
    state["total_tokens"] += ledger.total_tokens
    state["estimated_cost_usd"] += ledger.total_cost_usd
    _append_completed(state, "technical_analysis")
    return state


def sentiment_analysis_agent(state: ResearchGraphState) -> ResearchGraphState:
    news = state["data_collection"]["payload"]["news"]
    sentiment = aggregate_news_sentiment(news)
    ledger = CostLedger()
    headlines = [item.get("title", "") for item in news]
    narrative = _narrative(
        "You are a market sentiment analyst.",
        f"Ticker: {state['ticker']}\nAggregated sentiment: {sentiment}\nHeadlines: {headlines}\nIdentify dominant themes, catalysts, and dislocations versus price action.",
        "sentiment_analysis",
        ledger,
    )
    state["sentiment_analysis"] = {
        "status": "completed",
        "summary": "Aggregated source sentiment and generated narrative.",
        "payload": {"sentiment": sentiment, "narrative": narrative},
    }
    state["total_tokens"] += ledger.total_tokens
    state["estimated_cost_usd"] += ledger.total_cost_usd
    _append_completed(state, "sentiment_analysis")
    return state


def risk_assessment_agent(state: ResearchGraphState) -> ResearchGraphState:
    price_frame = price_history_frame(state["data_collection"]["payload"]["price_history"])
    benchmark_bundle = fetch_market_data(
        settings.market_benchmark,
        include_info=False,
        include_financials=False,
        include_analyst_ratings=False,
    )
    benchmark_frame = price_history_frame(benchmark_bundle.price_history)
    risk_metrics = calculate_risk_metrics(price_frame, benchmark_frame)
    ledger = CostLedger()
    narrative = _narrative(
        "You are a portfolio risk specialist.",
        (
            f"Ticker: {state['ticker']}\nRisk metrics: {risk_metrics}\n"
            f"Fundamental summary: {state['fundamental_analysis']['payload'].get('narrative', '')[:500]}\n"
            f"Technical summary: {state['technical_analysis']['payload'].get('narrative', '')[:500]}\n"
            f"Sentiment summary: {state['sentiment_analysis']['payload'].get('narrative', '')[:500]}\n"
            "Provide risk rating, downside scenarios, and sizing/hedging guidance."
        ),
        "risk_assessment",
        ledger,
    )
    state["risk_assessment"] = {
        "status": "completed",
        "summary": "Calculated risk metrics and produced portfolio risk interpretation.",
        "payload": {"risk_metrics": risk_metrics, "narrative": narrative},
    }
    state["total_tokens"] += ledger.total_tokens
    state["estimated_cost_usd"] += ledger.total_cost_usd
    _append_completed(state, "risk_assessment")
    return state


def report_generation_agent(state: ResearchGraphState) -> ResearchGraphState:
    company_info = state["data_collection"]["payload"]["company_info"]
    ledger = CostLedger()
    executive_summary = _narrative(
        "You are an institutional equity research analyst.",
        (
            f"Ticker: {state['ticker']}\n"
            f"Fundamental: {state['fundamental_analysis']['payload'].get('narrative', '')}\n"
            f"Technical: {state['technical_analysis']['payload'].get('narrative', '')}\n"
            f"Sentiment: {state['sentiment_analysis']['payload'].get('narrative', '')}\n"
            f"Risk: {state['risk_assessment']['payload'].get('narrative', '')}\n"
            "Write an executive summary and final recommendation with price-target framing."
        ),
        "report_generation",
        ledger,
    )
    markdown_report = build_markdown_report(
        ticker=state["ticker"],
        company_info=company_info,
        sections={
            "executive_summary": executive_summary,
            "fundamental_analysis": state["fundamental_analysis"]["payload"].get("narrative", ""),
            "technical_analysis": state["technical_analysis"]["payload"].get("narrative", ""),
            "sentiment_analysis": state["sentiment_analysis"]["payload"].get("narrative", ""),
            "risk_assessment": state["risk_assessment"]["payload"].get("narrative", ""),
            "recommendation": executive_summary,
        },
    )
    markdown_path = export_report_markdown(markdown_report, state["ticker"])
    pdf_path = export_report_pdf(markdown_report, state["ticker"])
    VECTOR_STORE.ingest_text(
        markdown_report,
        {
            "ticker": state["ticker"],
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "type": "research_report",
        },
    )

    state["report_generation"] = {
        "status": "completed",
        "summary": "Generated markdown and PDF investment report.",
        "payload": {
            "markdown_path": markdown_path,
            "pdf_path": pdf_path,
            "executive_summary": executive_summary,
        },
    }
    state["final_report_markdown"] = markdown_report
    state["final_report_path"] = markdown_path
    state["total_tokens"] += ledger.total_tokens
    state["estimated_cost_usd"] += ledger.total_cost_usd
    _append_completed(state, "report_generation")
    return state


def build_research_graph():
    if not StateGraph:
        return None

    graph = StateGraph(ResearchGraphState)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("data_collection", data_collection_agent)
    graph.add_node("fundamental_analysis", fundamental_analysis_agent)
    graph.add_node("technical_analysis", technical_analysis_agent)
    graph.add_node("sentiment_analysis", sentiment_analysis_agent)
    graph.add_node("risk_assessment", risk_assessment_agent)
    graph.add_node("report_generation", report_generation_agent)
    graph.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {
            "data_collection": "data_collection",
            "fundamental_analysis": "fundamental_analysis",
            "technical_analysis": "technical_analysis",
            "sentiment_analysis": "sentiment_analysis",
            "risk_assessment": "risk_assessment",
            "report_generation": "report_generation",
            END: END,
        },
    )
    for node in WORKFLOW_ORDER:
        graph.add_edge(node, "supervisor")
    graph.set_entry_point("supervisor")
    return graph.compile()


def execute_research(request: ResearchRequest) -> ResearchStateModel:
    final_state = initialize_state(request)
    graph = build_research_graph()

    if graph:
        final_state = graph.invoke(final_state)
    else:
        final_state = supervisor_node(final_state)
        for agent in [
            data_collection_agent,
            fundamental_analysis_agent,
            technical_analysis_agent,
            sentiment_analysis_agent,
            risk_assessment_agent,
            report_generation_agent,
        ]:
            final_state = agent(final_state)
            final_state = supervisor_node(final_state)

    final_state["current_agent"] = "FINISH"
    model = ResearchStateModel.model_validate(final_state)
    model.completed_at = datetime.now(timezone.utc)
    return model
