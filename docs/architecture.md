# Architecture

## Request flow

1. User submits a ticker through Streamlit or FastAPI.
2. The supervisor agent creates the research plan and dispatches the next pending agent.
3. Data collection gathers market data, news, analyst context, and SEC filings.
4. Analytics agents compute deterministic metrics first, then request LLM synthesis.
5. Report generation exports markdown and PDF and ingests the report into the vector store.

## Agent inventory

- `supervisor`
- `data_collection`
- `fundamental_analysis`
- `technical_analysis`
- `sentiment_analysis`
- `risk_assessment`
- `report_generation`

## Storage layers

- Chroma for historical research retrieval
- Redis/PostgreSQL placeholders in config for production persistence
- Local report output directory for artifacts

## Design choices

- Deterministic calculations happen before LLM calls to reduce cost and improve explainability.
- Each provider has a fallback path so the repo stays usable in partially configured environments.
- LangGraph is the preferred runtime, but the workflow has a sequential fallback for local development.

