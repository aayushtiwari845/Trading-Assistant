# Intelligent Trading Research Platform

Multi-agent AI research system for institutional-style stock analysis. The project combines LangGraph orchestration, retrieval-augmented generation, quant analytics, risk scoring, report generation, a FastAPI backend, and a Streamlit frontend.

## What is implemented

- Six-agent workflow with a supervisor pattern in `src/trading_research/agents/workflow.py`
- Data collection layer for market data, news, analyst ratings, and SEC filings
- Fundamental, technical, sentiment, and risk analytics modules
- RAG-ready Chroma wrapper with offline fallback
- Markdown and PDF report generation
- FastAPI backend with background jobs
- Streamlit UI for direct or API-backed execution
- Evaluation hooks for RAGAS and W&B
- Fine-tuning scaffold plus sample financial NER dataset

## Project structure

```text
src/trading_research/
  agents/        LangGraph workflow and agent nodes
  analytics/     Deterministic finance calculations
  api/           FastAPI app and in-memory job store
  evaluation/    RAG and recommendation evaluation hooks
  providers/     yfinance, news, and SEC access
  rag/           Chroma integration
  reports/       Markdown/PDF report exporters
  training/      Fine-tuning scaffolding
  ui/            Streamlit app
assets/          Sample NER dataset
infrastructure/  Docker assets
tests/           Smoke tests
```

## Setup

1. Install Python 3.11+.
2. Create and activate a virtual environment.
3. Install dependencies:

```bash
pip install -e .[dev,eval]
```

4. Copy `.env.example` to `.env` and set API keys you want to enable.

## Run the API

```bash
uvicorn trading_research.api.main:app --reload
```

## Run the Streamlit UI

```bash
streamlit run src/trading_research/ui/app.py
```

## Notes on execution

- The system is designed to degrade gracefully when live keys are missing.
- Without `OPENAI_API_KEY`, narrative sections use a deterministic offline fallback.
- Without `NEWS_API_KEY`, sentiment uses fallback article stubs.
- Without LangGraph installed, the workflow still executes sequentially.

## Next upgrades

- Replace the in-memory FastAPI job store with Redis/PostgreSQL persistence.
- Add real Finnhub / Alpha Vantage adapters and rate limiting.
- Expand the NER training pipeline from the sample dataset into BIO-tag training.
- Add richer charting and report templates.
- Add Celery or distributed workers for longer-running research jobs.
