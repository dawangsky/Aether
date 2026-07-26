"""按期号核对投注号码中奖（支持单式 / 复式）。"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import comb

from lottery.config import GameConfig, get_game
from lottery.models import Draw

# 大乐透自 2026014 期起改为 7 个奖级
DLT_NEW_RULES_FROM = 2026014

# 官网缺奖金时的固定奖兜底（浮动奖不兜底）
_SSQ_FIXED_FALLBACK = {3: 3000, 4: 200, 5: 10, 6: 5}
_DLT_OLD_FIXED_FALLBACK = {3: 10000, 4: 3000, 5: 300, 6: 200, 7: 100, 8: 15, 9: 5}
# 新规固定奖随奖池档位变化，缺官网数据时不臆造


@dataclass(frozen=True)
class PrizeLevelCount:
    prize_level: int
    prize_name: str
    rule: str  # 紧凑命中规则，如 "2+1 1+1 0+1"
    count: int
    unit_prize: int | None  # 单注奖金（元），无数据为 None
    amount: int | None  # 该奖等合计奖金


@dataclass(frozen=True)
class PrizeResult:
    game: str
    issue: str
    draw_date: str
    draw_formatted: str
    ticket_formatted: str
    mode: str  # single | compound
    main_selected: int
    special_selected: int
    main_hit: int  # 所选号码中命中开奖的个数（复式池命中）
    special_hit: int
    total_bets: int
    winning_bets: int
    levels: tuple[PrizeLevelCount, ...]
    prize_level: int | None  # 最高奖等；未中奖为 None
    prize_name: str
    rule: str
    total_prize: int | None  # 合计奖金；任一档缺数据则为 None
    prize_source: str  # official | fallback | mixed | none

    @property
    def won(self) -> bool:
        return self.winning_bets > 0

    def as_dict(self) -> dict:
        d = asdict(self)
        d["won"] = self.won
        return d


def normalize_issue(issue: str) -> str:
    s = "".join(ch for ch in str(issue).strip() if ch.isdigit())
    if len(s) == 5:
        return f"20{s}"
    return s


def _fmt(main: tuple[int, ...] | list[int], special: tuple[int, ...] | list[int]) -> str:
    m = " ".join(f"{n:02d}" for n in sorted(main))
    s = " ".join(f"{n:02d}" for n in sorted(special))
    return f"{m} + {s}"


def _compact_rule(main_hit: int, special_hit: int) -> str:
    return f"{main_hit}+{special_hit}"


def _ssq_prize(main_hit: int, special_hit: int) -> tuple[int | None, str, str]:
    table = {
        (6, 1): (1, "一等奖"),
        (6, 0): (2, "二等奖"),
        (5, 1): (3, "三等奖"),
        (5, 0): (4, "四等奖"),
        (4, 1): (4, "四等奖"),
        (4, 0): (5, "五等奖"),
        (3, 1): (5, "五等奖"),
        (2, 1): (6, "六等奖"),
        (1, 1): (6, "六等奖"),
        (0, 1): (6, "六等奖"),
    }
    hit = table.get((main_hit, special_hit))
    if not hit:
        return None, "未中奖", "未达到设奖条件"
    level, name = hit
    return level, name, _compact_rule(main_hit, special_hit)


def _dlt_prize_old(main_hit: int, special_hit: int) -> tuple[int | None, str, str]:
    table = {
        (5, 2): (1, "一等奖"),
        (5, 1): (2, "二等奖"),
        (5, 0): (3, "三等奖"),
        (4, 2): (4, "四等奖"),
        (4, 1): (5, "五等奖"),
        (3, 2): (6, "六等奖"),
        (4, 0): (7, "七等奖"),
        (3, 1): (8, "八等奖"),
        (2, 2): (8, "八等奖"),
        (3, 0): (9, "九等奖"),
        (2, 1): (9, "九等奖"),
        (1, 2): (9, "九等奖"),
        (0, 2): (9, "九等奖"),
    }
    hit = table.get((main_hit, special_hit))
    if not hit:
        return None, "未中奖", "未达到设奖条件"
    level, name = hit
    return level, name, _compact_rule(main_hit, special_hit)


def _dlt_prize_new(main_hit: int, special_hit: int) -> tuple[int | None, str, str]:
    """2026014 期起：13 个命中条件合并为 7 个奖级。"""
    table = {
        (5, 2): (1, "一等奖"),
        (5, 1): (2, "二等奖"),
        (5, 0): (3, "三等奖"),
        (4, 2): (3, "三等奖"),
        (4, 1): (4, "四等奖"),
        (4, 0): (5, "五等奖"),
        (3, 2): (5, "五等奖"),
        (3, 1): (6, "六等奖"),
        (2, 2): (6, "六等奖"),
        (3, 0): (7, "七等奖"),
        (2, 1): (7, "七等奖"),
        (1, 2): (7, "七等奖"),
        (0, 2): (7, "七等奖"),
    }
    hit = table.get((main_hit, special_hit))
    if not hit:
        return None, "未中奖", "未达到设奖条件"
    level, name = hit
    return level, name, _compact_rule(main_hit, special_hit)


def _prize_fn(cfg: GameConfig, issue: str):
    if cfg.key == "ssq":
        return _ssq_prize
    if cfg.key == "dlt":
        issue_n = int(normalize_issue(issue) or "0")
        if issue_n >= DLT_NEW_RULES_FROM:
            return _dlt_prize_new
        return _dlt_prize_old
    raise ValueError(f"不支持的彩种: {cfg.key}")


def _fallback_unit(cfg: GameConfig, issue: str, level: int) -> int | None:
    if cfg.key == "ssq":
        return _SSQ_FIXED_FALLBACK.get(level)
    if cfg.key == "dlt":
        issue_n = int(normalize_issue(issue) or "0")
        if issue_n >= DLT_NEW_RULES_FROM:
            return None
        return _DLT_OLD_FIXED_FALLBACK.get(level)
    return None


def _resolve_unit_prize(cfg: GameConfig, draw: Draw, level: int) -> tuple[int | None, str]:
    official = draw.unit_prize(level)
    if official is not None:
        return official, "official"
    fb = _fallback_unit(cfg, draw.issue, level)
    if fb is not None:
        return fb, "fallback"
    return None, "none"


def _validate_selection(cfg: GameConfig, main: list[int], special: list[int]) -> None:
    if len(set(main)) != len(main):
        raise ValueError(f"{cfg.main_label}号码不可重复")
    if len(set(special)) != len(special):
        raise ValueError(f"{cfg.special_label}号码不可重复")
    if len(main) < cfg.main_count:
        raise ValueError(f"{cfg.main_label}至少选 {cfg.main_count} 个，当前 {len(main)} 个")
    if len(special) < cfg.special_count:
        raise ValueError(f"{cfg.special_label}至少选 {cfg.special_count} 个，当前 {len(special)} 个")
    if len(main) > cfg.main_max:
        raise ValueError(f"{cfg.main_label}最多选 {cfg.main_max} 个")
    if len(special) > cfg.special_max:
        raise ValueError(f"{cfg.special_label}最多选 {cfg.special_max} 个")
    for n in main:
        if n < 1 or n > cfg.main_max:
            raise ValueError(f"{cfg.main_label}号码越界: {n}")
    for n in special:
        if n < 1 or n > cfg.special_max:
            raise ValueError(f"{cfg.special_label}号码越界: {n}")


def _aggregate_levels(
    cfg: GameConfig,
    draw: Draw,
    hit_main: int,
    miss_main: int,
    hit_special: int,
    miss_special: int,
) -> tuple[int, list[PrizeLevelCount], str]:
    """按组合数统计各奖等单式注数，返回 (总注数, 奖等汇总, 奖金来源)。"""
    pick_m, pick_s = cfg.main_count, cfg.special_count
    total = comb(hit_main + miss_main, pick_m) * comb(hit_special + miss_special, pick_s)
    prize = _prize_fn(cfg, draw.issue)

    # level -> {rule_code: ways}
    raw: dict[int, dict[str, int]] = {}
    names: dict[int, str] = {}

    for k in range(0, pick_m + 1):
        if k > hit_main or (pick_m - k) > miss_main:
            continue
        ways_main = comb(hit_main, k) * comb(miss_main, pick_m - k)
        for b in range(0, pick_s + 1):
            if b > hit_special or (pick_s - b) > miss_special:
                continue
            ways = ways_main * comb(hit_special, b) * comb(miss_special, pick_s - b)
            if ways <= 0:
                continue
            level, name, rule = prize(k, b)
            if level is None:
                continue
            names[level] = name
            bucket = raw.setdefault(level, {})
            bucket[rule] = bucket.get(rule, 0) + ways

    levels: list[PrizeLevelCount] = []
    sources: set[str] = set()
    for level in sorted(raw):
        rules_map = raw[level]
        # 规则按命中强度排序：主区降序、特区降序
        ordered_rules = sorted(
            rules_map.keys(),
            key=lambda r: tuple(int(x) for x in r.split("+")),
            reverse=True,
        )
        count = sum(rules_map.values())
        unit, src = _resolve_unit_prize(cfg, draw, level)
        sources.add(src)
        amount = (unit * count) if unit is not None else None
        rule_text = " ".join(ordered_rules)
        levels.append(
            PrizeLevelCount(
                prize_level=level,
                prize_name=names[level],
                rule=rule_text,
                count=count,
                unit_prize=unit,
                amount=amount,
            )
        )

    if not levels:
        source = "none"
    elif sources == {"official"}:
        source = "official"
    elif sources == {"fallback"}:
        source = "fallback"
    elif "none" in sources and len(sources) == 1:
        source = "none"
    else:
        source = "mixed"
    return total, levels, source


def evaluate_ticket(
    cfg: GameConfig,
    draw: Draw,
    main: list[int] | tuple[int, ...],
    special: list[int] | tuple[int, ...],
) -> PrizeResult:
    main_list = list(main)
    special_list = list(special)
    _validate_selection(cfg, main_list, special_list)

    hit_main = len(set(main_list) & set(draw.main))
    hit_special = len(set(special_list) & set(draw.special))
    miss_main = len(main_list) - hit_main
    miss_special = len(special_list) - hit_special

    total_bets, levels_list, prize_source = _aggregate_levels(
        cfg, draw, hit_main, miss_main, hit_special, miss_special
    )
    levels = tuple(levels_list)
    winning_bets = sum(x.count for x in levels)

    mode = (
        "single"
        if len(main_list) == cfg.main_count and len(special_list) == cfg.special_count
        else "compound"
    )

    if levels:
        best = levels[0]
        prize_level, prize_name = best.prize_level, best.prize_name
        rule = f"{prize_name} {best.rule}"
        if mode == "compound":
            rule = f"复式拆解后最高：{rule}"
    else:
        prize_level, prize_name, rule = None, "未中奖", "未达到设奖条件"

    if levels and all(x.amount is not None for x in levels):
        total_prize = sum(x.amount or 0 for x in levels)
    else:
        total_prize = None

    return PrizeResult(
        game=cfg.key,
        issue=draw.issue,
        draw_date=draw.date,
        draw_formatted=draw.format_numbers(),
        ticket_formatted=_fmt(main_list, special_list),
        mode=mode,
        main_selected=len(main_list),
        special_selected=len(special_list),
        main_hit=hit_main,
        special_hit=hit_special,
        total_bets=total_bets,
        winning_bets=winning_bets,
        levels=levels,
        prize_level=prize_level,
        prize_name=prize_name,
        rule=rule,
        total_prize=total_prize,
        prize_source=prize_source,
    )


def find_draw(draws: list[Draw], issue: str) -> Draw | None:
    target = normalize_issue(issue)
    for d in draws:
        if normalize_issue(d.issue) == target:
            return d
    return None


def check_prize(
    game: str,
    issue: str,
    main: list[int],
    special: list[int],
    draws: list[Draw],
) -> PrizeResult:
    cfg = get_game(game)
    draw = find_draw(draws, issue)
    if draw is None:
        raise LookupError(f"未找到期号 {issue}，请先同步该期开奖数据")
    return evaluate_ticket(cfg, draw, main, special)
