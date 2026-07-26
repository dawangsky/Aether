"""本地 CSV 开奖数据读写。"""

from __future__ import annotations

import csv
from pathlib import Path

from lottery.config import DATA_DIR, GameConfig, get_game
from lottery.models import Draw


def csv_path(game: str | GameConfig) -> Path:
    cfg = game if isinstance(game, GameConfig) else get_game(game)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR / cfg.csv_name


def _row_to_draw(cfg: GameConfig, row: dict[str, str]) -> Draw:
    main = tuple(int(row[f"m{i}"]) for i in range(1, cfg.main_count + 1))
    special = tuple(int(row[f"s{i}"]) for i in range(1, cfg.special_count + 1))
    return Draw(issue=row["issue"], date=row["date"], main=main, special=special)


def _draw_to_row(cfg: GameConfig, draw: Draw) -> dict[str, str]:
    row: dict[str, str] = {"issue": draw.issue, "date": draw.date}
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
        merged[d.issue] = d
    return sorted(merged.values(), key=lambda d: d.issue)
