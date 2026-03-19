from __future__ import annotations

import logging

import requests

LOGGER = logging.getLogger(__name__)
SEC_HEADERS = {
    "User-Agent": "trading-research-platform/0.1 contact@example.com",
    "Accept-Encoding": "gzip, deflate",
}


def fetch_recent_filings(ticker: str, limit: int = 5) -> list[dict[str, str]]:
    try:
        mapping_response = requests.get(
            "https://www.sec.gov/files/company_tickers.json",
            headers=SEC_HEADERS,
            timeout=20,
        )
        mapping_response.raise_for_status()
        companies = mapping_response.json()
        match = next(
            (item for item in companies.values() if item.get("ticker", "").upper() == ticker.upper()),
            None,
        )
        if not match:
            return []

        cik = str(match["cik_str"]).zfill(10)
        response = requests.get(
            f"https://data.sec.gov/submissions/CIK{cik}.json",
            headers=SEC_HEADERS,
            timeout=20,
        )
        response.raise_for_status()
        filings = response.json().get("filings", {}).get("recent", {})

        forms = filings.get("form", [])
        accession_numbers = filings.get("accessionNumber", [])
        primary_docs = filings.get("primaryDocument", [])
        filing_dates = filings.get("filingDate", [])

        results: list[dict[str, str]] = []
        for idx, form in enumerate(forms[:limit]):
            accession = accession_numbers[idx].replace("-", "")
            primary_doc = primary_docs[idx]
            results.append(
                {
                    "form": form,
                    "filing_date": filing_dates[idx],
                    "url": f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession}/{primary_doc}",
                }
            )
        return results
    except Exception as exc:  # pragma: no cover - network dependent
        LOGGER.warning("SEC lookup failed for %s: %s", ticker, exc)
        return []
