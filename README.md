# Equity Model

A small, fundamentals-driven equity research model that pulls financials for a ticker and estimates intrinsic value using a simplified DCF.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .

equity-model --ticker DUOL
```

## What it does

- Fetches historical cash flow data via `yfinance`.
- Computes free cash flow (operating cash flow minus capex).
- Forecasts future cash flows using a historical CAGR with configurable caps.
- Discounts forecast cash flows and a terminal value to estimate intrinsic value.

## Example

```bash
equity-model --ticker LMT --years 5 --discount-rate 0.09 --terminal-growth 0.02
```

## Web UI

To run the local website (FastAPI + HTML/CSS):

```bash
pip install -e .
uvicorn equity_model.web:app --reload --port 8000
```

Then open `http://localhost:8000` in your browser.

### Hosting on GitHub Pages

GitHub Pages only hosts static files, so it cannot execute the Python model directly. You have two options:

1. Host the API separately (Render, Fly.io, Railway, Google Cloud Run, etc.) and point the website to that API.
2. Convert the model to a purely client-side or serverless approach (e.g., WebAssembly or a serverless function).

> Note: This is a research scaffold, not investment advice.
