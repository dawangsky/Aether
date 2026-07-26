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

    def main_sorted(self) -> tuple[int, ...]:
        return tuple(sorted(self.main))

    def special_sorted(self) -> tuple[int, ...]:
        return tuple(sorted(self.special))

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
