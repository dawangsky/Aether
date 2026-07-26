"""形态指标：奇偶、大小、三区、和值、连号、重号、邻号、012路。"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from lottery.config import GameConfig
from lottery.models import Draw


@dataclass
class PatternStats:
    sum_value: int
    span: int
    odd_even: tuple[int, int]
    big_small: tuple[int, int]
    zones: tuple[int, int, int]
    consecutive_groups: int
    mod3: tuple[int, int, int]
    repeats: int
    neighbors: int

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def zone_of(n: int, cfg: GameConfig) -> int:
    a, b = cfg.zone_edges
    if n <= a:
        return 1
    if n <= b:
        return 2
    return 3


def consecutive_groups(nums: tuple[int, ...] | list[int]) -> int:
    ordered = sorted(nums)
    if not ordered:
        return 0
    groups = 0
    run = 1
    for i in range(1, len(ordered)):
        if ordered[i] == ordered[i - 1] + 1:
            run += 1
        else:
            if run >= 2:
                groups += 1
            run = 1
    if run >= 2:
        groups += 1
    return groups


def neighbor_set(prev: tuple[int, ...]) -> set[int]:
    s: set[int] = set()
    for n in prev:
        s.add(n - 1)
        s.add(n + 1)
    return s - set(prev)


def analyze_main(
    cfg: GameConfig,
    main: tuple[int, ...] | list[int],
    *,
    prev_main: tuple[int, ...] | None = None,
) -> PatternStats:
    nums = tuple(sorted(main))
    odd = sum(1 for n in nums if n % 2 == 1)
    big = sum(1 for n in nums if n >= cfg.size_split)
    z1 = sum(1 for n in nums if zone_of(n, cfg) == 1)
    z2 = sum(1 for n in nums if zone_of(n, cfg) == 2)
    z3 = sum(1 for n in nums if zone_of(n, cfg) == 3)
    mod3 = (
        sum(1 for n in nums if n % 3 == 0),
        sum(1 for n in nums if n % 3 == 1),
        sum(1 for n in nums if n % 3 == 2),
    )
    repeats = 0
    neighbors = 0
    if prev_main is not None:
        repeats = len(set(nums) & set(prev_main))
        neighbors = len(set(nums) & neighbor_set(prev_main))
    return PatternStats(
        sum_value=sum(nums),
        span=(nums[-1] - nums[0]) if nums else 0,
        odd_even=(odd, len(nums) - odd),
        big_small=(big, len(nums) - big),
        zones=(z1, z2, z3),
        consecutive_groups=consecutive_groups(nums),
        mod3=mod3,
        repeats=repeats,
        neighbors=neighbors,
    )


def summarize_history(cfg: GameConfig, draws: list[Draw]) -> dict[str, Any]:
    if not draws:
        return {}
    patterns = []
    for i, d in enumerate(draws):
        prev = draws[i - 1].main_sorted() if i > 0 else None
        patterns.append(analyze_main(cfg, d.main_sorted(), prev_main=prev))
    sums = [p.sum_value for p in patterns]
    spans = [p.span for p in patterns]
    return {
        "count": len(patterns),
        "sum_mean": round(sum(sums) / len(sums), 2),
        "sum_median": sorted(sums)[len(sums) // 2],
        "sum_min": min(sums),
        "sum_max": max(sums),
        "span_mean": round(sum(spans) / len(spans), 2),
        "odd_even_modes": _mode_tuple([p.odd_even for p in patterns]),
        "big_small_modes": _mode_tuple([p.big_small for p in patterns]),
        "zone_modes": _mode_tuple([p.zones for p in patterns]),
        "avg_consecutive": round(
            sum(p.consecutive_groups for p in patterns) / len(patterns), 2
        ),
        "avg_repeats": round(sum(p.repeats for p in patterns) / len(patterns), 2),
    }


def _mode_tuple(items: list[tuple]) -> list[tuple]:
    from collections import Counter

    c = Counter(items)
    return c.most_common(3)
