from __future__ import annotations

from typing import Any

try:
    import wandb
except ImportError:  # pragma: no cover
    wandb = None

try:
    from ragas import evaluate
    from ragas.metrics import answer_relevancy, context_precision, context_recall, faithfulness
except ImportError:  # pragma: no cover
    evaluate = None
    answer_relevancy = None
    context_precision = None
    context_recall = None
    faithfulness = None


def evaluate_rag_quality(query: str, answer: str, contexts: list[str]) -> dict[str, Any]:
    if not evaluate:
        return {
            "available": False,
            "message": "Install the optional eval dependencies to enable RAGAS scoring.",
            "query": query,
        }

    dataset = {
        "question": [query],
        "answer": [answer],
        "contexts": [contexts],
        "ground_truth": [""],
    }
    scores = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
    )
    return {"available": True, "scores": scores}


def evaluate_recommendation(recommendation: str, actual_price_change_pct: float) -> dict[str, Any]:
    normalized = recommendation.upper()
    if "BUY" in normalized:
        expected = actual_price_change_pct > 5
        label = "BUY"
    elif "SELL" in normalized:
        expected = actual_price_change_pct < -5
        label = "SELL"
    else:
        expected = -5 <= actual_price_change_pct <= 5
        label = "HOLD"

    return {
        "recommendation": label,
        "actual_price_change_pct": actual_price_change_pct,
        "correct": expected,
    }


def log_metrics(metrics: dict[str, Any]) -> None:
    if wandb:
        wandb.log(metrics)

