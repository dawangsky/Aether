"""基于走势偏斜生成选号约束。"""

from __future__ import annotations

from dataclasses import dataclass

from lottery.analysis.omission import current_omissions, omission_bands
from lottery.analysis.patterns import analyze_main, summarize_history
from lottery.config import GameConfig
from lottery.models import Draw


@dataclass
class PredictConstraints:
    sum_lo: int
    sum_hi: int
    odd_min: int
    odd_max: int
    big_min: int
    big_max: int
    zone_targets: list[tuple[int, int, int]]
    consec_min: int
    consec_max: int
    hot_band_min: int
    hot_band_max: int
    cold_band_min: int
    cold_band_max: int
    prefer_rebalance_empty_zone: bool


def build_constraints(cfg: GameConfig, draws: list[Draw]) -> PredictConstraints:
    hist = summarize_history(cfg, draws)
    last = draws[-1]
    prev = draws[-2] if len(draws) > 1 else None
    last_pat = analyze_main(
        cfg,
        last.main_sorted(),
        prev_main=prev.main_sorted() if prev else None,
    )

    median = int(hist.get("sum_median", 100))
    mean = float(hist.get("sum_mean", median))
    center = int(round((median + mean) / 2))
    # 极端偏斜时向中枢回拉
    if last_pat.sum_value < hist.get("sum_min", 0) + 15:
        center = max(center, median + 10)
    if last_pat.sum_value > hist.get("sum_max", 200) - 15:
        center = min(center, median - 5)
    sum_lo, sum_hi = center - 12, center + 12

    odd_min, odd_max = 2, cfg.main_count - 1
    if last_pat.odd_even[0] <= 1:
        odd_min = max(odd_min, 3)
    if last_pat.odd_even[1] <= 1:
        odd_max = min(odd_max, cfg.main_count - 2)

    big_min, big_max = 1, cfg.main_count - 1
    if last_pat.big_small[0] == 0:
        big_min = 2
    if last_pat.big_small[1] == 0:
        big_max = cfg.main_count - 2

    empty_zones = [i + 1 for i, c in enumerate(last_pat.zones) if c == 0]
    zone_targets = _default_zones(cfg.main_count)
    if empty_zones:
        # 优先带空区回补的均衡形态
        if cfg.main_count == 6:
            zone_targets = [(2, 2, 2), (1, 3, 2), (2, 3, 1), (1, 2, 3)]
        else:
            zone_targets = [(2, 2, 1), (1, 2, 2), (2, 1, 2), (1, 3, 1)]

    return PredictConstraints(
        sum_lo=sum_lo,
        sum_hi=sum_hi,
        odd_min=odd_min,
        odd_max=odd_max,
        big_min=big_min,
        big_max=big_max,
        zone_targets=zone_targets,
        consec_min=0,
        consec_max=2,
        hot_band_min=max(2, cfg.main_count // 2 - 1),
        hot_band_max=cfg.main_count - 1,
        cold_band_min=0,
        cold_band_max=2,
        prefer_rebalance_empty_zone=bool(empty_zones),
    )


def _default_zones(main_count: int) -> list[tuple[int, int, int]]:
    if main_count == 6:
        return [(2, 2, 2), (1, 3, 2), (2, 3, 1), (3, 2, 1), (1, 2, 3)]
    return [(2, 2, 1), (1, 2, 2), (2, 1, 2), (1, 3, 1), (3, 1, 1)]


def main_weights(cfg: GameConfig, draws: list[Draw]) -> dict[int, float]:
    """热号加权 + 过冷回补加权。"""
    from lottery.analysis.frequency import frequency_map

    freq = frequency_map(draws, special=False)
    omit = current_omissions(cfg, draws, special=False)
    weights: dict[int, float] = {}
    for n in cfg.main_range:
        hot = 1.0 + freq.get(n, 0) * 0.35
        cold_boost = 1.0 + max(0, omit.get(n, 0) - 6) * 0.18
        weights[n] = hot * cold_boost
    return weights


def special_weights(cfg: GameConfig, draws: list[Draw]) -> dict[int, float]:
    from lottery.analysis.frequency import frequency_map

    freq = frequency_map(draws, special=True)
    omit = current_omissions(cfg, draws, special=True)
    weights: dict[int, float] = {}
    for n in cfg.special_range:
        hot = 1.0 + freq.get(n, 0) * 0.4
        cold_boost = 1.0 + max(0, omit.get(n, 0) - 4) * 0.25
        # 奇偶回补：若近窗偶号过多，抬高奇数权重
        recent = [s for d in draws[-10:] for s in d.special]
        even_ratio = sum(1 for x in recent if x % 2 == 0) / max(1, len(recent))
        parity = 1.15 if (even_ratio > 0.6 and n % 2 == 1) or (
            even_ratio < 0.4 and n % 2 == 0
        ) else 1.0
        weights[n] = hot * cold_boost * parity
    return weights


def band_lookup(cfg: GameConfig, draws: list[Draw]) -> dict[int, str]:
    omit = current_omissions(cfg, draws, special=False)
    bands = omission_bands(omit)
    return {n: name for name, nums in bands.items() for n in nums}
