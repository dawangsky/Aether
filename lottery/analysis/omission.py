"""遗漏值与遗漏分层。"""

from __future__ import annotations

from lottery.config import GameConfig
from lottery.models import Draw

OMISSION_BANDS = (
    ("0-2", 0, 2),
    ("3-4", 3, 4),
    ("5-7", 5, 7),
    (">=8", 8, 10_000),
)


def current_omissions(
    cfg: GameConfig,
    draws: list[Draw],
    *,
    special: bool = False,
) -> dict[int, int]:
    """号码当前遗漏：距最近一次开出的期数；从未开出则为窗口长度。"""
    span = list(cfg.special_range if special else cfg.main_range)
    last_seen = {n: None for n in span}
    for idx, draw in enumerate(draws):
        nums = draw.special if special else draw.main
        for n in nums:
            if n in last_seen:
                last_seen[n] = idx
    end = len(draws) - 1
    result: dict[int, int] = {}
    for n, seen in last_seen.items():
        result[n] = end - seen if seen is not None else len(draws)
    return result


def average_omissions(
    cfg: GameConfig,
    draws: list[Draw],
    *,
    special: bool = False,
) -> dict[int, float]:
    span = list(cfg.special_range if special else cfg.main_range)
    gaps: dict[int, list[int]] = {n: [] for n in span}
    last: dict[int, int | None] = {n: None for n in span}
    for idx, draw in enumerate(draws):
        nums = set(draw.special if special else draw.main)
        for n in span:
            if n in nums:
                if last[n] is not None:
                    gaps[n].append(idx - last[n] - 1)
                last[n] = idx
    avg: dict[int, float] = {}
    for n in span:
        avg[n] = sum(gaps[n]) / len(gaps[n]) if gaps[n] else float(len(draws))
    return avg


def omission_bands(omissions: dict[int, int]) -> dict[str, list[int]]:
    bands: dict[str, list[int]] = {name: [] for name, _, _ in OMISSION_BANDS}
    for n, miss in sorted(omissions.items()):
        for name, lo, hi in OMISSION_BANDS:
            if lo <= miss <= hi:
                bands[name].append(n)
                break
    return bands


def band_hit_counts(omissions: dict[int, int], drawn: tuple[int, ...]) -> dict[str, int]:
    bands = omission_bands(omissions)
    inverted = {n: name for name, nums in bands.items() for n in nums}
    counts = {name: 0 for name, _, _ in OMISSION_BANDS}
    for n in drawn:
        name = inverted.get(n)
        if name:
            counts[name] += 1
    return counts
