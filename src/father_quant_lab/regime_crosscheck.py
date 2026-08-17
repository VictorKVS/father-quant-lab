"""Independent Decimal oracle for cross-checking MODELLED regime labels."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any


LABEL_FIELDS = (
    "timestamp",
    "available_to_system_at",
    "trend",
    "volatility",
    "lookback_bars",
    "trend_return",
    "rms_log_return",
)


def _load_json(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("cross-check input must be a JSON object")
    return payload


def _canonical_sha(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _independent_labels(
    scenario: dict[str, Any], classifier: dict[str, Any]
) -> list[dict[str, object]]:
    """Recompute labels without importing either production classifier module."""

    lookback = classifier.get("lookback_bars")
    trend_bps = classifier.get("trend_threshold_bps")
    volatility_bps = classifier.get("high_volatility_threshold_bps")
    if not isinstance(lookback, int) or isinstance(lookback, bool) or lookback < 2:
        raise ValueError("cross-check lookback_bars must be an integer of at least 2")
    if not isinstance(trend_bps, (int, float)) or isinstance(trend_bps, bool) or trend_bps <= 0:
        raise ValueError("cross-check trend threshold must be positive")
    if (
        not isinstance(volatility_bps, (int, float))
        or isinstance(volatility_bps, bool)
        or volatility_bps <= 0
    ):
        raise ValueError("cross-check volatility threshold must be positive")
    returns = scenario.get("returns_bps")
    if not isinstance(returns, list) or any(
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or value <= -10_000
        for value in returns
    ):
        raise ValueError("cross-check returns must be numeric and greater than -10000 bps")

    with localcontext() as context:
        context.prec = 50
        closes = [Decimal(1)]
        for value in returns:
            closes.append(closes[-1] * (Decimal(1) + Decimal(str(value)) / Decimal(10_000)))
        trend_threshold = Decimal(str(trend_bps)) / Decimal(10_000)
        volatility_threshold = Decimal(str(volatility_bps)) / Decimal(10_000)
        start = datetime(2026, 2, 1, tzinfo=UTC)
        labels: list[dict[str, object]] = []
        for index in range(lookback, len(closes)):
            window = closes[index - lookback : index + 1]
            trend_return = window[-1] / window[0] - Decimal(1)
            log_returns = [
                (current / previous).ln()
                for previous, current in zip(window, window[1:])
            ]
            rms = (sum(value * value for value in log_returns) / Decimal(lookback)).sqrt()
            if trend_return > trend_threshold:
                trend = "UP"
            elif trend_return < -trend_threshold:
                trend = "DOWN"
            else:
                trend = "RANGE"
            volatility = "HIGH" if rms >= volatility_threshold else "NORMAL"
            timestamp = (start + timedelta(days=index)).isoformat()
            labels.append(
                {
                    "timestamp": timestamp,
                    "available_to_system_at": timestamp,
                    "trend": trend,
                    "volatility": volatility,
                    "lookback_bars": lookback,
                    "trend_return": str(trend_return),
                    "rms_log_return": str(rms),
                }
            )
    return labels


def crosscheck_regime_result(
    *,
    suite_path: str | Path,
    primary_result_path: str | Path,
    numeric_tolerance: str = "1e-12",
) -> dict[str, object]:
    suite_path = Path(suite_path)
    primary_result_path = Path(primary_result_path)
    suite = _load_json(suite_path)
    primary = _load_json(primary_result_path)
    if suite.get("classification") != "MODELLED" or suite.get("status") != "PRE_REGISTERED":
        raise ValueError("cross-check accepts only PRE_REGISTERED MODELLED suites")
    if primary.get("suite_id") != suite.get("suite_id"):
        raise ValueError("primary result suite ID does not match cross-check suite")
    suite_sha = hashlib.sha256(suite_path.read_bytes()).hexdigest()
    if primary.get("suite_sha256") != suite_sha:
        raise ValueError("primary result suite SHA-256 does not match cross-check suite")
    tolerance = Decimal(numeric_tolerance)
    if not tolerance.is_finite() or tolerance <= 0:
        raise ValueError("numeric tolerance must be finite and positive")

    scenarios = suite.get("scenarios")
    primary_scenarios = primary.get("scenarios")
    if not isinstance(scenarios, list) or not isinstance(primary_scenarios, list):
        raise ValueError("suite and primary result must contain scenario lists")
    primary_by_id = {
        item.get("scenario_id"): item for item in primary_scenarios if isinstance(item, dict)
    }
    expected_ids = [item.get("scenario_id") for item in scenarios if isinstance(item, dict)]
    if len(expected_ids) != len(scenarios) or len(set(expected_ids)) != len(expected_ids):
        raise ValueError("cross-check suite scenario IDs must be present and unique")
    if set(primary_by_id) != set(expected_ids) or len(primary_by_id) != len(primary_scenarios):
        raise ValueError("primary result scenario set does not match cross-check suite")

    mismatches: list[dict[str, object]] = []
    label_count = 0
    field_comparison_count = 0
    for scenario in scenarios:
        scenario_id = scenario["scenario_id"]
        primary_scenario = primary_by_id[scenario_id]
        if primary_scenario.get("definition_sha256") != _canonical_sha(scenario):
            raise ValueError(f"primary definition SHA-256 mismatch for {scenario_id}")
        primary_labels = primary_scenario.get("regime_report", {}).get("labels")
        if not isinstance(primary_labels, list):
            raise ValueError(f"primary labels missing for {scenario_id}")
        oracle_labels = _independent_labels(scenario, suite.get("classifier", {}))
        if len(primary_labels) != len(oracle_labels):
            mismatches.append(
                {
                    "scenario_id": scenario_id,
                    "field": "label_count",
                    "primary": len(primary_labels),
                    "oracle": len(oracle_labels),
                }
            )
        label_count += max(len(primary_labels), len(oracle_labels))
        for index, (primary_label, oracle_label) in enumerate(zip(primary_labels, oracle_labels)):
            for field in LABEL_FIELDS:
                field_comparison_count += 1
                primary_value = primary_label.get(field)
                oracle_value = oracle_label[field]
                if field in {"trend_return", "rms_log_return"}:
                    try:
                        difference = abs(Decimal(str(primary_value)) - Decimal(str(oracle_value)))
                    except Exception:
                        difference = Decimal("Infinity")
                    equal = difference <= tolerance
                else:
                    difference = None
                    equal = primary_value == oracle_value
                if not equal:
                    mismatch: dict[str, object] = {
                        "scenario_id": scenario_id,
                        "label_index": index,
                        "field": field,
                        "primary": primary_value,
                        "oracle": oracle_value,
                    }
                    if difference is not None:
                        mismatch["absolute_difference"] = str(difference)
                    mismatches.append(mismatch)

    return {
        "schema_version": "1.0.0",
        "artifact_id": "FQL-REGIME-CROSSCHECK-001",
        "mode": "independent_decimal_oracle",
        "classification": "MODELLED",
        "suite": {
            "path": suite_path.as_posix(),
            "sha256": suite_sha,
        },
        "primary_result": {
            "path": primary_result_path.as_posix(),
            "sha256": hashlib.sha256(primary_result_path.read_bytes()).hexdigest(),
        },
        "oracle": {
            "implementation": "standalone_decimal_recurrence_log_sqrt",
            "imports_primary_classifier": False,
            "imports_primary_fixture_generator": False,
            "numeric_tolerance": numeric_tolerance,
        },
        "scenario_count": len(scenarios),
        "label_count": label_count,
        "field_comparison_count": field_comparison_count,
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "status": (
            "PASS_INDEPENDENT_LABEL_EQUIVALENCE"
            if not mismatches
            else "BLOCKED_CROSSCHECK_MISMATCH"
        ),
        "regime_truth_claimed": False,
        "performance_claim_allowed": False,
        "paper_trading_allowed": False,
        "live_orders_forbidden": True,
    }
