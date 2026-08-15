"""Command-line entry points for reproducible local experiments."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from .data import load_bars_csv
from .engine import BacktestEngine, ExecutionCostModel, RiskPolicy
from .evidence import build_run_passport, write_json
from .reporting import league_report, write_report
from .strategies import control_strategies


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="father-quant-lab")
    subparsers = parser.add_subparsers(dest="command", required=True)
    controls = subparsers.add_parser("run-controls", help="run mandatory control robots")
    controls.add_argument("--data", type=Path, required=True)
    controls.add_argument("--output", type=Path, required=True)
    controls.add_argument(
        "--passport",
        type=Path,
        help="evidence passport path; defaults to <output>.passport.json",
    )
    controls.add_argument("--seed", type=int, default=20260816)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "run-controls":
        bars = load_bars_csv(args.data)
        costs = ExecutionCostModel()
        risk = RiskPolicy(max_position_weight=1.0, max_drawdown=0.10)
        engine = BacktestEngine(
            initial_equity=10_000,
            costs=costs,
            risk=risk,
        )
        results = [engine.run(bars, strategy) for strategy in control_strategies(args.seed)]
        run_config = {
            "dataset": {
                "name": args.data.name,
                "sha256": hashlib.sha256(args.data.read_bytes()).hexdigest(),
                "classification": "MODELLED",
            },
            "seed": args.seed,
            "initial_equity": engine.initial_equity,
            "execution_costs_bps": {
                "spread": costs.spread_bps,
                "slippage": costs.slippage_bps,
                "commission": costs.commission_bps,
            },
            "risk": {
                "max_position_weight": risk.max_position_weight,
                "max_drawdown": risk.max_drawdown,
                "short_allowed": False,
                "leverage_allowed": False,
            },
        }
        destination = write_report(args.output, league_report(results, run_config=run_config))
        passport_path = args.passport or destination.with_name(
            f"{destination.stem}.passport.json"
        )
        passport = build_run_passport(
            run_id=f"RUN-M0-CONTROLS-SEED-{args.seed}",
            report_path=destination,
            dataset_path=args.data,
            seed=args.seed,
            results=results,
        )
        passport_destination = write_json(passport_path, passport)
        print(destination)
        print(passport_destination)
        return 0
    raise AssertionError("unreachable command")
