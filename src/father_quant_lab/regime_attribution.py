"""Retrospective attribution of an equity curve to causal diagnostic regimes."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence

from .models import BacktestResult


def load_regime_report(path: str | Path) -> dict[str, Any]:
    report = json.loads(Path(path).read_text(encoding="utf-8"))
    if report.get("artifact_id") != "FQL-REGIME-LABELS-001":
        raise ValueError("unsupported regime report")
    if report.get("causality") != "past_and_current_closed_bars_only":
        raise ValueError("regime report must preserve causal labeling")
    if report.get("live_orders_forbidden") is not True:
        raise ValueError("regime report must preserve LIVE prohibition")
    labels = report.get("labels")
    if not isinstance(labels, list) or any(not isinstance(item, dict) for item in labels):
        raise ValueError("regime report labels must be a list of objects")
    return report


def _timestamp(value: object, field: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be an ISO-8601 timestamp")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    return parsed


def attribute_result(
    result: BacktestResult,
    regime_report: dict[str, Any],
    *,
    dataset_path: str | Path,
    regime_report_path: str | Path,
) -> dict[str, object]:
    dataset_path = Path(dataset_path)
    regime_report_path = Path(regime_report_path)
    dataset_sha = hashlib.sha256(dataset_path.read_bytes()).hexdigest()
    if regime_report.get("dataset", {}).get("sha256") != dataset_sha:
        raise ValueError("regime report dataset SHA-256 does not match input data")
    if regime_report.get("dataset", {}).get("instrument") != result.instrument:
        raise ValueError("regime report instrument does not match backtest result")

    labels_by_time: dict[datetime, dict[str, Any]] = {}
    for label in regime_report["labels"]:
        label_time = _timestamp(label.get("timestamp"), "label.timestamp")
        available = _timestamp(
            label.get("available_to_system_at"), "label.available_to_system_at"
        )
        if available != label_time:
            raise ValueError("diagnostic label must be available at its closed-bar timestamp")
        if label_time in labels_by_time:
            raise ValueError("regime timestamps must be unique")
        if label.get("trend") not in {"UP", "DOWN", "RANGE"}:
            raise ValueError("unsupported trend regime")
        if label.get("volatility") not in {"HIGH", "NORMAL"}:
            raise ValueError("unsupported volatility regime")
        labels_by_time[label_time] = label

    curve_by_time = {point.timestamp: point for point in result.equity_curve}
    unknown = set(labels_by_time) - set(curve_by_time)
    if unknown:
        raise ValueError("regime labels must match equity-curve timestamps")

    buckets: dict[str, list[tuple[float, bool]]] = defaultdict(list)
    labelled = 0
    curve: Sequence = result.equity_curve
    for previous, current in zip(curve, curve[1:]):
        label = labels_by_time.get(current.timestamp)
        if label is None:
            continue
        interval_return = current.equity / previous.equity - 1.0
        key = f"{label['trend']}|{label['volatility']}"
        buckets[key].append((interval_return, current.position_units > 0))
        labelled += 1

    groups: list[dict[str, object]] = []
    for key in sorted(buckets):
        observations = buckets[key]
        returns = [item[0] for item in observations]
        compounded = 1.0
        for value in returns:
            compounded *= 1.0 + value
        trend, volatility = key.split("|", 1)
        groups.append(
            {
                "regime": key,
                "trend": trend,
                "volatility": volatility,
                "observation_count": len(returns),
                "compounded_interval_return": compounded - 1.0,
                "mean_interval_return": sum(returns) / len(returns),
                "worst_interval_return": min(returns),
                "positive_interval_count": sum(value > 0 for value in returns),
                "exposed_observation_count": sum(item[1] for item in observations),
            }
        )

    return {
        "schema_version": "1.0.0",
        "artifact_id": "FQL-REGIME-ATTRIBUTION-001",
        "mode": "retrospective_diagnostics_only",
        "strategy_id": result.strategy_id,
        "instrument": result.instrument,
        "dataset": {
            "classification": "MODELLED",
            "path": dataset_path.as_posix(),
            "sha256": dataset_sha,
        },
        "regime_report": {
            "path": regime_report_path.as_posix(),
            "sha256": hashlib.sha256(regime_report_path.read_bytes()).hexdigest(),
        },
        "equity_observation_count": len(curve),
        "labelled_interval_count": labelled,
        "unlabelled_interval_count": (len(curve) - 1) - labelled,
        "labelled_interval_ratio": labelled / (len(curve) - 1),
        "groups": groups,
        "regimes_used_for_strategy_decisions": False,
        "performance_claim_allowed": False,
        "paper_trading_allowed": False,
        "live_orders_forbidden": True,
    }
