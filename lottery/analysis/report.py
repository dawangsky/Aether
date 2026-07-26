"""Rich 终端报表。"""

from __future__ import annotations

from rich.console import Console
from rich.table import Table

from lottery.analysis.frequency import ranked_frequency
from lottery.analysis.omission import average_omissions, current_omissions, omission_bands
from lottery.analysis.patterns import analyze_main, summarize_history
from lottery.config import GameConfig
from lottery.models import Draw, Ticket

console = Console()


def print_recent(cfg: GameConfig, draws: list[Draw], limit: int = 10) -> None:
    table = Table(title=f"{cfg.name} 最近 {min(limit, len(draws))} 期")
    table.add_column("期号", style="cyan")
    table.add_column("日期")
    table.add_column("开奖号码", style="bold")
    for d in draws[-limit:]:
        table.add_row(d.issue, d.date, d.format_numbers())
    console.print(table)


def print_analysis(cfg: GameConfig, draws: list[Draw], window: int) -> None:
    window_draws = draws[-window:] if len(draws) > window else draws
    if not window_draws:
        console.print("[red]无历史数据，请先执行 update[/red]")
        return

    console.rule(f"{cfg.name} 量化分析 · 近 {len(window_draws)} 期")
    last = window_draws[-1]
    prev = window_draws[-2] if len(window_draws) > 1 else None
    pat = analyze_main(
        cfg,
        last.main_sorted(),
        prev_main=prev.main_sorted() if prev else None,
    )
    console.print(
        f"上期 [bold]{last.issue}[/bold] {last.date} → {last.format_numbers()}\n"
        f"和值={pat.sum_value} 跨度={pat.span} 奇偶={pat.odd_even[0]}:{pat.odd_even[1]} "
        f"大小={pat.big_small[0]}:{pat.big_small[1]} 三区={pat.zones[0]}:{pat.zones[1]}:{pat.zones[2]} "
        f"连号组={pat.consecutive_groups} 重号={pat.repeats} 邻号={pat.neighbors}"
    )

    hist = summarize_history(cfg, window_draws)
    console.print(
        f"窗口形态中枢: 和值均值={hist['sum_mean']} 中位={hist['sum_median']} "
        f"区间=[{hist['sum_min']},{hist['sum_max']}] 跨度均值={hist['span_mean']}"
    )

    _print_freq_table(cfg, window_draws, special=False)
    _print_omit_table(cfg, window_draws, special=False)
    _print_freq_table(cfg, window_draws, special=True)
    _print_omit_table(cfg, window_draws, special=True)

    main_omit = current_omissions(cfg, window_draws, special=False)
    bands = omission_bands(main_omit)
    band_table = Table(title=f"{cfg.main_label} 遗漏分层")
    band_table.add_column("分层")
    band_table.add_column("号码")
    band_table.add_column("个数", justify="right")
    for name, nums in bands.items():
        band_table.add_row(
            name,
            " ".join(f"{n:02d}" for n in nums) or "-",
            str(len(nums)),
        )
    console.print(band_table)


def _print_freq_table(cfg: GameConfig, draws: list[Draw], *, special: bool) -> None:
    label = cfg.special_label if special else cfg.main_label
    ranked = ranked_frequency(cfg, draws, special=special)
    table = Table(title=f"{label} 冷热（出现次数）")
    table.add_column("热号 Top")
    table.add_column("次数", justify="right")
    table.add_column("冷号 Bottom")
    table.add_column("次数", justify="right")
    hot = ranked[:8]
    cold = list(reversed(ranked[-8:]))
    for i in range(max(len(hot), len(cold))):
        h = hot[i] if i < len(hot) else ("", "")
        c = cold[i] if i < len(cold) else ("", "")
        table.add_row(
            f"{h[0]:02d}" if h[0] != "" else "",
            str(h[1]) if h[0] != "" else "",
            f"{c[0]:02d}" if c[0] != "" else "",
            str(c[1]) if c[0] != "" else "",
        )
    console.print(table)


def _print_omit_table(cfg: GameConfig, draws: list[Draw], *, special: bool) -> None:
    label = cfg.special_label if special else cfg.main_label
    omit = current_omissions(cfg, draws, special=special)
    avg = average_omissions(cfg, draws, special=special)
    ranked = sorted(omit.items(), key=lambda x: (-x[1], x[0]))[:12]
    table = Table(title=f"{label} 当前遗漏 Top12")
    table.add_column("号码")
    table.add_column("当前遗漏", justify="right")
    table.add_column("平均遗漏", justify="right")
    for n, miss in ranked:
        table.add_row(f"{n:02d}", str(miss), f"{avg[n]:.1f}")
    console.print(table)


def print_tickets(cfg: GameConfig, tickets: list[Ticket], title: str = "推荐号码") -> None:
    table = Table(title=f"{cfg.name} {title}")
    table.add_column("注", justify="right")
    table.add_column("号码", style="bold green")
    table.add_column("形态摘要")
    for i, t in enumerate(tickets, start=1):
        meta = t.meta
        summary = (
            f"和值={meta.get('sum')} 奇偶={meta.get('odd_even')} "
            f"大小={meta.get('big_small')} 三区={meta.get('zones')} "
            f"遗漏层={meta.get('bands')}"
        )
        table.add_row(str(i), t.format_numbers(), summary)
    console.print(table)
    console.print("[dim]仅供研究娱乐，开奖随机，不构成投注建议。[/dim]")
