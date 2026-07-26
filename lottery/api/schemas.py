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
