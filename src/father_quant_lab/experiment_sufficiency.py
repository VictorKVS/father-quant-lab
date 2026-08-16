"""Independent evidence-sufficiency gate for a validated experiment plan."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

REQUIRED_SPLITS = ("TRAIN", "VALIDATION", "OUT_OF_SAMPLE")


def _load_json_object(path: str | Path, label: str) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be a JSON object")
    return payload


def load_sufficiency_criteria(path: str | Path) -> dict[str, Any]:
    criteria = _load_json_object(path, "sufficiency criteria")
    if criteria.get("schema_version") != "1.0.0":
        raise ValueError("unsupported sufficiency-criteria schema")
    if criteria.get("status") != "PRE_REGISTERED":
        raise ValueError("sufficiency criteria must be PRE_REGISTERED")
    if criteria.get("basis") != "MECHANICAL_SMOKE_ONLY":
        raise ValueError("criteria basis must not imply statistical sufficiency")
    minimum = criteria.get("minimum_scored_bars_per_split")
    if not isinstance(minimum, int) or isinstance(minimum, bool) or minimum < 1:
        raise ValueError("minimum_scored_bars_per_split must be a positive integer")
    if criteria.get("independent_warmup_per_split") is not True:
        raise ValueError("each split must have independent warmup")
    return criteria


def load_plan_result(path: str | Path) -> dict[str, Any]:
    result = _load_json_object(path, "plan result")
    if result.get("gate_id") != "FQL-S4-GATE-004":
        raise ValueError("unsupported plan-gate result")
    splits = result.get("splits")
    if (
        not isinstance(splits, list)
        or any(not isinstance(item, dict) for item in splits)
        or tuple(item.get("name") for item in splits) != REQUIRED_SPLITS
    ):
        raise ValueError("plan result must contain the three ordered splits")
    if result.get("live_orders_forbidden") is not True:
        raise ValueError("plan result must preserve the LIVE prohibition")
    return result


def _strategy_lookback(result: dict[str, Any]) -> int:
    strategy = result.get("strategy")
    parameters = strategy.get("parameters") if isinstance(strategy, dict) else None
    if not isinstance(parameters, dict):
        raise ValueError("strategy parameters are required for sufficiency evaluation")
    windows = [
        value
        for key, value in parameters.items()
        if key.endswith("_window")
        and isinstance(value, int)
        and not isinstance(value, bool)
        and value > 0
    ]
    if not windows:
        raise ValueError("at least one positive *_window parameter is required")
    return max(windows)


def evaluate_sufficiency(
    result: dict[str, Any],
    criteria: dict[str, Any],
    *,
    result_path: str | Path,
    criteria_path: str | Path,
) -> dict[str, object]:
    lookback = _strategy_lookback(result)
    scored = criteria["minimum_scored_bars_per_split"]
    required_total = lookback + scored
    decisions: list[dict[str, object]] = []
    for split in result["splits"]:
        count = split.get("bar_count")
        if not isinstance(count, int) or isinstance(count, bool) or count < 1:
            raise ValueError("split bar_count must be a positive integer")
        deficit = max(required_total - count, 0)
        decisions.append(
            {
                "name": split["name"],
                "actual_bars": count,
                "warmup_bars": lookback,
                "minimum_scored_bars": scored,
                "required_total_bars": required_total,
                "deficit_bars": deficit,
                "status": "PASS" if deficit == 0 else "BLOCKED",
            }
        )
    passed = all(item["status"] == "PASS" for item in decisions)
    result_path = Path(result_path)
    criteria_path = Path(criteria_path)
    return {
        "schema_version": "1.0.0",
        "gate_id": "FQL-S4-GATE-005",
        "plan_id": result["plan_id"],
        "criteria_id": criteria["criteria_id"],
        "status": "PASS_MECHANICAL_MINIMUM" if passed else "BLOCKED_INSUFFICIENT_BARS",
        "basis": "MECHANICAL_SMOKE_ONLY",
        "provenance": {
            "plan_result_path": result_path.as_posix(),
            "plan_result_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
            "criteria_path": criteria_path.as_posix(),
            "criteria_sha256": hashlib.sha256(criteria_path.read_bytes()).hexdigest(),
        },
        "strategy_lookback_bars": lookback,
        "decisions": decisions,
        "statistical_sufficiency_proved": False,
        "performance_claim_allowed": False,
        "paper_trading_allowed": False,
        "live_orders_forbidden": True,
        "decision": (
            "mechanical minimum met; statistical design and dataset admission remain blocked"
            if passed
            else "do not evaluate strategy; obtain longer admitted data and register a new plan"
        ),
    }
