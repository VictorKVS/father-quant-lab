"""Fail-closed validation for pre-registered chronological experiments."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import Bar

REQUIRED_SPLITS = ("TRAIN", "VALIDATION", "OUT_OF_SAMPLE")
ALLOWED_CLASSIFICATIONS = {
    "REAL_TRADED",
    "OFFICIAL_REFERENCE",
    "SYNTHETIC_RECONSTRUCTION",
    "MODELLED",
}


def _aware_timestamp(value: object, field: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be an ISO-8601 timestamp")
    parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    return parsed


def load_experiment_plan(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != "1.0.0":
        raise ValueError("unsupported experiment-plan schema")
    if not isinstance(payload.get("plan_id"), str) or not payload["plan_id"].strip():
        raise ValueError("plan_id is required")
    if payload.get("registration_status") != "SEALED":
        raise ValueError("experiment plan must be SEALED before validation")
    if payload.get("registered_before_evaluation") is not True:
        raise ValueError("plan must be registered before evaluation")
    if payload.get("optimization_performed") is not False:
        raise ValueError("optimization_performed must be false")
    if payload.get("live_orders_forbidden") is not True:
        raise ValueError("live_orders_forbidden must be true")
    if payload.get("out_of_sample_access") != "SEALED_UNTIL_FINAL_EVALUATION":
        raise ValueError("out-of-sample access must remain sealed")

    dataset = payload.get("dataset")
    if not isinstance(dataset, dict):
        raise ValueError("dataset registration is required")
    digest = dataset.get("sha256")
    if not isinstance(digest, str) or len(digest) != 64:
        raise ValueError("dataset sha256 must be a 64-character digest")
    try:
        int(digest, 16)
    except ValueError as error:
        raise ValueError("dataset sha256 must be hexadecimal") from error
    if dataset.get("classification") not in ALLOWED_CLASSIFICATIONS:
        raise ValueError("unsupported dataset classification")
    if not dataset.get("instrument"):
        raise ValueError("dataset instrument is required")

    strategy = payload.get("strategy")
    if not isinstance(strategy, dict) or not strategy.get("strategy_id"):
        raise ValueError("strategy registration is required")
    if not isinstance(strategy.get("parameters"), dict):
        raise ValueError("strategy parameters must be registered")

    splits = payload.get("splits")
    if (
        not isinstance(splits, list)
        or any(not isinstance(item, dict) for item in splits)
        or [item.get("name") for item in splits] != list(REQUIRED_SPLITS)
    ):
        raise ValueError("splits must be TRAIN, VALIDATION, OUT_OF_SAMPLE in order")
    embargo = payload.get("embargo_bars")
    if not isinstance(embargo, int) or isinstance(embargo, bool) or embargo < 0:
        raise ValueError("embargo_bars must be a non-negative integer")
    return payload


def evaluate_experiment_plan(
    plan: dict[str, Any], *, dataset_path: str | Path, bars: tuple[Bar, ...]
) -> dict[str, object]:
    dataset_path = Path(dataset_path)
    actual_sha = hashlib.sha256(dataset_path.read_bytes()).hexdigest()
    expected = plan["dataset"]
    if actual_sha != expected["sha256"]:
        raise ValueError("dataset SHA-256 does not match the sealed plan")
    instruments = {bar.instrument for bar in bars}
    if instruments != {expected["instrument"]}:
        raise ValueError("dataset instrument does not match the sealed plan")

    index_by_time = {bar.timestamp: index for index, bar in enumerate(bars)}
    evaluated: list[dict[str, object]] = []
    previous_end_index: int | None = None
    embargo = plan["embargo_bars"]
    for split in plan["splits"]:
        start = _aware_timestamp(split.get("start"), f"{split['name']}.start")
        end = _aware_timestamp(split.get("end"), f"{split['name']}.end")
        if start > end:
            raise ValueError(f"{split['name']} start must not exceed end")
        if start not in index_by_time or end not in index_by_time:
            raise ValueError(f"{split['name']} boundaries must match dataset bars")
        start_index = index_by_time[start]
        end_index = index_by_time[end]
        if start_index > end_index:
            raise ValueError(f"{split['name']} boundaries are not chronological")
        if previous_end_index is not None:
            unused_bars = start_index - previous_end_index - 1
            if unused_bars < embargo:
                raise ValueError("splits overlap or violate the registered embargo")
        evaluated.append(
            {
                "name": split["name"],
                "start": start.isoformat(),
                "end": end.isoformat(),
                "bar_count": end_index - start_index + 1,
            }
        )
        previous_end_index = end_index

    classification = expected["classification"]
    return {
        "schema_version": "1.0.0",
        "gate_id": "FQL-S4-GATE-004",
        "plan_id": plan["plan_id"],
        "status": "VALID_MODELLED_ONLY" if classification == "MODELLED" else "STRUCTURE_VALID",
        "dataset": {
            "path": dataset_path.as_posix(),
            "sha256": actual_sha,
            "classification": classification,
            "instrument": expected["instrument"],
            "bar_count": len(bars),
        },
        "strategy": plan["strategy"],
        "embargo_bars": embargo,
        "splits": evaluated,
        "optimization_performed": False,
        "out_of_sample_access": "SEALED_UNTIL_FINAL_EVALUATION",
        "performance_claim_allowed": False,
        "paper_trading_allowed": False,
        "live_orders_forbidden": True,
        "decision": "plan structure accepted; dataset admission and performance evidence remain separate gates",
    }
