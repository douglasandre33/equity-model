from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from .model import DataFetchError, estimate_intrinsic_value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Estimate intrinsic value for a ticker using a simple DCF.")
    parser.add_argument("--ticker", required=True, help="Ticker symbol (e.g., DUOL, LMT).")
    parser.add_argument("--years", type=int, default=5, help="Forecast horizon in years.")
    parser.add_argument("--discount-rate", type=float, default=0.09, help="Discount rate (WACC proxy).")
    parser.add_argument("--terminal-growth", type=float, default=0.02, help="Terminal growth rate.")
    parser.add_argument(
        "--growth-cap",
        type=float,
        nargs=2,
        default=(-0.1, 0.2),
        metavar=("LOW", "HIGH"),
        help="Clamp forecast CAGR between LOW and HIGH.",
    )
    parser.add_argument("--json", action="store_true", help="Output results as JSON.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        estimate = estimate_intrinsic_value(
            ticker=args.ticker,
            forecast_years=args.years,
            discount_rate=args.discount_rate,
            terminal_growth=args.terminal_growth,
            growth_cap=(args.growth_cap[0], args.growth_cap[1]),
        )
    except DataFetchError as exc:
        parser.error(str(exc))
        return

    if args.json:
        print(json.dumps(asdict(estimate), indent=2))
        return

    print(f"Ticker: {estimate.ticker}")
    print(f"Currency: {estimate.currency}")
    print(f"Intrinsic value: {estimate.intrinsic_value:,.2f}")
    if estimate.share_price is not None:
        print(f"Current price: {estimate.share_price:,.2f}")
    print(f"Shares outstanding: {estimate.shares_outstanding:,.0f}")
    print(f"Discount rate: {estimate.discount_rate:.2%}")
    print(f"Terminal growth: {estimate.terminal_growth:.2%}")
    print(f"Forecast years: {estimate.forecast_years}")
    print("Historical FCF:")
    for value in estimate.fcf_history:
        print(f"  - {value:,.0f}")
    print("Forecast FCF:")
    for value in estimate.fcf_forecast:
        print(f"  - {value:,.0f}")


if __name__ == "__main__":
    main()
