from __future__ import annotations

from typing import Any


def _pick_first_number(statement: dict[str, Any], candidates: list[str]) -> float:
    for row_name, values in statement.items():
        if row_name in candidates:
            if isinstance(values, dict):
                for value in values.values():
                    if isinstance(value, (int, float)):
                        return float(value)
            elif isinstance(values, (int, float)):
                return float(values)
    return 0.0


def calculate_financial_ratios(financials: dict[str, Any], company_info: dict[str, Any]) -> dict[str, float]:
    income_statement = financials.get("income_statement", {})
    balance_sheet = financials.get("balance_sheet", {})
    cash_flow = financials.get("cash_flow", {})

    revenue = _pick_first_number(income_statement, ["Total Revenue", "Operating Revenue"])
    net_income = _pick_first_number(income_statement, ["Net Income", "Net Income Common Stockholders"])
    ebitda = _pick_first_number(income_statement, ["EBITDA"])
    operating_income = _pick_first_number(income_statement, ["Operating Income"])
    current_assets = _pick_first_number(balance_sheet, ["Current Assets", "Total Current Assets"])
    current_liabilities = _pick_first_number(balance_sheet, ["Current Liabilities", "Total Current Liabilities"])
    total_assets = _pick_first_number(balance_sheet, ["Total Assets"])
    total_debt = _pick_first_number(balance_sheet, ["Total Debt", "Long Term Debt"])
    equity = _pick_first_number(balance_sheet, ["Stockholders Equity", "Total Equity Gross Minority Interest"])
    operating_cash_flow = _pick_first_number(
        cash_flow,
        ["Operating Cash Flow", "Cash Flow From Continuing Operating Activities"],
    )

    ratios: dict[str, float] = {
        "market_cap": float(company_info.get("marketCap", 0) or 0),
        "forward_pe": float(company_info.get("forwardPE", 0) or 0),
        "trailing_pe": float(company_info.get("trailingPE", 0) or 0),
        "price_to_book": float(company_info.get("priceToBook", 0) or 0),
        "dividend_yield": float(company_info.get("dividendYield", 0) or 0),
        "revenue": revenue,
        "net_income": net_income,
        "ebitda": ebitda,
    }

    if revenue:
        ratios["profit_margin_pct"] = round((net_income / revenue) * 100, 2)
        ratios["operating_margin_pct"] = round((operating_income / revenue) * 100, 2)
        ratios["cash_conversion_pct"] = round((operating_cash_flow / revenue) * 100, 2)
    if total_assets:
        ratios["roa_pct"] = round((net_income / total_assets) * 100, 2)
        ratios["asset_turnover"] = round(revenue / total_assets, 2) if revenue else 0.0
    if equity:
        ratios["roe_pct"] = round((net_income / equity) * 100, 2)
        ratios["debt_to_equity"] = round(total_debt / equity, 2)
    if current_liabilities:
        ratios["current_ratio"] = round(current_assets / current_liabilities, 2)

    return ratios

