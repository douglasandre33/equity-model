from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd
import yfinance as yf


@dataclass(frozen=True)
class IntrinsicValueEstimate:
    ticker: str
    currency: str
    intrinsic_value: float
    share_price: float | None
    shares_outstanding: float
    discount_rate: float
    terminal_growth: float
    forecast_years: int
    fcf_history: list[float]
    fcf_forecast: list[float]


class DataFetchError(RuntimeError):
    """Raised when a required data input is missing or malformed."""


def _normalize_cashflow(cashflow: pd.DataFrame) -> pd.DataFrame:
    if cashflow.empty:
        raise DataFetchError("Cash flow statement is empty.")

    if not isinstance(cashflow.columns, pd.DatetimeIndex):
        cashflow.columns = pd.to_datetime(cashflow.columns, errors="coerce")

    return cashflow.sort_index(axis=1)


def _extract_fcf(cashflow: pd.DataFrame) -> list[float]:
    cashflow = _normalize_cashflow(cashflow)
    operating = cashflow.loc[cashflow.index.str.contains("Operating", case=False, na=False)]
    capex = cashflow.loc[cashflow.index.str.contains("Capital Expenditures", case=False, na=False)]

    if operating.empty or capex.empty:
        raise DataFetchError("Missing operating cash flow or capital expenditures in cash flow statement.")

    operating_series = operating.iloc[0]
    capex_series = capex.iloc[0]

    fcf = operating_series - capex_series
    fcf = fcf.dropna().astype(float)

    if fcf.empty:
        raise DataFetchError("Unable to compute free cash flow from cash flow statement.")

    return fcf.tolist()


def _cagr(values: Iterable[float]) -> float:
    values = list(values)
    if len(values) < 2:
        return 0.0

    start, end = values[0], values[-1]
    if start == 0:
        return 0.0

    periods = len(values) - 1
    return (end / start) ** (1 / periods) - 1


def _forecast_fcf(fcf_history: list[float], years: int, growth_cap: tuple[float, float]) -> list[float]:
    if years <= 0:
        return []

    growth_rate = _cagr(fcf_history[-min(len(fcf_history), 3) :])
    growth_rate = float(np.clip(growth_rate, growth_cap[0], growth_cap[1]))

    forecast = []
    last = fcf_history[-1]
    for _ in range(years):
        last *= 1 + growth_rate
        forecast.append(last)
    return forecast


def estimate_intrinsic_value(
    ticker: str,
    forecast_years: int = 5,
    discount_rate: float = 0.09,
    terminal_growth: float = 0.02,
    growth_cap: tuple[float, float] = (-0.1, 0.2),
) -> IntrinsicValueEstimate:
    """Estimate intrinsic value per share using a simplified DCF model."""

    yf_ticker = yf.Ticker(ticker)
    cashflow = yf_ticker.cashflow
    fcf_history = _extract_fcf(cashflow)

    fcf_forecast = _forecast_fcf(fcf_history, forecast_years, growth_cap)

    discount_factors = [(1 + discount_rate) ** year for year in range(1, forecast_years + 1)]
    discounted_fcf = [fcf / df for fcf, df in zip(fcf_forecast, discount_factors, strict=False)]

    if not fcf_forecast:
        raise DataFetchError("Forecast could not be generated; check historical cash flow data.")

    terminal_value = fcf_forecast[-1] * (1 + terminal_growth) / (discount_rate - terminal_growth)
    terminal_discounted = terminal_value / ((1 + discount_rate) ** forecast_years)

    enterprise_value = float(np.sum(discounted_fcf) + terminal_discounted)

    info = yf_ticker.info
    shares_outstanding = info.get("sharesOutstanding")
    if not shares_outstanding:
        raise DataFetchError("Shares outstanding not available in ticker metadata.")

    share_price = info.get("currentPrice")
    currency = info.get("currency", "USD")

    intrinsic_value = enterprise_value / shares_outstanding

    return IntrinsicValueEstimate(
        ticker=ticker.upper(),
        currency=currency,
        intrinsic_value=intrinsic_value,
        share_price=share_price,
        shares_outstanding=float(shares_outstanding),
        discount_rate=discount_rate,
        terminal_growth=terminal_growth,
        forecast_years=forecast_years,
        fcf_history=fcf_history,
        fcf_forecast=fcf_forecast,
    )
