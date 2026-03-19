import pandas as pd
import pytest


@pytest.fixture
def sample_price_frame():
    return pd.DataFrame(
        [
            {"Date": "2025-01-01", "Open": 100, "High": 101, "Low": 99, "Close": 100, "Volume": 1000},
            {"Date": "2025-01-02", "Open": 101, "High": 102, "Low": 100, "Close": 101, "Volume": 1000},
            {"Date": "2025-01-03", "Open": 102, "High": 103, "Low": 101, "Close": 102, "Volume": 1000},
            {"Date": "2025-01-04", "Open": 103, "High": 104, "Low": 102, "Close": 101, "Volume": 1000},
            {"Date": "2025-01-05", "Open": 104, "High": 105, "Low": 103, "Close": 103, "Volume": 1000},
        ]
    )

