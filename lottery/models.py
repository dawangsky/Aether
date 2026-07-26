"""开奖与推荐号码的数据结构。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Draw:
    issue: str
    date: str
    main: tuple[int, ...]
    special: tuple[int, ...]
    # 奖等 -> 单注奖金（元），来自官网当期公告；无数据时为空
    prizes: tuple[tuple[int, int], ...] = ()

    def main_sorted(self) -> tuple[int, ...]:
        return tuple(sorted(self.main))

    def special_sorted(self) -> tuple[int, ...]:
        return tuple(sorted(self.special))

    def prize_map(self) -> dict[int, int]:
        return dict(self.prizes)

    def unit_prize(self, level: int) -> int | None:
        money = self.prize_map().get(level)
        return money if money is not None and money >= 0 else None

    def format_numbers(self) -> str:
        main = " ".join(f"{n:02d}" for n in self.main_sorted())
        special = " ".join(f"{n:02d}" for n in self.special_sorted())
        return f"{main} + {special}"


@dataclass
class Ticket:
    main: tuple[int, ...]
    special: tuple[int, ...]
    meta: dict[str, Any] = field(default_factory=dict)

    def format_numbers(self) -> str:
        main = " ".join(f"{n:02d}" for n in sorted(self.main))
        special = " ".join(f"{n:02d}" for n in sorted(self.special))
        return f"{main} + {special}"
