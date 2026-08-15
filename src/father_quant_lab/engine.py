"""Small deterministic reference engine for cross-checking external frameworks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .data import validate_bars
from .models import BacktestResult, Bar, Decision, EquityPoint, Fill, Metrics
from .strategies import Strategy


@dataclass(frozen=True, slots=True)
class ExecutionCostModel:
    spread_bps: float = 1.0
    slippage_bps: float = 0.5
    commission_bps: float = 0.2

    def __post_init__(self) -> None:
        if min(self.spread_bps, self.slippage_bps, self.commission_bps) < 0:
            raise ValueError("execution costs must not be negative")

    @property
    def commission_rate(self) -> float:
        return self.commission_bps / 10_000

    def price(self, mid: float, side: str) -> float:
        half_spread = self.spread_bps / 20_000
        slippage = self.slippage_bps / 10_000
        direction = 1 if side == "BUY" else -1
        return mid * (1 + direction * (half_spread + slippage))


@dataclass(frozen=True, slots=True)
class RiskPolicy:
    max_position_weight: float = 1.0
    max_drawdown: float = 0.10

    def __post_init__(self) -> None:
        if not 0 <= self.max_position_weight <= 1:
            raise ValueError("max_position_weight must be in [0, 1]")
        if not 0 < self.max_drawdown < 1:
            raise ValueError("max_drawdown must be in (0, 1)")

    def approve(self, target_weight: float) -> float:
        if not 0 <= target_weight <= self.max_position_weight:
            raise ValueError(
                f"target weight {target_weight} violates long-only risk limit "
                f"[0, {self.max_position_weight}]"
            )
        return target_weight


@dataclass(slots=True)
class BacktestEngine:
    initial_equity: float = 10_000.0
    costs: ExecutionCostModel = ExecutionCostModel()
    risk: RiskPolicy = RiskPolicy()

    def __post_init__(self) -> None:
        if self.initial_equity <= 0:
            raise ValueError("initial_equity must be positive")

    def run(self, bars: Sequence[Bar], strategy: Strategy) -> BacktestResult:
        validated = validate_bars(list(bars))
        cash = self.initial_equity
        units = 0.0
        pending: Decision | None = None
        fills: list[Fill] = []
        curve: list[EquityPoint] = []
        high_watermark = self.initial_equity
        kill_switch = False

        for index, bar in enumerate(validated):
            if pending is not None:
                cash, units, fill = self._execute_target(cash, units, bar, pending)
                if fill is not None:
                    fills.append(fill)
                pending = None

            equity = cash + units * bar.close
            high_watermark = max(high_watermark, equity)
            drawdown = 0.0 if high_watermark == 0 else 1 - equity / high_watermark

            if drawdown >= self.risk.max_drawdown and not kill_switch:
                kill_switch = True
                pending = Decision(bar.timestamp, 0.0, "risk kill switch")
            elif not kill_switch:
                decision = strategy.on_bar(index, validated[: index + 1])
                if decision is not None:
                    pending = Decision(
                        signal_time=decision.signal_time,
                        target_weight=self.risk.approve(decision.target_weight),
                        reason=decision.reason,
                    )

            curve.append(
                EquityPoint(
                    timestamp=bar.timestamp,
                    equity=equity,
                    cash=cash,
                    position_units=units,
                    close=bar.close,
                    drawdown=drawdown,
                    kill_switch_active=kill_switch,
                )
            )

        if units > 0:
            final_bar = validated[-1]
            liquidation = Decision(final_bar.timestamp, 0.0, "end-of-test liquidation")
            cash, units, fill = self._execute_target(cash, units, final_bar, liquidation, at_close=True)
            if fill is not None:
                fills.append(fill)
            high_watermark = max(high_watermark, cash)
            drawdown = 1 - cash / high_watermark
            curve[-1] = EquityPoint(
                timestamp=final_bar.timestamp,
                equity=cash,
                cash=cash,
                position_units=0.0,
                close=final_bar.close,
                drawdown=drawdown,
                kill_switch_active=kill_switch,
            )

        metrics = self._metrics(curve, fills, kill_switch)
        return BacktestResult(
            strategy_id=strategy.strategy_id,
            instrument=validated[0].instrument,
            metrics=metrics,
            fills=tuple(fills),
            equity_curve=tuple(curve),
        )

    def _execute_target(
        self,
        cash: float,
        units: float,
        bar: Bar,
        decision: Decision,
        *,
        at_close: bool = False,
    ) -> tuple[float, float, Fill | None]:
        mid = bar.close if at_close else bar.open
        equity = cash + units * mid
        desired_units = equity * decision.target_weight / mid
        delta = desired_units - units
        if abs(delta) < 1e-12:
            return cash, units, None

        side = "BUY" if delta > 0 else "SELL"
        execution_price = self.costs.price(mid, side)
        if side == "BUY":
            affordable = cash / (execution_price * (1 + self.costs.commission_rate))
            delta = min(delta, max(0.0, affordable))
            if delta < 1e-12:
                return cash, units, None

        traded_units = abs(delta)
        notional = traded_units * execution_price
        commission = notional * self.costs.commission_rate
        cash -= delta * execution_price + commission
        units += delta
        if abs(cash) < 1e-10:
            cash = 0.0
        if abs(units) < 1e-12:
            units = 0.0
        return (
            cash,
            units,
            Fill(
                signal_time=decision.signal_time,
                execution_time=bar.timestamp,
                side=side,
                units=traded_units,
                price=execution_price,
                commission=commission,
                reason=decision.reason,
            ),
        )

    def _metrics(
        self,
        curve: Sequence[EquityPoint],
        fills: Sequence[Fill],
        kill_switch: bool,
    ) -> Metrics:
        final_equity = curve[-1].equity
        turnover = sum(fill.notional for fill in fills) / self.initial_equity
        exposed = sum(point.position_units > 0 for point in curve)
        return Metrics(
            initial_equity=self.initial_equity,
            final_equity=final_equity,
            total_return=final_equity / self.initial_equity - 1,
            max_drawdown=max(point.drawdown for point in curve),
            trade_count=len(fills),
            turnover=turnover,
            exposure_ratio=exposed / len(curve),
            kill_switch_triggered=kill_switch,
        )
