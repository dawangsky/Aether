"""基于走势偏斜与专家形态因子生成选号约束 / 权重。"""

from __future__ import annotations

from dataclasses import dataclass

from lottery.analysis.omission import current_omissions, omission_bands
from lottery.analysis.patterns import analyze_main, summarize_history
from lottery.config import GameConfig
from lottery.models import Draw
from lottery.predict.expert import expert_main_weights, expert_special_weights


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
    span_lo: int = 0
    span_hi: int = 99
    repeats_min: int = 0
    repeats_max: int = 3
    neighbors_min: int = 0
    neighbors_max: int = 4
    mod3_max_single: int = 4  # 单路最多号码数，避免 012 路塌缩


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
    if last_pat.sum_value < hist.get("sum_min", 0) + 15:
        center = max(center, median + 10)
    if last_pat.sum_value > hist.get("sum_max", 200) - 15:
        center = min(center, median - 5)
    # 大乐透前区和值经验窗略窄；双色球保持原宽
    sum_pad = 10 if cfg.key == "dlt" else 12
    sum_lo, sum_hi = center - sum_pad, center + sum_pad

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
        if cfg.main_count == 6:
            zone_targets = [(2, 2, 2), (1, 3, 2), (2, 3, 1), (1, 2, 3)]
        else:
            zone_targets = [(2, 2, 1), (1, 2, 2), (2, 1, 2), (1, 3, 1)]

    span_mean = float(hist.get("span_mean", 20))
    span_lo = max(6 if cfg.key == "dlt" else 8, int(span_mean - 10))
    span_hi = min(cfg.main_max - 1, int(span_mean + 12))

    # 重号/邻号：大乐透专家常看 1–2 重、1–2 邻
    if cfg.key == "dlt":
        repeats_min, repeats_max = 0, 2
        neighbors_min, neighbors_max = 0, 3
        mod3_max = 3
    else:
        repeats_min, repeats_max = 0, 3
        neighbors_min, neighbors_max = 0, 3
        mod3_max = 4

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
        span_lo=span_lo,
        span_hi=span_hi,
        repeats_min=repeats_min,
        repeats_max=repeats_max,
        neighbors_min=neighbors_min,
        neighbors_max=neighbors_max,
        mod3_max_single=mod3_max,
    )


def _default_zones(main_count: int) -> list[tuple[int, int, int]]:
    if main_count == 6:
        return [(2, 2, 2), (1, 3, 2), (2, 3, 1), (3, 2, 1), (1, 2, 3)]
    return [(2, 2, 1), (1, 2, 2), (2, 1, 2), (1, 3, 1), (3, 1, 1)]


def main_weights(cfg: GameConfig, draws: list[Draw]) -> dict[int, float]:
    return expert_main_weights(cfg, draws)


def special_weights(cfg: GameConfig, draws: list[Draw]) -> dict[int, float]:
    return expert_special_weights(cfg, draws)


def band_lookup(cfg: GameConfig, draws: list[Draw]) -> dict[int, str]:
    omit = current_omissions(cfg, draws, special=False)
    bands = omission_bands(omit)
    return {n: name for name, nums in bands.items() for n in nums}
