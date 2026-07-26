"""彩种规则与全局路径配置。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"


@dataclass(frozen=True)
class GameConfig:
    key: str
    name: str
    main_count: int
    main_max: int
    special_count: int
    special_max: int
    main_label: str
    special_label: str
    zone_edges: tuple[int, int]  # 三区边界：1..a / a+1..b / b+1..max
    size_split: int  # >= size_split 为大号
    csv_name: str

    @property
    def main_range(self) -> range:
        return range(1, self.main_max + 1)

    @property
    def special_range(self) -> range:
        return range(1, self.special_max + 1)


SSQ = GameConfig(
    key="ssq",
    name="双色球",
    main_count=6,
    main_max=33,
    special_count=1,
    special_max=16,
    main_label="红球",
    special_label="蓝球",
    zone_edges=(11, 22),
    size_split=17,
    csv_name="ssq.csv",
)

DLT = GameConfig(
    key="dlt",
    name="大乐透",
    main_count=5,
    main_max=35,
    special_count=2,
    special_max=12,
    main_label="前区",
    special_label="后区",
    zone_edges=(12, 23),
    size_split=18,
    csv_name="dlt.csv",
)

GAMES: dict[str, GameConfig] = {
    "ssq": SSQ,
    "dlt": DLT,
}


def get_game(key: str) -> GameConfig:
    try:
        return GAMES[key.lower()]
    except KeyError as exc:
        raise ValueError(f"未知彩种: {key}，可选: {', '.join(GAMES)}") from exc
