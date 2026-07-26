"""冷热频次统计。"""

from __future__ import annotations

from collections import Counter

from lottery.config import GameConfig
from lottery.models import Draw


def frequency_map(draws: list[Draw], *, special: bool = False) -> Counter[int]:
    counter: Counter[int] = Counter()
    for d in draws:
        nums = d.special if special else d.main
        counter.update(nums)
    return counter


def ranked_frequency(
    cfg: GameConfig,
    draws: list[Draw],
    *,
    special: bool = False,
) -> list[tuple[int, int]]:
    span = cfg.special_range if special else cfg.main_range
    freq = frequency_map(draws, special=special)
    return sorted(((n, freq.get(n, 0)) for n in span), key=lambda x: (-x[1], x[0]))
