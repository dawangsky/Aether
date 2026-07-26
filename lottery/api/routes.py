"""FastAPI 路由。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from lottery import __version__
from lottery.analysis.service import build_analyze_payload
from lottery.api.schemas import (
    BacktestRequest,
    BacktestResponse,
    DrawItem,
    DrawsResponse,
    HealthResponse,
    PredictRequest,
    PredictResponse,
    TicketItem,
    UpdateRequest,
    UpdateResponse,
    UpdateResultItem,
)
from lottery.backtest.evaluator import run_backtest
from lottery.config import GAMES, get_game
from lottery.data.fetcher import update_game, update_games
from lottery.data.loader import load_draws
from lottery.predict.generator import generate_tickets

router = APIRouter()


def _ensure_draws(game: str, min_count: int = 5):
    draws = load_draws(game)
    if len(draws) < min_count:
        raise HTTPException(
            status_code=400,
            detail=f"{game} 本地数据不足（{len(draws)} 期），请先调用 POST /update",
        )
    return draws


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", version=__version__)


@router.get("/draws", response_model=DrawsResponse)
def draws(
    game: str = Query(..., pattern="^(ssq|dlt)$"),
    limit: int = Query(20, ge=1, le=200),
) -> DrawsResponse:
    cfg = get_game(game)
    all_draws = load_draws(cfg)
    items = all_draws[-limit:]
    return DrawsResponse(
        game=cfg.key,  # type: ignore[arg-type]
        total=len(all_draws),
        items=[
            DrawItem(
                issue=d.issue,
                date=d.date,
                main=list(d.main_sorted()),
                special=list(d.special_sorted()),
                formatted=d.format_numbers(),
            )
            for d in items
        ],
    )


@router.post("/update", response_model=UpdateResponse)
def update(body: UpdateRequest) -> UpdateResponse:
    try:
        if body.game == "all":
            result = update_games(list(GAMES), limit=body.limit)
        else:
            draws, added = update_game(body.game, limit=body.limit)
            result = {body.game: (len(draws), added)}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"拉取失败: {exc}") from exc
    return UpdateResponse(
        results=[
            UpdateResultItem(game=g, total=total, added=added)
            for g, (total, added) in result.items()
        ]
    )


@router.get("/analyze")
def analyze(
    game: str = Query(..., pattern="^(ssq|dlt)$"),
    window: int = Query(50, ge=10, le=300),
) -> dict:
    cfg = get_game(game)
    draws = _ensure_draws(game, min_count=1)
    try:
        return build_analyze_payload(cfg, draws, window)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/predict", response_model=PredictResponse)
def predict(body: PredictRequest) -> PredictResponse:
    cfg = get_game(body.game)
    draws = _ensure_draws(body.game, min_count=5)
    window_draws = draws[-body.window :] if len(draws) > body.window else draws
    try:
        tickets = generate_tickets(cfg, window_draws, n=body.n, seed=body.seed)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return PredictResponse(
        game=body.game,
        window=len(window_draws),
        last_issue=window_draws[-1].issue,
        tickets=[
            TicketItem(
                main=list(t.main),
                special=list(t.special),
                formatted=t.format_numbers(),
                meta=t.meta,
            )
            for t in tickets
        ],
    )


@router.post("/backtest", response_model=BacktestResponse)
def backtest(body: BacktestRequest) -> BacktestResponse:
    cfg = get_game(body.game)
    draws = _ensure_draws(body.game, min_count=body.window + 5)
    try:
        result = run_backtest(
            cfg,
            draws,
            window=body.window,
            n_tickets=body.n,
            periods=body.periods,
            seed=body.seed,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return BacktestResponse(game=body.game, result=result)
