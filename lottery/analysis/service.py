"""API 用的结构化分析服务（与 Rich 报表解耦）。"""

from __future__ import annotations

from typing import Any

from lottery.analysis.frequency import ranked_frequency
from lottery.analysis.omission import average_omissions, current_omissions, omission_bands
from lottery.analysis.patterns import analyze_main, summarize_history
from lottery.config import GameConfig
from lottery.models import Draw


def build_analyze_payload(cfg: GameConfig, draws: list[Draw], window: int) -> dict[str, Any]:
    window_draws = draws[-window:] if len(draws) > window else draws
    if not window_draws:
        raise ValueError("无历史数据，请先更新开奖")

    last = window_draws[-1]
    prev = window_draws[-2] if len(window_draws) > 1 else None
    pat = analyze_main(
        cfg,
        last.main_sorted(),
        prev_main=prev.main_sorted() if prev else None,
    )
    hist = summarize_history(cfg, window_draws)
    main_omit = current_omissions(cfg, window_draws, special=False)
    special_omit = current_omissions(cfg, window_draws, special=True)
    main_avg = average_omissions(cfg, window_draws, special=False)
    special_avg = average_omissions(cfg, window_draws, special=True)
    bands = omission_bands(main_omit)

    def _omit_rows(omit: dict[int, int], avg: dict[int, float], top: int = 12) -> list[dict]:
        ranked = sorted(omit.items(), key=lambda x: (-x[1], x[0]))[:top]
        return [
            {"number": n, "current": miss, "average": round(avg[n], 2)}
            for n, miss in ranked
        ]

    return {
        "game": cfg.key,
        "window": len(window_draws),
        "last_draw": {
            "issue": last.issue,
            "date": last.date,
            "main": list(last.main_sorted()),
            "special": list(last.special_sorted()),
            "formatted": last.format_numbers(),
        },
        "last_pattern": {
            "sum": pat.sum_value,
            "span": pat.span,
            "odd_even": f"{pat.odd_even[0]}:{pat.odd_even[1]}",
            "big_small": f"{pat.big_small[0]}:{pat.big_small[1]}",
            "zones": f"{pat.zones[0]}:{pat.zones[1]}:{pat.zones[2]}",
            "consecutive_groups": pat.consecutive_groups,
            "repeats": pat.repeats,
            "neighbors": pat.neighbors,
        },
        "history_summary": hist,
        "main_hot": [
            {"number": n, "count": c}
            for n, c in ranked_frequency(cfg, window_draws, special=False)[:10]
        ],
        "main_cold": [
            {"number": n, "count": c}
            for n, c in list(reversed(ranked_frequency(cfg, window_draws, special=False)[-10:]))
        ],
        "special_hot": [
            {"number": n, "count": c}
            for n, c in ranked_frequency(cfg, window_draws, special=True)[:8]
        ],
        "main_omissions": _omit_rows(main_omit, main_avg),
        "special_omissions": _omit_rows(special_omit, special_avg),
        "omission_bands": {k: v for k, v in bands.items()},
        "disclaimer": "仅供研究娱乐，开奖随机，不构成投注建议。",
    }
