"""投注方案：单式 / 复式选号池、注数与费用。"""

from __future__ import annotations

from math import comb
from typing import Any, Sequence

from lottery.config import GameConfig
from lottery.models import Draw
from lottery.predict.constraints import main_weights, special_weights

PRICE_PER_BET = 2  # 人民币元 / 注


def validate_counts(cfg: GameConfig, main_count: int, special_count: int) -> None:
    if main_count < cfg.main_count or main_count > cfg.main_max:
        raise ValueError(f"主区个数需在 {cfg.main_count}–{cfg.main_max} 之间，当前 {main_count}")
    if special_count < cfg.special_count or special_count > cfg.special_max:
        raise ValueError(
            f"特区个数需在 {cfg.special_count}–{cfg.special_max} 之间，当前 {special_count}"
        )


def bet_count(cfg: GameConfig, main_count: int, special_count: int) -> int:
    validate_counts(cfg, main_count, special_count)
    return comb(main_count, cfg.main_count) * comb(special_count, cfg.special_count)


def ticket_cost(cfg: GameConfig, main_count: int, special_count: int) -> dict[str, Any]:
    bets = bet_count(cfg, main_count, special_count)
    mode = "single" if (main_count == cfg.main_count and special_count == cfg.special_count) else "compound"
    return {
        "mode": mode,
        "main_count": main_count,
        "special_count": special_count,
        "formula": f"{main_count}+{special_count}",
        "unit_bets": f"C({main_count},{cfg.main_count})×C({special_count},{cfg.special_count})",
        "bets": bets,
        "price_per_bet": PRICE_PER_BET,
        "cost": bets * PRICE_PER_BET,
    }


def _top_by_weight(pool: Sequence[int], weights: dict[int, float], k: int) -> list[int]:
    """按权重降序取前 k；同分按号码升序，保证同一数据下结果确定。"""
    ranked = sorted(pool, key=lambda n: (-float(weights.get(n, 0.0)), n))
    return ranked[:k]


def generate_pool(
    cfg: GameConfig,
    draws: list[Draw],
    *,
    main_count: int | None = None,
    special_count: int | None = None,
) -> dict[str, Any]:
    """按因子权重取 Top-K 选号池（确定性推荐，非随机抽样）。"""
    if len(draws) < 5:
        raise ValueError("历史数据不足，请先同步开奖数据")

    m = cfg.main_count if main_count is None else main_count
    s = cfg.special_count if special_count is None else special_count
    validate_counts(cfg, m, s)

    mw = main_weights(cfg, draws)
    sw = special_weights(cfg, draws)
    main = tuple(sorted(_top_by_weight(list(cfg.main_range), mw, m)))
    special = tuple(sorted(_top_by_weight(list(cfg.special_range), sw, s)))
    quote = ticket_cost(cfg, m, s)
    return {
        "game": cfg.key,
        "method": "top_weight",
        "main": list(main),
        "special": list(special),
        "main_scores": {str(n): round(float(mw.get(n, 0.0)), 4) for n in main},
        "special_scores": {str(n): round(float(sw.get(n, 0.0)), 4) for n in special},
        "formatted": " ".join(f"{n:02d}" for n in main)
        + " + "
        + " ".join(f"{n:02d}" for n in special),
        "last_issue": draws[-1].issue,
        **quote,
    }
