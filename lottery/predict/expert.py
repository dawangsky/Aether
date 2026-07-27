"""大乐透/双色球常见「专家形态」因子：研究向权重与分层选号。

参考业界常用分析维度（非官方模型、不构成投注建议）：
- 多窗口冷热（近 10 / 30 / 全窗）
- 遗漏回补（当前遗漏相对历史均遗漏）
- 上期重号 / 邻号
- 空区回补、012 路偏斜回拉
- 质数号微权重（前区常见质合讨论）
- 分层配号：热 + 温 + 冷，避免纯热号堆叠
"""

from __future__ import annotations

from collections import Counter
from typing import Sequence

from lottery.analysis.frequency import frequency_map
from lottery.analysis.omission import average_omissions, current_omissions
from lottery.analysis.patterns import neighbor_set, zone_of
from lottery.config import GameConfig
from lottery.models import Draw

# 1–35 内质数（覆盖双色球红球与大乐透前区）
_PRIMES = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31}


def _freq_window(draws: list[Draw], *, special: bool, last_n: int | None) -> Counter[int]:
    subset = draws if last_n is None else draws[-last_n:]
    return frequency_map(subset, special=special)


def expert_main_weights(cfg: GameConfig, draws: list[Draw]) -> dict[int, float]:
    """前区/红球多因子权重。"""
    omit = current_omissions(cfg, draws, special=False)
    avg_omit = average_omissions(cfg, draws, special=False)
    f10 = _freq_window(draws, special=False, last_n=10)
    f30 = _freq_window(draws, special=False, last_n=30)
    fall = _freq_window(draws, special=False, last_n=None)

    last = draws[-1].main_sorted()
    prev_set = set(last)
    neigh = neighbor_set(last)
    empty_zones = {z for z in (1, 2, 3) if sum(1 for n in last if zone_of(n, cfg) == z) == 0}

    # 近 5 期 012 路占比，抬高偏少一路
    recent_mains = [n for d in draws[-5:] for n in d.main]
    mod_counts = [sum(1 for n in recent_mains if n % 3 == r) for r in (0, 1, 2)]
    mod_total = max(1, sum(mod_counts))
    mod_share = [c / mod_total for c in mod_counts]
    weak_mod = min(range(3), key=lambda r: mod_share[r])

    weights: dict[int, float] = {}
    for n in cfg.main_range:
        w = 1.0
        w *= 1.0 + f10.get(n, 0) * 0.55
        w *= 1.0 + f30.get(n, 0) * 0.28
        w *= 1.0 + fall.get(n, 0) * 0.12

        miss = omit.get(n, 0)
        avg = max(1.0, float(avg_omit.get(n, miss or 1)))
        ratio = miss / avg
        if miss <= 1:
            w *= 1.08  # 热号微抬
        elif 0.75 <= ratio <= 1.35:
            w *= 1.32  # 遗漏回补窗口（专家常用「到平均遗漏附近关注」）
        elif ratio > 1.6:
            w *= 1.12 + min(0.45, (ratio - 1.6) * 0.12)  # 过冷温补，避免无限抬冷号

        if n in prev_set:
            w *= 1.14  # 重号
        if n in neigh:
            w *= 1.22  # 邻号

        z = zone_of(n, cfg)
        if z in empty_zones:
            w *= 1.18  # 空区回补

        if n % 3 == weak_mod:
            w *= 1.1  # 012 路回拉

        if n in _PRIMES:
            w *= 1.04  # 质数微权重（大乐透前区质合讨论）

        # 尾数过热抑制：近 10 期同尾过多则略降
        tail = n % 10
        tail_hits = sum(1 for x in (m for d in draws[-10:] for m in d.main) if x % 10 == tail)
        if tail_hits >= 6:
            w *= 0.92

        weights[n] = max(0.05, w)
    return weights


def expert_special_weights(cfg: GameConfig, draws: list[Draw]) -> dict[int, float]:
    """后区/蓝球多因子权重。"""
    omit = current_omissions(cfg, draws, special=True)
    avg_omit = average_omissions(cfg, draws, special=True)
    f10 = _freq_window(draws, special=True, last_n=10)
    f30 = _freq_window(draws, special=True, last_n=30)
    fall = _freq_window(draws, special=True, last_n=None)

    last_sp = tuple(sorted(draws[-1].special))
    prev_set = set(last_sp)
    neigh = neighbor_set(last_sp) if last_sp else set()

    recent = [s for d in draws[-12:] for s in d.special]
    even_ratio = sum(1 for x in recent if x % 2 == 0) / max(1, len(recent))

    weights: dict[int, float] = {}
    for n in cfg.special_range:
        w = 1.0
        w *= 1.0 + f10.get(n, 0) * 0.6
        w *= 1.0 + f30.get(n, 0) * 0.3
        w *= 1.0 + fall.get(n, 0) * 0.15

        miss = omit.get(n, 0)
        avg = max(1.0, float(avg_omit.get(n, miss or 1)))
        ratio = miss / avg
        if miss <= 1:
            w *= 1.1
        elif 0.7 <= ratio <= 1.4:
            w *= 1.35
        elif ratio > 1.5:
            w *= 1.15 + min(0.5, (ratio - 1.5) * 0.15)

        if n in prev_set:
            w *= 1.12
        if n in neigh:
            w *= 1.2

        # 奇偶回补
        if (even_ratio > 0.58 and n % 2 == 1) or (even_ratio < 0.42 and n % 2 == 0):
            w *= 1.16

        # 大乐透后区：大小分界约 7
        if cfg.key == "dlt":
            recent_big = sum(1 for x in recent if x >= 7) / max(1, len(recent))
            if recent_big > 0.6 and n < 7:
                w *= 1.12
            elif recent_big < 0.4 and n >= 7:
                w *= 1.12

        weights[n] = max(0.05, w)
    return weights


