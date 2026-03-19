from __future__ import annotations

import time

import requests
import streamlit as st

from trading_research.agents.workflow import execute_research
from trading_research.schemas import ResearchRequest

st.set_page_config(page_title="Trading Research Platform", page_icon=":chart_with_upwards_trend:", layout="wide")

st.title("Intelligent Trading Research Platform")
st.caption("Multi-agent stock research with data collection, analysis, RAG, and report generation.")

with st.sidebar:
    st.header("Run Configuration")
    ticker = st.text_input("Ticker", value="AAPL").upper()
    depth = st.selectbox("Research Depth", ["quick", "standard", "deep"], index=1)
    execution_mode = st.radio("Execution Mode", ["Direct Python", "FastAPI"], index=0)
    api_base_url = st.text_input("API Base URL", value="http://localhost:8000")
    start = st.button("Start Research", type="primary")

if start:
    request = ResearchRequest(ticker=ticker, research_depth=depth)
    with st.spinner(f"Researching {ticker}..."):
        if execution_mode == "Direct Python":
            state = execute_research(request)
            result = {
                "status": "completed",
                "result": {
                    "request_id": state.request_id,
                    "ticker": state.ticker,
                    "state": state.model_dump(mode="json"),
                    "cost_estimate_usd": state.estimated_cost_usd,
                },
            }
        else:
            create_response = requests.post(f"{api_base_url}/api/research", json=request.model_dump(), timeout=30)
            create_response.raise_for_status()
            request_id = create_response.json()["request_id"]
            result = {}
            for _ in range(60):
                poll = requests.get(f"{api_base_url}/api/research/{request_id}", timeout=30)
                poll.raise_for_status()
                result = poll.json()
                if result.get("status") in {"completed", "failed"}:
                    break
                time.sleep(2)

    if result.get("status") == "failed":
        st.error(result.get("error", "Research failed."))
    else:
        payload = result["result"]["state"]
        st.success("Research completed.")
        st.metric("Estimated Cost (USD)", f"{result['result'].get('cost_estimate_usd', 0):.4f}")
        st.metric("Agents Completed", len(payload.get("completed_agents", [])))

        tab1, tab2, tab3, tab4, tab5 = st.tabs(
            ["Report", "Fundamental", "Technical", "Sentiment", "Risk"]
        )

        with tab1:
            st.markdown(payload.get("final_report_markdown", ""))

        with tab2:
            st.json(payload.get("fundamental_analysis", {}).get("payload", {}))

        with tab3:
            st.json(payload.get("technical_analysis", {}).get("payload", {}))

        with tab4:
            st.json(payload.get("sentiment_analysis", {}).get("payload", {}))

        with tab5:
            st.json(payload.get("risk_assessment", {}).get("payload", {}))

