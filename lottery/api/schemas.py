"""FastAPI Pydantic 模型。"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

GameKey = Literal["ssq", "dlt"]
GameOrAll = Literal["ssq", "dlt", "all"]


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    name: str = "lottery-quant-api"


class DrawItem(BaseModel):
    issue: str
    date: str
    main: list[int]
    special: list[int]
    formatted: str


class DrawsResponse(BaseModel):
    game: GameKey
    total: int
    items: list[DrawItem]


class UpdateRequest(BaseModel):
    game: GameOrAll = "all"
    limit: int = Field(default=120, ge=10, le=500)


class UpdateResultItem(BaseModel):
    game: str
    total: int
    added: int


class UpdateResponse(BaseModel):
    results: list[UpdateResultItem]


class PredictRequest(BaseModel):
    game: GameKey
    n: int = Field(default=2, ge=1, le=20)
    window: int = Field(default=50, ge=10, le=300)
    seed: int | None = None


class TicketItem(BaseModel):
    main: list[int]
    special: list[int]
    formatted: str
    meta: dict[str, Any] = Field(default_factory=dict)


class PredictResponse(BaseModel):
    game: GameKey
    window: int
    last_issue: str
    tickets: list[TicketItem]
    disclaimer: str = "仅供研究娱乐，开奖随机，不构成投注建议。"


class BacktestRequest(BaseModel):
    game: GameKey
    window: int = Field(default=30, ge=10, le=200)
    n: int = Field(default=5, ge=1, le=20)
    periods: int = Field(default=50, ge=5, le=300)
    seed: int = 42


class BacktestResponse(BaseModel):
    game: GameKey
    result: dict[str, Any]
    note: str = "接近随机不代表系统故障，说明缺少显著预测边缘。"


class CheckRequest(BaseModel):
    game: GameKey
    issue: str = Field(..., min_length=1, description="开奖期号，如 2026085 或 26085")
    main: list[int] = Field(..., min_length=1, description="主区号码；复式可多于单式个数")
    special: list[int] = Field(..., min_length=1, description="特区号码；复式可多于单式个数")


class PrizeLevelItem(BaseModel):
    prize_level: int
    prize_name: str
    rule: str
    count: int
    unit_prize: int | None = None
    amount: int | None = None


class CheckResponse(BaseModel):
    game: GameKey
    issue: str
    draw_date: str
    draw_formatted: str
    ticket_formatted: str
    mode: str
    main_selected: int
    special_selected: int
    main_hit: int
    special_hit: int
    total_bets: int
    winning_bets: int
    levels: list[PrizeLevelItem]
    prize_level: int | None
    prize_name: str
    rule: str
    won: bool
    total_prize: int | None = None
    prize_source: str = "none"


class TicketPlanRequest(BaseModel):
    game: GameKey
    mode: Literal["single", "compound"] = "single"
    main_count: int | None = Field(
        default=None, description="复式主区个数；单式可省略，按彩种默认"
    )
    special_count: int | None = Field(
        default=None, description="复式特区个数；单式可省略，按彩种默认"
    )
    window: int = Field(default=50, ge=10, le=200)


class TicketQuoteRequest(BaseModel):
    game: GameKey
    main: list[int] = Field(..., min_length=1)
    special: list[int] = Field(..., min_length=1)


class TicketPlanResponse(BaseModel):
    game: GameKey
    mode: str
    method: str = "top_weight"
    main: list[int]
    special: list[int]
    formatted: str
    formula: str
    unit_bets: str
    bets: int
    price_per_bet: int
    cost: int
    last_issue: str | None = None
    main_count: int
    special_count: int
    main_scores: dict[str, float] | None = None
    special_scores: dict[str, float] | None = None
