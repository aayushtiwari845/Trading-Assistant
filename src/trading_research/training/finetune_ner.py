from __future__ import annotations

import json
from pathlib import Path


def load_training_examples(path: str | Path) -> list[dict]:
    dataset_path = Path(path)
    raw = dataset_path.read_text(encoding="utf-8")
    return json.loads(raw)


TRAINING_NOTES = """
This module is a scaffold for a financial NER fine-tuning pipeline.

Recommended next step:
1. Replace the sample dataset with a larger BIO-tagged dataset.
2. Add Hugging Face token alignment and Trainer code.
3. Save the trained model under artifacts/financial_ner_model/.
"""

