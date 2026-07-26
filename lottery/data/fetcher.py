"""开奖数据抓取适配器：福彩官网(双色球) + 体彩网关(大乐透)。"""

from __future__ import annotations

import re
from typing import Iterable

import requests

from lottery.config import GameConfig, get_game
from lottery.data.loader import load_draws, merge_draws, save_draws
from lottery.models import Draw

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json,text/plain,*/*",
}

SSQ_URL = (
    "https://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice"
)
DLT_URL = (
    "https://webapi.sporttery.cn/gateway/lottery/getHistoryPageListV1.qry"
)

_LEVEL_NAME = {
    "一等奖": 1,
    "二等奖": 2,
    "三等奖": 3,
    "四等奖": 4,
    "五等奖": 5,
    "六等奖": 6,
    "七等奖": 7,
    "八等奖": 8,
    "九等奖": 9,
}


def _parse_date(raw: str) -> str:
    m = re.search(r"(\d{4}-\d{2}-\d{2})", raw or "")
    return m.group(1) if m else (raw or "")


def _parse_nums(text: str, sep: str = ",") -> tuple[int, ...]:
    parts = re.split(r"[\s,|]+", text.strip())
    return tuple(int(p) for p in parts if p)


def _parse_money(raw: object) -> int | None:
    if raw is None:
        return None
    text = str(raw).strip().replace(",", "").replace("，", "")
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def _prizes_from_ssq(item: dict) -> tuple[tuple[int, int], ...]:
    out: list[tuple[int, int]] = []
    for grade in item.get("prizegrades") or []:
        try:
            level = int(grade.get("type"))
        except (TypeError, ValueError):
            continue
        money = _parse_money(grade.get("typemoney"))
        if level >= 1 and money is not None:
            out.append((level, money))
    return tuple(sorted(out))


def _prizes_from_dlt(item: dict) -> tuple[tuple[int, int], ...]:
    out: list[tuple[int, int]] = []
    for grade in item.get("prizeLevelList") or []:
        name = str(grade.get("prizeLevel") or "")
        if "追加" in name:
            continue
        # 去掉可能的空格
        name = name.strip()
        level = _LEVEL_NAME.get(name)
        if level is None:
            continue
        money = _parse_money(grade.get("stakeAmountFormat") or grade.get("stakeAmount"))
        if money is not None:
            out.append((level, money))
    return tuple(sorted(out))


def fetch_ssq(issue_count: int = 100) -> list[Draw]:
    resp = requests.get(
        SSQ_URL,
        params={"name": "ssq", "issueCount": issue_count},
        headers={**HEADERS, "Referer": "https://www.cwl.gov.cn/"},
        timeout=20,
    )
    resp.raise_for_status()
    payload = resp.json()
    if payload.get("state") not in (0, "0"):
        raise RuntimeError(f"双色球接口异常: {payload.get('message')}")
    draws: list[Draw] = []
    for item in payload.get("result", []):
        draws.append(
            Draw(
                issue=str(item["code"]),
                date=_parse_date(item.get("date", "")),
                main=_parse_nums(item["red"]),
                special=_parse_nums(item["blue"]),
                prizes=_prizes_from_ssq(item),
            )
        )
    return sorted(draws, key=lambda d: d.issue)


def fetch_dlt(pages: int = 5, page_size: int = 30) -> list[Draw]:
    headers = {
        **HEADERS,
        "Referer": "https://www.lottery.gov.cn/",
    }
    draws: list[Draw] = []
    for page in range(1, pages + 1):
        resp = requests.get(
            DLT_URL,
            params={
                "gameNo": 85,
                "provinceId": 0,
                "pageSize": page_size,
                "isVerify": 1,
                "pageNo": page,
            },
            headers=headers,
            timeout=20,
        )
        resp.raise_for_status()
        payload = resp.json()
        if not payload.get("success"):
            raise RuntimeError(f"大乐透接口异常: {payload.get('errorMessage')}")
        lst = payload.get("value", {}).get("list") or []
        if not lst:
            break
        for item in lst:
            nums = _parse_nums(item["lotteryDrawResult"], sep=" ")
            if len(nums) < 7:
                continue
            issue = str(item["lotteryDrawNum"])
            # 体彩期号常为 5 位，统一补成 20xxxxx 便于排序对齐
            if len(issue) == 5:
                issue = f"20{issue}"
            draws.append(
                Draw(
                    issue=issue,
                    date=_parse_date(item.get("lotteryDrawTime", "")),
                    main=nums[:5],
                    special=nums[5:7],
                    prizes=_prizes_from_dlt(item),
                )
            )
    return sorted({d.issue: d for d in draws}.values(), key=lambda d: d.issue)


def fetch_history(game: str | GameConfig, limit: int = 100) -> list[Draw]:
    cfg = game if isinstance(game, GameConfig) else get_game(game)
    if cfg.key == "ssq":
        return fetch_ssq(issue_count=limit)
    if cfg.key == "dlt":
        pages = max(1, (limit + 29) // 30)
        return fetch_dlt(pages=pages, page_size=30)[-limit:]
    raise ValueError(f"不支持的彩种: {cfg.key}")


def update_game(game: str, limit: int = 100) -> tuple[list[Draw], int]:
    """拉取并合并本地数据，返回 (全部期数, 新增期数)。"""
    cfg = get_game(game)
    existing = load_draws(cfg)
    incoming = fetch_history(cfg, limit=limit)
    before = {d.issue for d in existing}
    merged = merge_draws(existing, incoming)
    save_draws(cfg, merged)
    added = sum(1 for d in incoming if d.issue not in before)
    return merged, added


def update_games(games: Iterable[str], limit: int = 100) -> dict[str, tuple[int, int]]:
    result: dict[str, tuple[int, int]] = {}
    for g in games:
        draws, added = update_game(g, limit=limit)
        result[g] = (len(draws), added)
    return result
