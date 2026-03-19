from trading_research.schemas import CostLedger


MODEL_INPUT_COST_PER_1K = {
    "gpt-4o-mini": 0.00015,
    "gpt-4o": 0.005,
}

MODEL_OUTPUT_COST_PER_1K = {
    "gpt-4o-mini": 0.0006,
    "gpt-4o": 0.015,
}


def estimate_llm_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    input_rate = MODEL_INPUT_COST_PER_1K.get(model, MODEL_INPUT_COST_PER_1K["gpt-4o-mini"])
    output_rate = MODEL_OUTPUT_COST_PER_1K.get(model, MODEL_OUTPUT_COST_PER_1K["gpt-4o-mini"])
    return (prompt_tokens / 1000 * input_rate) + (completion_tokens / 1000 * output_rate)


def add_usage(ledger: CostLedger, component: str, model: str, prompt_tokens: int, completion_tokens: int) -> None:
    ledger.add(
        component=component,
        tokens=prompt_tokens + completion_tokens,
        cost_usd=estimate_llm_cost(model, prompt_tokens, completion_tokens),
    )
