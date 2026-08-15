"""Domain models for deterministic research and paper-trading simulations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class Bar:
    """A time-zone-aware OHLC market bar known at ``timestamp``."""

    timestamp: datetime
    instrument: str
    open: float
    high: float
    low: float
    close: float

    def __post_init__(self) -> None:
        if self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None:
            raise ValueError("bar timestamp must be timezone-aware")
        if not self.instrument.strip():
            raise ValueError("instrument must not be empty")
        if min(self.open, self.high, self.low, self.close) <= 0:
            raise ValueError("OHLC prices must be positive")
        if self.high < max(self.open, self.close) or self.low > min(self.open, self.close):
            raise ValueError("OHLC values are inconsistent")
        if self.low > self.high:
            raise ValueError("bar low must not exceed high")


@dataclass(frozen=True, slots=True)
class Decision:
    """A target allocation produced after a bar closes."""

    signal_time: datetime
    target_weight: float
    reason: str


@dataclass(frozen=True, slots=True)
class Fill:
    """A simulated fill executed after a prior decision."""

    signal_time: datetime
    execution_time: datetime
    side: str
    units: float
    price: float
    commission: float
    reason: str

    @property
    def notional(self) -> float:
        return self.units * self.price


@dataclass(frozen=True, slots=True)
class EquityPoint:
    timestamp: datetime
    equity: float
    cash: float
    position_units: float
    close: float
    drawdown: float
    kill_switch_active: bool


@dataclass(frozen=True, slots=True)
class Metrics:
    initial_equity: float
    final_equity: float
    total_return: float
    max_drawdown: float
    trade_count: int
    turnover: float
    exposure_ratio: float
    kill_switch_triggered: bool


@dataclass(frozen=True, slots=True)
class BacktestResult:
    strategy_id: str
    instrument: str
    metrics: Metrics
    fills: tuple[Fill, ...]
    equity_curve: tuple[EquityPoint, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "instrument": self.instrument,
            "metrics": {
                "initial_equity": self.metrics.initial_equity,
                "final_equity": self.metrics.final_equity,
                "total_return": self.metrics.total_return,
                "max_drawdown": self.metrics.max_drawdown,
                "trade_count": self.metrics.trade_count,
                "turnover": self.metrics.turnover,
                "exposure_ratio": self.metrics.exposure_ratio,
                "kill_switch_triggered": self.metrics.kill_switch_triggered,
            },
            "fills": [
                {
                    "signal_time": fill.signal_time.isoformat(),
                    "execution_time": fill.execution_time.isoformat(),
                    "side": fill.side,
                    "units": fill.units,
                    "price": fill.price,
                    "commission": fill.commission,
                    "reason": fill.reason,
                }
                for fill in self.fills
            ],
            "equity_curve": [
                {
                    "timestamp": point.timestamp.isoformat(),
                    "equity": point.equity,
                    "cash": point.cash,
                    "position_units": point.position_units,
                    "close": point.close,
                    "drawdown": point.drawdown,
                    "kill_switch_active": point.kill_switch_active,
                }
                for point in self.equity_curve
            ],
        }
