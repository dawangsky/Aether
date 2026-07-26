"""约束 + 加权采样生成推荐注。"""

from __future__ import annotations

import random
from typing import Sequence

from lottery.analysis.omission import band_hit_counts, current_omissions
from lottery.analysis.patterns import analyze_main
from lottery.config import GameConfig
from lottery.models import Draw, Ticket
from lottery.predict.constraints import (
    PredictConstraints,
    band_lookup,
    build_constraints,
    main_weights,
    special_weights,
)


def _weighted_sample(pool: Sequence[int], weights: dict[int, float], k: int, rng: random.Random) -> list[int]:
    chosen: list[int] = []
    available = list(pool)
    while len(chosen) < k and available:
        ws = [max(0.01, weights.get(n, 1.0)) for n in available]
        pick = rng.choices(available, weights=ws, k=1)[0]
        chosen.append(pick)
        available.remove(pick)
    return chosen


def _passes(cfg: GameConfig, main: list[int], cons: PredictConstraints, bands: dict[int, str]) -> bool:
    nums = tuple(sorted(main))
    pat = analyze_main(cfg, nums)
    if not (cons.sum_lo <= pat.sum_value <= cons.sum_hi):
        return False
    if not (cons.odd_min <= pat.odd_even[0] <= cons.odd_max):
        return False
    if not (cons.big_min <= pat.big_small[0] <= cons.big_max):
        return False
    if cons.zone_targets and pat.zones not in cons.zone_targets:
        return False
    if not (cons.consec_min <= pat.consecutive_groups <= cons.consec_max):
        return False
    hot = sum(1 for n in nums if bands.get(n) in ("0-2", "3-4"))
    cold = sum(1 for n in nums if bands.get(n) in (">=8",))
    if not (cons.hot_band_min <= hot <= cons.hot_band_max):
        return False
    if not (cons.cold_band_min <= cold <= cons.cold_band_max):
        return False
    return True


def generate_tickets(
    cfg: GameConfig,
    draws: list[Draw],
    n: int = 2,
    *,
    seed: int | None = None,
    max_tries: int = 8000,
) -> list[Ticket]:
    if len(draws) < 5:
        raise ValueError("历史数据不足，请先 update 拉取更多期数")

    rng = random.Random(seed)
    cons = build_constraints(cfg, draws)
    mw = main_weights(cfg, draws)
    sw = special_weights(cfg, draws)
    bands = band_lookup(cfg, draws)
    omit = current_omissions(cfg, draws, special=False)
    prev = draws[-1].main_sorted()

    tickets: list[Ticket] = []
    seen: set[tuple[int, ...]] = set()
    tries = 0
    while len(tickets) < n and tries < max_tries:
        tries += 1
        main = _weighted_sample(list(cfg.main_range), mw, cfg.main_count, rng)
        if not _passes(cfg, main, cons, bands):
            continue
        key = tuple(sorted(main))
        if key in seen:
            continue
        special = tuple(
            sorted(_weighted_sample(list(cfg.special_range), sw, cfg.special_count, rng))
        )
        pat = analyze_main(cfg, key, prev_main=prev)
        band_counts = band_hit_counts(omit, key)
        tickets.append(
            Ticket(
                main=key,
                special=special,
                meta={
                    "sum": pat.sum_value,
                    "odd_even": f"{pat.odd_even[0]}:{pat.odd_even[1]}",
                    "big_small": f"{pat.big_small[0]}:{pat.big_small[1]}",
                    "zones": f"{pat.zones[0]}:{pat.zones[1]}:{pat.zones[2]}",
                    "bands": ",".join(f"{k}:{v}" for k, v in band_counts.items()),
                    "consec": pat.consecutive_groups,
                    "repeats": pat.repeats,
                },
            )
        )
        seen.add(key)

    # 约束过严时放宽重试
    if len(tickets) < n:
        loose = PredictConstraints(
            sum_lo=cons.sum_lo - 20,
            sum_hi=cons.sum_hi + 20,
            odd_min=1,
            odd_max=cfg.main_count - 1,
            big_min=1,
            big_max=cfg.main_count - 1,
            zone_targets=[],
            consec_min=0,
            consec_max=3,
            hot_band_min=0,
            hot_band_max=cfg.main_count,
            cold_band_min=0,
            cold_band_max=cfg.main_count,
            prefer_rebalance_empty_zone=False,
        )
        while len(tickets) < n and tries < max_tries * 2:
            tries += 1
            main = _weighted_sample(list(cfg.main_range), mw, cfg.main_count, rng)
            if not _passes(cfg, main, loose, bands):
                continue
            key = tuple(sorted(main))
            if key in seen:
                continue
            special = tuple(
                sorted(_weighted_sample(list(cfg.special_range), sw, cfg.special_count, rng))
            )
            pat = analyze_main(cfg, key, prev_main=prev)
            band_counts = band_hit_counts(omit, key)
            tickets.append(
                Ticket(
                    main=key,
                    special=special,
                    meta={
                        "sum": pat.sum_value,
                        "odd_even": f"{pat.odd_even[0]}:{pat.odd_even[1]}",
                        "big_small": f"{pat.big_small[0]}:{pat.big_small[1]}",
                        "zones": f"{pat.zones[0]}:{pat.zones[1]}:{pat.zones[2]}",
                        "bands": ",".join(f"{k}:{v}" for k, v in band_counts.items()),
                        "consec": pat.consecutive_groups,
                        "repeats": pat.repeats,
                        "relaxed": True,
                    },
                )
            )
            seen.add(key)

    return tickets


def random_tickets(cfg: GameConfig, n: int, rng: random.Random | None = None) -> list[Ticket]:
    rng = rng or random.Random()
    out: list[Ticket] = []
    for _ in range(n):
        main = tuple(sorted(rng.sample(list(cfg.main_range), cfg.main_count)))
        special = tuple(sorted(rng.sample(list(cfg.special_range), cfg.special_count)))
        out.append(Ticket(main=main, special=special))
    return out
