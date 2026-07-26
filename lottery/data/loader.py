"""本地 CSV 开奖数据读写。"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from lottery.config import DATA_DIR, GameConfig, get_game
from lottery.models import Draw


def csv_path(game: str | GameConfig) -> Path:
    cfg = game if isinstance(game, GameConfig) else get_game(game)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR / cfg.csv_name


def _parse_prizes(raw: str | None) -> tuple[tuple[int, int], ...]:
    text = (raw or "").strip()
    if not text:
        return ()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return ()
    if not isinstance(data, dict):
        return ()
    items: list[tuple[int, int]] = []
    for k, v in data.items():
        try:
            level = int(k)
            money = int(v)
        except (TypeError, ValueError):
            continue
        if level > 0 and money >= 0:
            items.append((level, money))
    return tuple(sorted(items))


def _format_prizes(prizes: tuple[tuple[int, int], ...]) -> str:
    if not prizes:
        return ""
    return json.dumps({str(level): money for level, money in prizes}, ensure_ascii=False, separators=(",", ":"))


def _row_to_draw(cfg: GameConfig, row: dict[str, str]) -> Draw:
    main = tuple(int(row[f"m{i}"]) for i in range(1, cfg.main_count + 1))
    special = tuple(int(row[f"s{i}"]) for i in range(1, cfg.special_count + 1))
    return Draw(
        issue=row["issue"],
        date=row["date"],
        main=main,
        special=special,
        prizes=_parse_prizes(row.get("prizes")),
    )


def _draw_to_row(cfg: GameConfig, draw: Draw) -> dict[str, str]:
    row: dict[str, str] = {
        "issue": draw.issue,
        "date": draw.date,
        "prizes": _format_prizes(draw.prizes),
    }
    for i, n in enumerate(draw.main_sorted(), start=1):
        row[f"m{i}"] = f"{n:02d}"
    for i, n in enumerate(draw.special_sorted(), start=1):
        row[f"s{i}"] = f"{n:02d}"
    return row


def fieldnames(cfg: GameConfig) -> list[str]:
    return (
        ["issue", "date"]
        + [f"m{i}" for i in range(1, cfg.main_count + 1)]
        + [f"s{i}" for i in range(1, cfg.special_count + 1)]
        + ["prizes"]
    )


def load_draws(game: str | GameConfig) -> list[Draw]:
    cfg = game if isinstance(game, GameConfig) else get_game(game)
    path = csv_path(cfg)
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        draws = [_row_to_draw(cfg, row) for row in reader if row.get("issue")]
    draws.sort(key=lambda d: d.issue)
    return draws


def save_draws(game: str | GameConfig, draws: list[Draw]) -> Path:
    cfg = game if isinstance(game, GameConfig) else get_game(game)
    path = csv_path(cfg)
    path.parent.mkdir(parents=True, exist_ok=True)
    uniq: dict[str, Draw] = {d.issue: d for d in draws}
    ordered = sorted(uniq.values(), key=lambda d: d.issue)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames(cfg))
        writer.writeheader()
        for draw in ordered:
            writer.writerow(_draw_to_row(cfg, draw))
    return path


def merge_draws(existing: list[Draw], incoming: list[Draw]) -> list[Draw]:
    merged = {d.issue: d for d in existing}
    for d in incoming:
        old = merged.get(d.issue)
        # 新抓取缺奖金时，保留本地已有奖金
        if old and not d.prizes and old.prizes:
            d = Draw(
                issue=d.issue,
                date=d.date or old.date,
                main=d.main,
                special=d.special,
                prizes=old.prizes,
            )
        merged[d.issue] = d
    return sorted(merged.values(), key=lambda d: d.issue)
