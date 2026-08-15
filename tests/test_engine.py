import unittest
from datetime import UTC, datetime

from father_quant_lab.engine import BacktestEngine, ExecutionCostModel, RiskPolicy
from father_quant_lab.models import Bar
from father_quant_lab.strategies import (
    BuyHoldStrategy,
    NoTradeStrategy,
    PeriodicRebalanceStrategy,
    RandomStrategy,
)


def make_bar(day: int, open_: float, close: float) -> Bar:
    return Bar(
        timestamp=datetime(2026, 1, day, tzinfo=UTC),
        instrument="TEST/USD",
        open=open_,
        high=max(open_, close),
        low=min(open_, close),
        close=close,
    )


ZERO_COST = ExecutionCostModel(spread_bps=0, slippage_bps=0, commission_bps=0)


class ReferenceEngineTests(unittest.TestCase):
    def test_no_trade_is_flat_and_has_no_fills(self) -> None:
        bars = [make_bar(1, 100, 110), make_bar(2, 110, 120)]
        result = BacktestEngine(costs=ZERO_COST).run(bars, NoTradeStrategy())
        self.assertEqual(result.metrics.final_equity, 10_000)
        self.assertEqual(result.metrics.trade_count, 0)
        self.assertEqual(result.metrics.exposure_ratio, 0)

    def test_signal_is_executed_on_next_bar_not_current_close(self) -> None:
        bars = [
            make_bar(1, 100, 100),
            make_bar(2, 110, 120),
            make_bar(3, 125, 130),
        ]
        result = BacktestEngine(costs=ZERO_COST).run(bars, BuyHoldStrategy())
        first_fill = result.fills[0]
        self.assertEqual(first_fill.signal_time, bars[0].timestamp)
        self.assertEqual(first_fill.execution_time, bars[1].timestamp)
        self.assertEqual(first_fill.price, 110)
        self.assertAlmostEqual(result.metrics.final_equity, 10_000 / 110 * 130)

    def test_seeded_random_strategy_is_reproducible(self) -> None:
        bars = [make_bar(day, 100 + day, 100 + day) for day in range(1, 8)]
        engine = BacktestEngine(costs=ZERO_COST)
        first = engine.run(bars, RandomStrategy(seed=7)).to_dict()
        second = engine.run(bars, RandomStrategy(seed=7)).to_dict()
        self.assertEqual(first, second)

    def test_costs_reduce_buy_hold_result(self) -> None:
        bars = [make_bar(1, 100, 100), make_bar(2, 100, 110), make_bar(3, 110, 120)]
        free = BacktestEngine(costs=ZERO_COST).run(bars, BuyHoldStrategy())
        costly = BacktestEngine(
            costs=ExecutionCostModel(spread_bps=10, slippage_bps=5, commission_bps=5)
        ).run(bars, BuyHoldStrategy())
        self.assertLess(costly.metrics.final_equity, free.metrics.final_equity)

    def test_kill_switch_liquidates_and_blocks_reentry(self) -> None:
        bars = [
            make_bar(1, 100, 100),
            make_bar(2, 100, 100),
            make_bar(3, 100, 75),
            make_bar(4, 75, 80),
            make_bar(5, 80, 120),
        ]
        engine = BacktestEngine(costs=ZERO_COST, risk=RiskPolicy(max_drawdown=0.10))
        result = engine.run(bars, BuyHoldStrategy())
        self.assertTrue(result.metrics.kill_switch_triggered)
        self.assertEqual(result.fills[-1].reason, "risk kill switch")
        self.assertEqual(result.equity_curve[-1].position_units, 0)

    def test_periodic_strategy_does_not_emit_every_bar(self) -> None:
        bars = [make_bar(day, 100 + day, 100 + day) for day in range(1, 7)]
        strategy = PeriodicRebalanceStrategy(target_weight=0.5, rebalance_every=3)
        result = BacktestEngine(costs=ZERO_COST).run(bars, strategy)
        self.assertGreaterEqual(result.metrics.trade_count, 2)
        self.assertLess(result.metrics.trade_count, len(bars))

    def test_risk_policy_rejects_leverage_and_short_targets(self) -> None:
        risk = RiskPolicy(max_position_weight=1.0)
        with self.assertRaises(ValueError):
            risk.approve(1.1)
        with self.assertRaises(ValueError):
            risk.approve(-0.1)
