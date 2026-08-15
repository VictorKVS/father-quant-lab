"""Stable report serialization for evidence and regression tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .models import BacktestResult


def league_report(
    results: Iterable[BacktestResult], *, run_config: dict[str, object] | None = None
) -> dict[str, object]:
    ordered = sorted(results, key=lambda result: result.strategy_id)
    return {
        "schema_version": "1.0.0",
        "mode": "backtest_only",
        "live_orders_forbidden": True,
        "run_config": run_config or {},
        "results": [result.to_dict() for result in ordered],
    }


def write_report(path: str | Path, report: dict[str, object]) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return destination
