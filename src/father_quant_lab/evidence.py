"""Evidence passports for the complete idea-to-result research lifecycle."""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from pathlib import Path
from typing import Iterable

from .models import BacktestResult


def sha256_file(path: str | Path) -> str:
    """Return a stable content fingerprint for an artifact."""
    source = Path(path)
    return hashlib.sha256(source.read_bytes()).hexdigest()


def build_run_passport(
    *,
    run_id: str,
    report_path: str | Path,
    dataset_path: str | Path,
    seed: int,
    results: Iterable[BacktestResult],
) -> dict[str, object]:
    """Describe why a run exists, how it was produced, and what it proved."""
    report = Path(report_path)
    dataset = Path(dataset_path)
    ordered = sorted(results, key=lambda result: result.strategy_id)
    return {
        "schema_version": "1.0.0",
        "passport_type": "experiment_run",
        "run_id": run_id,
        "lifecycle": {
            "idea": "Create a reproducible minimum control league for EUR/USD.",
            "hypothesis": "The reference engine can execute four controls deterministically without look-ahead or live orders.",
            "requirements": ["FQL-FR-001", "FQL-FR-002", "FQL-FR-003", "FQL-FR-004", "FQL-FR-005", "FQL-FR-006", "FQL-FR-007", "FQL-FR-008"],
            "design_decisions": ["ADR-0001", "ADR-0002", "ADR-0003"],
            "implementation": [
                "src/father_quant_lab/data.py",
                "src/father_quant_lab/engine.py",
                "src/father_quant_lab/strategies.py",
                "src/father_quant_lab/reporting.py",
            ],
            "verification": [
                "tests/test_cli.py",
                "tests/test_data.py",
                "tests/test_engine.py",
                "tests/test_reporting.py",
            ],
            "decision": "accepted_as_m0_control_baseline",
            "next_gate": "Run the same contract on licensed historical data and independent engines.",
        },
        "provenance": {
            "dataset_path": dataset.as_posix(),
            "dataset_sha256": sha256_file(dataset),
            "dataset_classification": "MODELLED",
            "report_path": report.as_posix(),
            "report_sha256": sha256_file(report),
            "seed": seed,
        },
        "environment": {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "executable": Path(sys.executable).name,
        },
        "safety": {
            "mode": "backtest_only",
            "live_orders_forbidden": True,
            "real_money_used": False,
            "performance_claim_allowed": False,
        },
        "result_summary": [
            {
                "strategy_id": result.strategy_id,
                "final_equity": result.metrics.final_equity,
                "total_return": result.metrics.total_return,
                "max_drawdown": result.metrics.max_drawdown,
                "trade_count": result.metrics.trade_count,
                "kill_switch_triggered": result.metrics.kill_switch_triggered,
            }
            for result in ordered
        ],
        "interpretation": {
            "proved": [
                "the control pipeline executes end to end",
                "the same seed and input produce the same report",
                "costs, risk limits and data lineage are recorded",
            ],
            "not_proved": [
                "future profitability",
                "validity on real market data",
                "readiness for live trading",
            ],
            "lessons": [
                "installation and Python version are part of reproducibility",
                "console output alone is not accepted as durable evidence",
            ],
        },
    }


def write_json(path: str | Path, payload: dict[str, object]) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return destination