def _band_of(omit: int) -> str:
    if omit <= 3:
        return "hot"
    if omit <= 7:
        return "warm"
    return "cold"


def _quotas(k: int) -> tuple[int, int, int]:
    """热 / 温 / 冷 目标个数。"""
    if k <= 2:
        return 1, max(0, k - 1), 0
    if k == 5:  # 大乐透前区常见配比思路
        return 2, 2, 1
    if k == 6:  # 双色球
        return 3, 2, 1
    hot = max(1, k // 2)
    cold = 1 if k >= 4 else 0
    warm = k - hot - cold
    return hot, warm, cold


def diversified_select(
    cfg: GameConfig,
    draws: list[Draw],
    weights: dict[int, float],
    k: int,
    *,
    special: bool = False,
) -> list[int]:
    """分层配号：按权重在热/温/冷层取号，再做区间与奇偶微调。"""
    omit = current_omissions(cfg, draws, special=special)
    pool = list(cfg.special_range if special else cfg.main_range)
    ranked = sorted(pool, key=lambda n: (-float(weights.get(n, 0.0)), n))

    by_band: dict[str, list[int]] = {"hot": [], "warm": [], "cold": []}
    for n in ranked:
        by_band[_band_of(omit.get(n, 0))].append(n)

    if special:
        # 后区/蓝球个数少：直接取权重 Top，再尽量奇偶搭配
        chosen = ranked[:k]
        if k >= 2 and len({x % 2 for x in chosen}) == 1:
            want_parity = 1 - (chosen[0] % 2)
            for n in ranked[k:]:
                if n % 2 == want_parity:
                    chosen[-1] = n
                    break
        # 大乐透后区尽量避免双连号（除非权重极高）
        if cfg.key == "dlt" and k == 2:
            a, b = sorted(chosen)
            if b == a + 1:
                for n in ranked:
                    if n not in chosen and abs(n - a) > 1 and abs(n - b) > 1:
                        # 替换权重较低者
                        weaker = a if weights.get(a, 0) <= weights.get(b, 0) else b
                        chosen = [x for x in chosen if x != weaker] + [n]
                        break
        return sorted(chosen)[:k]

    q_hot, q_warm, q_cold = _quotas(k)
    chosen: list[int] = []
    for band, need in (("hot", q_hot), ("warm", q_warm), ("cold", q_cold)):
        for n in by_band[band]:
            if len([x for x in chosen if _band_of(omit.get(x, 0)) == band]) >= need:
                break
            if n not in chosen:
                chosen.append(n)

    for n in ranked:
        if len(chosen) >= k:
            break
        if n not in chosen:
            chosen.append(n)
    chosen = chosen[:k]

    # 区间补缺：若缺某一区，用该区最高权号替换同区外最弱号
    if not special and k >= 3:
        for z in (1, 2, 3):
            if any(zone_of(n, cfg) == z for n in chosen):
                continue
            cand = next((n for n in ranked if zone_of(n, cfg) == z and n not in chosen), None)
            if cand is None:
                continue
            # 替换权重最低且不在该区的号
            victims = [n for n in chosen if zone_of(n, cfg) != z]
            if not victims:
                continue
            victim = min(victims, key=lambda n: (weights.get(n, 0.0), -n))
            chosen = [cand if x == victim else x for x in chosen]

    # 奇偶极端修正
    odd = sum(1 for n in chosen if n % 2 == 1)
    if odd == 0 or odd == k:
        want = 1 if odd == 0 else 0
        for n in ranked:
            if n in chosen or n % 2 != want:
                continue
            victim = min(
                (x for x in chosen if x % 2 != want),
                key=lambda x: (weights.get(x, 0.0), -x),
                default=None,
            )
            if victim is None:
                break
            chosen = [n if x == victim else x for x in chosen]
            break

    return sorted(chosen)[:k]


def factor_snapshot(cfg: GameConfig, draws: list[Draw]) -> dict[str, object]:
    """供 UI/API 展示的策略摘要。"""
    last = draws[-1]
    omit = current_omissions(cfg, draws, special=False)
    return {
        "strategy": "expert_v1",
        "label": "专家形态加权 + 冷热分层配号",
        "ref_issue": last.issue,
        "main_hot": sorted(n for n, m in omit.items() if m <= 3)[:8],
        "main_cold": sorted(n for n, m in omit.items() if m >= 8)[:8],
        "last_main": list(last.main_sorted()),
        "neighbors": sorted(neighbor_set(last.main_sorted()))[:10],
        "notes": [
            "多窗口冷热（10/30/全窗）",
            "遗漏回补窗口",
            "重号与邻号",
            "空区与 012 路回拉",
            "热温冷分层配号（避免纯热堆叠）",
        ],
    }
