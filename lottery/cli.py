"""命令行入口。"""

from __future__ import annotations

import argparse
import sys

from rich.console import Console

from lottery.analysis.report import print_analysis, print_recent, print_tickets
from lottery.backtest.evaluator import print_backtest, run_backtest
from lottery.config import GAMES, get_game
from lottery.data.fetcher import update_game, update_games
from lottery.data.loader import load_draws
from lottery.predict.generator import generate_tickets

console = Console()


def _ensure_data(game: str, auto_update: bool = True) -> list:
    draws = load_draws(game)
    if len(draws) >= 20:
        return draws
    if not auto_update:
        return draws
    console.print(f"[yellow]本地 {game} 数据不足，正在自动拉取...[/yellow]")
    try:
        draws, added = update_game(game, limit=120)
        console.print(f"[green]已更新 {game}: 共 {len(draws)} 期，新增 {added} 期[/green]")
    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]拉取失败: {exc}[/red]")
        if not draws:
            raise SystemExit(1) from exc
    return draws


def cmd_update(args: argparse.Namespace) -> int:
    games = list(GAMES) if args.game == "all" else [args.game]
    try:
        result = update_games(games, limit=args.limit)
    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]更新失败: {exc}[/red]")
        return 1
    for g, (total, added) in result.items():
        cfg = get_game(g)
        console.print(f"[green]{cfg.name}[/green]: 共 {total} 期，本次新增 {added} 期")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    cfg = get_game(args.game)
    draws = _ensure_data(args.game)
    print_recent(cfg, draws, limit=args.limit)
    return 0


def cmd_analyze(args: argparse.Namespace) -> int:
    cfg = get_game(args.game)
    draws = _ensure_data(args.game)
    print_analysis(cfg, draws, window=args.window)
    return 0


def cmd_predict(args: argparse.Namespace) -> int:
    cfg = get_game(args.game)
    draws = _ensure_data(args.game)
    window_draws = draws[-args.window :] if len(draws) > args.window else draws
    tickets = generate_tickets(cfg, window_draws, n=args.n, seed=args.seed)
    console.print(
        f"{cfg.name} 基于近 {len(window_draws)} 期走势生成 {len(tickets)} 注"
        f"（上期 {window_draws[-1].issue}）"
    )
    print_tickets(cfg, tickets)
    return 0


def cmd_backtest(args: argparse.Namespace) -> int:
    cfg = get_game(args.game)
    draws = _ensure_data(args.game)
    result = run_backtest(
        cfg,
        draws,
        window=args.window,
        n_tickets=args.n,
        periods=args.periods,
        seed=args.seed,
    )
    print_backtest(cfg, result)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lottery",
        description="双色球 & 大乐透量化分析预测系统（研究娱乐用途）",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_upd = sub.add_parser("update", help="拉取/更新历史开奖")
    p_upd.add_argument("--game", choices=["ssq", "dlt", "all"], default="all")
    p_upd.add_argument("--limit", type=int, default=120, help="拉取期数上限")
    p_upd.set_defaults(func=cmd_update)

    p_show = sub.add_parser("show", help="查看最近开奖")
    p_show.add_argument("--game", choices=["ssq", "dlt"], required=True)
    p_show.add_argument("--limit", type=int, default=10)
    p_show.set_defaults(func=cmd_show)

    p_an = sub.add_parser("analyze", help="量化走势分析")
    p_an.add_argument("--game", choices=["ssq", "dlt"], required=True)
    p_an.add_argument("--window", type=int, default=50)
    p_an.set_defaults(func=cmd_analyze)

    p_pred = sub.add_parser("predict", help="生成推荐号码")
    p_pred.add_argument("--game", choices=["ssq", "dlt"], required=True)
    p_pred.add_argument("-n", type=int, default=2, help="注数")
    p_pred.add_argument("--window", type=int, default=50)
    p_pred.add_argument("--seed", type=int, default=None)
    p_pred.set_defaults(func=cmd_predict)

    p_bt = sub.add_parser("backtest", help="滚动回测 vs 随机基线")
    p_bt.add_argument("--game", choices=["ssq", "dlt"], required=True)
    p_bt.add_argument("--window", type=int, default=30)
    p_bt.add_argument("-n", type=int, default=5, help="每期生成注数")
    p_bt.add_argument("--periods", type=int, default=50)
    p_bt.add_argument("--seed", type=int, default=42)
    p_bt.set_defaults(func=cmd_backtest)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
