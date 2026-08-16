"""Causal, deterministic market-regime labels for research diagnostics."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

from .models import Bar


@dataclass(frozen=True, slots=True)
class RegimeLabel:
    timestamp: str
    available_to_system_at: str
    trend: str
    volatility: str
    trend_return: float
    rms_log_return: float
    lookback_bars: int

    def to_dict(self) -> dict[str, object]:
        return {
            "timestamp": self.timestamp,
            "available_to_system_at": self.available_to_system_at,
            "trend": self.trend,
            "volatility": self.volatility,
            "trend_return": self.trend_return,
            "rms_log_return": self.rms_log_return,
            "lookback_bars": self.lookback_bars,
        }


@dataclass(frozen=True, slots=True)
class CausalRegimeClassifier:
    lookback_bars: int = 5
    trend_threshold_bps: float = 20.0
    high_volatility_threshold_bps: float = 50.0

    def __post_init__(self) -> None:
        if self.lookback_bars < 2:
            raise ValueError("lookback_bars must be at least 2")
        if self.trend_threshold_bps <= 0:
            raise ValueError("trend_threshold_bps must be positive")
        if self.high_volatility_threshold_bps <= 0:
            raise ValueError("high_volatility_threshold_bps must be positive")

    def classify(self, history: Sequence[Bar]) -> RegimeLabel | None:
        required = self.lookback_bars + 1
        if len(history) < required:
            return None
        window = history[-required:]
        closes = [bar.close for bar in window]
        trend_return = closes[-1] / closes[0] - 1.0
        log_returns = [math.log(current / previous) for previous, current in zip(closes, closes[1:])]
        rms_log_return = math.sqrt(sum(value * value for value in log_returns) / len(log_returns))

        trend_threshold = self.trend_threshold_bps / 10_000
        if trend_return > trend_threshold:
            trend = "UP"
        elif trend_return < -trend_threshold:
            trend = "DOWN"
        else:
            trend = "RANGE"
        volatility = (
            "HIGH"
            if rms_log_return >= self.high_volatility_threshold_bps / 10_000
            else "NORMAL"
        )
        timestamp = history[-1].timestamp.isoformat()
        return RegimeLabel(
            timestamp=timestamp,
            available_to_system_at=timestamp,
            trend=trend,
            volatility=volatility,
            trend_return=trend_return,
            rms_log_return=rms_log_return,
            lookback_bars=self.lookback_bars,
        )

    def classify_all(self, bars: Sequence[Bar]) -> tuple[RegimeLabel, ...]:
        labels: list[RegimeLabel] = []
        for index in range(len(bars)):
            label = self.classify(bars[: index + 1])
            if label is not None:
                labels.append(label)
        return tuple(labels)


def build_regime_report(
    bars: Sequence[Bar], classifier: CausalRegimeClassifier, *, dataset_sha256: str
) -> dict[str, object]:
    labels = classifier.classify_all(bars)
    return {
        "schema_version": "1.0.0",
        "artifact_id": "FQL-REGIME-LABELS-001",
        "mode": "research_diagnostics_only",
        "dataset": {
            "instrument": bars[0].instrument,
            "classification": "MODELLED",
            "sha256": dataset_sha256,
            "bar_count": len(bars),
        },
        "parameters": {
            "lookback_bars": classifier.lookback_bars,
            "trend_threshold_bps": classifier.trend_threshold_bps,
            "high_volatility_threshold_bps": classifier.high_volatility_threshold_bps,
            "optimized": False,
        },
        "causality": "past_and_current_closed_bars_only",
        "warmup_bars": classifier.lookback_bars,
        "label_count": len(labels),
        "labels": [label.to_dict() for label in labels],
        "regime_truth_claimed": False,
        "performance_claim_allowed": False,
        "paper_trading_allowed": False,
        "live_orders_forbidden": True,
    }
