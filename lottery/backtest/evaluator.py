"""滚动回测：量化策略 vs 纯随机基线。"""

from __future__ import annotations

from dataclasses import dataclass
import random

from rich.console import Console
from rich.table import Table

from lottery.config import GameConfig
from lottery.models import Draw
from lottery.predict.generator import generate_tickets, random_tickets

console = Console()


@dataclass
class HitStats:
    main_hits: list[int]
    special_hits: list[int]
    best_main: int
    best_special: int
    avg_main: float
    avg_special: float


def _eval_tickets(tickets, actual: Draw) -> HitStats:
    main_hits = [len(set(t.main) & set(actual.main)) for t in tickets]
    special_hits = [len(set(t.special) & set(actual.special)) for t in tickets]
    return HitStats(
        main_hits=main_hits,
        special_hits=special_hits,
        best_main=max(main_hits) if main_hits else 0,
        best_special=max(special_hits) if special_hits else 0,
        avg_main=sum(main_hits) / len(main_hits) if main_hits else 0.0,
        avg_special=sum(special_hits) / len(special_hits) if special_hits else 0.0,
    )


def run_backtest(
    cfg: GameConfig,
    draws: list[Draw],
    *,
    window: int = 30,
    n_tickets: int = 5,
    periods: int = 50,
    seed: int = 42,
) -> dict:
    if len(draws) < window + 5:
        raise ValueError("历史数据不足以回测，请先 update 拉取更多期数")

    start = max(window, len(draws) - periods)
    rng = random.Random(seed)

    model_best_main: list[int] = []
    model_avg_main: list[float] = []
    model_best_special: list[int] = []
    rand_best_main: list[int] = []
    rand_avg_main: list[float] = []
    rand_best_special: list[int] = []
    detail_rows: list[tuple] = []

    for t in range(start, len(draws)):
        hist = draws[t - window : t]
        actual = draws[t]
        try:
            model_tickets = generate_tickets(cfg, hist, n=n_tickets, seed=seed + t)
        except ValueError:
            continue
        rand_tickets = random_tickets(cfg, n_tickets, rng=rng)
        m = _eval_tickets(model_tickets, actual)
        r = _eval_tickets(rand_tickets, actual)
        model_best_main.append(m.best_main)
        model_avg_main.append(m.avg_main)
        model_best_special.append(m.best_special)
        rand_best_main.append(r.best_main)
        rand_avg_main.append(r.avg_main)
        rand_best_special.append(r.best_special)
        detail_rows.append(
            (
                actual.issue,
                actual.format_numbers(),
                m.best_main,
                m.best_special,
                r.best_main,
                r.best_special,
            )
        )

    def _avg(xs: list[float] | list[int]) -> float:
        return sum(xs) / len(xs) if xs else 0.0

    return {
        "periods": len(model_best_main),
        "window": window,
        "n_tickets": n_tickets,
        "model_avg_best_main": round(_avg(model_best_main), 3),
        "model_avg_main": round(_avg(model_avg_main), 3),
        "model_avg_best_special": round(_avg(model_best_special), 3),
        "rand_avg_best_main": round(_avg(rand_best_main), 3),
        "rand_avg_main": round(_avg(rand_avg_main), 3),
        "rand_avg_best_special": round(_avg(rand_best_special), 3),
        "model_ge3": sum(1 for x in model_best_main if x >= 3),
        "rand_ge3": sum(1 for x in rand_best_main if x >= 3),
        "details": detail_rows[-15:],
    }


def print_backtest(cfg: GameConfig, result: dict) -> None:
    console.rule(f"{cfg.name} 回测报告")
    console.print(
        f"回测期数={result['periods']} 窗口={result['window']} 每期注数={result['n_tickets']}"
    )
    table = Table(title="策略 vs 随机基线（均值）")
    table.add_column("指标")
    table.add_column("量化策略", justify="right")
    table.add_column("随机基线", justify="right")
    table.add_row(
        f"{cfg.main_label}最佳命中均值",
        str(result["model_avg_best_main"]),
        str(result["rand_avg_best_main"]),
    )
    table.add_row(
        f"{cfg.main_label}平均命中",
        str(result["model_avg_main"]),
        str(result["rand_avg_main"]),
    )
    table.add_row(
        f"{cfg.special_label}最佳命中均值",
        str(result["model_avg_best_special"]),
        str(result["rand_avg_best_special"]),
    )
    table.add_row(
        f"{cfg.main_label}≥3 期数",
        str(result["model_ge3"]),
        str(result["rand_ge3"]),
    )
    console.print(table)

    detail = Table(title="最近回测明细（最佳命中）")
    detail.add_column("期号")
    detail.add_column("实际开奖")
    detail.add_column("策略主", justify="right")
    detail.add_column("策略特", justify="right")
    detail.add_column("随机主", justify="right")
    detail.add_column("随机特", justify="right")
    for row in result["details"]:
        detail.add_row(*[str(x) for x in row])
    console.print(detail)
    console.print(
        "[dim]回测仅验证统计约束的历史拟合，不代表未来可预测；"
        "若策略与随机接近，说明无显著边缘。[/dim]"
    )
