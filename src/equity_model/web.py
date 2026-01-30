from __future__ import annotations

from dataclasses import asdict
from importlib import resources

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .model import DataFetchError, estimate_intrinsic_value

app = FastAPI(title="Equity Model")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

static_dir = resources.files("equity_model").joinpath("static")
templates_dir = resources.files("equity_model").joinpath("templates")

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

templates = Jinja2Templates(directory=str(templates_dir))


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/estimate")
def api_estimate(
    ticker: str,
    years: int = 5,
    discount_rate: float = 0.09,
    terminal_growth: float = 0.02,
) -> JSONResponse:
    try:
        estimate = estimate_intrinsic_value(
            ticker=ticker,
            forecast_years=years,
            discount_rate=discount_rate,
            terminal_growth=terminal_growth,
        )
    except DataFetchError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return JSONResponse(asdict(estimate))


def main() -> None:
    uvicorn.run("equity_model.web:app", host="0.0.0.0", port=8000)
