"""Deterministic synthetic scenarios for mechanical regime-branch coverage."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from .models import Bar
from .regimes import CausalRegimeClassifier, build_regime_report


def load_stress_suite(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != "1.0.0":
        raise ValueError("unsupported stress-suite schema")
    if payload.get("status") != "PRE_REGISTERED":
        raise ValueError("stress suite must be PRE_REGISTERED")
    if payload.get("classification") != "MODELLED" or payload.get("subtype") != "DETERMINISTIC_STRESS":
        raise ValueError("stress suite must remain MODELLED deterministic stress")
    if payload.get("performance_claim_allowed") is not False:
        raise ValueError("stress suite cannot allow performance claims")
    if payload.get("live_orders_forbidden") is not True:
        raise ValueError("stress suite must forbid LIVE orders")
    scenarios = payload.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        raise ValueError("stress suite must contain scenarios")
    identifiers = [item.get("scenario_id") for item in scenarios if isinstance(item, dict)]
    if len(identifiers) != len(scenarios) or any(not item for item in identifiers):
        raise ValueError("every stress scenario must be an object with an ID")
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("stress scenario IDs must be unique")
    for scenario in scenarios:
        returns = scenario.get("returns_bps")
        if not isinstance(returns, list) or len(returns) < 2:
            raise ValueError("each stress scenario needs at least two returns")
        if any(
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or value <= -10_000
            for value in returns
        ):
            raise ValueError("stress returns must be numeric and greater than -10000 bps")
    return payload


def generate_bars(scenario: dict[str, Any]) -> tuple[Bar, ...]:
    start = datetime(2026, 2, 1, tzinfo=UTC)
    closes = [1.0]
    for return_bps in scenario["returns_bps"]:
        closes.append(closes[-1] * (1.0 + return_bps / 10_000))
    result: list[Bar] = []
    previous = closes[0]
    for index, close in enumerate(closes):
        open_price = previous if index else close
        result.append(
            Bar(
                timestamp=start + timedelta(days=index),
                instrument="EUR/USD",
                open=open_price,
                high=max(open_price, close) * 1.0001,
                low=min(open_price, close) * 0.9999,
                close=close,
            )
        )
        previous = close
    return tuple(result)


def run_stress_suite(payload: dict[str, Any], *, suite_path: str | Path) -> dict[str, object]:
    config = payload["classifier"]
    classifier = CausalRegimeClassifier(
        lookback_bars=config["lookback_bars"],
        trend_threshold_bps=config["trend_threshold_bps"],
        high_volatility_threshold_bps=config["high_volatility_threshold_bps"],
    )
    observed_trends: set[str] = set()
    observed_volatility: set[str] = set()
    scenarios: list[dict[str, object]] = []
    for scenario in payload["scenarios"]:
        definition = json.dumps(scenario, sort_keys=True, separators=(",", ":")).encode()
        definition_sha = hashlib.sha256(definition).hexdigest()
        report = build_regime_report(
            generate_bars(scenario), classifier, dataset_sha256=definition_sha
        )
        report["dataset"]["subtype"] = "DETERMINISTIC_STRESS"
        trends = sorted({item["trend"] for item in report["labels"]})
        volatility = sorted({item["volatility"] for item in report["labels"]})
        observed_trends.update(trends)
        observed_volatility.update(volatility)
        scenarios.append(
            {
                "scenario_id": scenario["scenario_id"],
                "definition_sha256": definition_sha,
                "observed_trend_classes": trends,
                "observed_volatility_classes": volatility,
                "regime_report": report,
            }
        )
    required_trends = set(payload["required_trend_classes"])
    required_volatility = set(payload["required_volatility_classes"])
    missing_trends = sorted(required_trends - observed_trends)
    missing_volatility = sorted(required_volatility - observed_volatility)
    passed = not missing_trends and not missing_volatility
    suite_path = Path(suite_path)
    return {
        "schema_version": "1.0.0",
        "artifact_id": "FQL-STRESS-REGIME-001",
        "suite_id": payload["suite_id"],
        "suite_path": suite_path.as_posix(),
        "suite_sha256": hashlib.sha256(suite_path.read_bytes()).hexdigest(),
        "classification": "MODELLED",
        "subtype": "DETERMINISTIC_STRESS",
        "status": "PASS_MECHANICAL_BRANCH_COVERAGE" if passed else "BLOCKED_MISSING_BRANCHES",
        "observed_trend_classes": sorted(observed_trends),
        "observed_volatility_classes": sorted(observed_volatility),
        "missing_trend_classes": missing_trends,
        "missing_volatility_classes": missing_volatility,
        "scenarios": scenarios,
        "historical_likelihood_claimed": False,
        "performance_claim_allowed": False,
        "paper_trading_allowed": False,
        "live_orders_forbidden": True,
    }
