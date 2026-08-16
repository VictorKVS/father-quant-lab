"""Command-line entry points for reproducible local experiments."""

from __future__ import annotations

import argparse
import hashlib
from datetime import UTC, date, datetime
from pathlib import Path

from .data import load_bars_csv
from .engine import BacktestEngine, ExecutionCostModel, RiskPolicy
from .evidence import build_run_passport, write_json
from .provider_gate import evaluate_registry, load_registry
from .reporting import league_report, write_report
from .reference_data import (
    build_ecb_url,
    build_reference_passport,
    fetch_ecb_csv,
    parse_ecb_csv,
    write_passport,
    write_reference_csv,
)
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
    reference = subparsers.add_parser(
        "fetch-ecb-reference", help="fetch official non-tradable EUR/USD reference rates"
    )
    reference.add_argument("--start", type=date.fromisoformat, required=True)
    reference.add_argument("--end", type=date.fromisoformat, required=True)
    reference.add_argument("--raw-output", type=Path, required=True)
    reference.add_argument("--output", type=Path, required=True)
    reference.add_argument("--passport", type=Path, required=True)
    providers = subparsers.add_parser(
        "evaluate-providers", help="apply the fail-closed FX data-provider gate"
    )
    providers.add_argument("--registry", type=Path, required=True)
    providers.add_argument("--output", type=Path, required=True)
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
    if args.command == "fetch-ecb-reference":
        source_url = build_ecb_url(args.start, args.end)
        raw = fetch_ecb_csv(source_url)
        args.raw_output.parent.mkdir(parents=True, exist_ok=True)
        args.raw_output.write_bytes(raw)
        observations = parse_ecb_csv(raw)
        canonical = write_reference_csv(args.output, observations)
        passport = build_reference_passport(
            source_url=source_url,
            raw_path=args.raw_output,
            canonical_path=canonical,
            observations=observations,
            retrieved_at=datetime.now(UTC),
        )
        destination = write_passport(args.passport, passport)
        print(args.raw_output)
        print(canonical)
        print(destination)
        return 0
    if args.command == "evaluate-providers":
        registry = load_registry(args.registry)
        destination = write_json(args.output, evaluate_registry(registry))
        print(destination)
        return 0
    raise AssertionError("unreachable command")
