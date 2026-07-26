"""FastAPI 应用工厂。"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from lottery import __version__
from lottery.api.routes import router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Lottery Quant API",
        description="双色球/大乐透量化分析预测本地 API（研究娱乐用途）",
        version=__version__,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
    return app


app = create_app()
