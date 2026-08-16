"""Command-line entry points for reproducible local experiments."""

from __future__ import annotations

import argparse
import hashlib
from datetime import UTC, date, datetime
from pathlib import Path

from .data import load_bars_csv
from .engine import BacktestEngine, ExecutionCostModel, RiskPolicy
from .experiment_plan import evaluate_experiment_plan, load_experiment_plan
from .experiment_sufficiency import (
    evaluate_sufficiency,
    load_plan_result,
    load_sufficiency_criteria,
)
from .evidence import build_rule_baseline_passport, build_run_passport, write_json
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
from .regimes import CausalRegimeClassifier, build_regime_report
from .strategies import control_strategies, first_rule_league
from .vendor_due_diligence import evaluate_dossiers, load_dossiers


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
    rule = subparsers.add_parser(
        "run-rule-baseline", help="run controls plus BOT-RULE-101 moving-average baseline"
    )
    rule.add_argument("--data", type=Path, required=True)
    rule.add_argument("--output", type=Path, required=True)
    rule.add_argument("--passport", type=Path)
    rule.add_argument("--seed", type=int, default=20260816)
    rule.add_argument("--short-window", type=int, default=3)
    rule.add_argument("--long-window", type=int, default=5)
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
    dossiers = subparsers.add_parser(
        "evaluate-vendor-dossiers",
        help="apply the fail-closed questionnaire and offline-sample gate",
    )
    dossiers.add_argument("--dossiers", type=Path, required=True)
    dossiers.add_argument("--output", type=Path, required=True)
    plan = subparsers.add_parser(
        "validate-experiment-plan",
        help="validate a sealed chronological train/validation/OOS plan",
    )
    plan.add_argument("--plan", type=Path, required=True)
    plan.add_argument("--data", type=Path, required=True)
    plan.add_argument("--output", type=Path, required=True)
    sufficiency = subparsers.add_parser(
        "evaluate-plan-sufficiency",
        help="check whether validated splits can warm up and score a strategy",
    )
    sufficiency.add_argument("--plan-result", type=Path, required=True)
    sufficiency.add_argument("--criteria", type=Path, required=True)
    sufficiency.add_argument("--output", type=Path, required=True)
    regimes = subparsers.add_parser(
        "label-regimes", help="create causal diagnostic regime labels from closed bars"
    )
    regimes.add_argument("--data", type=Path, required=True)
    regimes.add_argument("--output", type=Path, required=True)
    regimes.add_argument("--lookback-bars", type=int, default=5)
    regimes.add_argument("--trend-threshold-bps", type=float, default=20.0)
    regimes.add_argument("--high-volatility-threshold-bps", type=float, default=50.0)
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
    if args.command == "run-rule-baseline":
        bars = load_bars_csv(args.data)
        costs = ExecutionCostModel()
        risk = RiskPolicy(max_position_weight=1.0, max_drawdown=0.10)
        engine = BacktestEngine(initial_equity=10_000, costs=costs, risk=risk)
        strategies = first_rule_league(
            args.seed,
            short_window=args.short_window,
            long_window=args.long_window,
        )
        results = [engine.run(bars, strategy) for strategy in strategies]
        run_config = {
            "dataset": {
                "name": args.data.name,
                "sha256": hashlib.sha256(args.data.read_bytes()).hexdigest(),
                "classification": "MODELLED",
            },
            "seed": args.seed,
            "rule": {
                "strategy_id": "BOT-RULE-101",
                "short_window": args.short_window,
                "long_window": args.long_window,
                "optimization_performed": False,
            },
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
        passport = build_rule_baseline_passport(
            run_id=(
                f"RUN-M0-RULE-101-S{args.short_window}-L{args.long_window}-SEED-{args.seed}"
            ),
            report_path=destination,
            dataset_path=args.data,
            seed=args.seed,
            short_window=args.short_window,
            long_window=args.long_window,
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
    if args.command == "evaluate-vendor-dossiers":
        payload = load_dossiers(args.dossiers)
        destination = write_json(args.output, evaluate_dossiers(payload))
        print(destination)
        return 0
    if args.command == "validate-experiment-plan":
        plan = load_experiment_plan(args.plan)
        bars = load_bars_csv(args.data)
        result = evaluate_experiment_plan(plan, dataset_path=args.data, bars=bars)
        destination = write_json(args.output, result)
        print(destination)
        return 0
    if args.command == "evaluate-plan-sufficiency":
        result = load_plan_result(args.plan_result)
        criteria = load_sufficiency_criteria(args.criteria)
        evaluation = evaluate_sufficiency(
            result,
            criteria,
            result_path=args.plan_result,
            criteria_path=args.criteria,
        )
        destination = write_json(args.output, evaluation)
        print(destination)
        return 0
    if args.command == "label-regimes":
        bars = load_bars_csv(args.data)
        classifier = CausalRegimeClassifier(
            lookback_bars=args.lookback_bars,
            trend_threshold_bps=args.trend_threshold_bps,
            high_volatility_threshold_bps=args.high_volatility_threshold_bps,
        )
        report = build_regime_report(
            bars,
            classifier,
            dataset_sha256=hashlib.sha256(args.data.read_bytes()).hexdigest(),
        )
        destination = write_json(args.output, report)
        print(destination)
        return 0
    raise AssertionError("unreachable command")
