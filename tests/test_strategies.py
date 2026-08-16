import unittest
from datetime import UTC, datetime

from father_quant_lab.models import Bar
from father_quant_lab.strategies import MovingAverageCrossStrategy


def bars(closes: list[float]) -> list[Bar]:
    return [
        Bar(
            timestamp=datetime(2026, 1, index + 1, tzinfo=UTC),
            instrument="TEST/USD",
            open=close,
            high=close,
            low=close,
            close=close,
        )
        for index, close in enumerate(closes)
    ]


class MovingAverageCrossTests(unittest.TestCase):
    def test_windows_are_fail_closed(self) -> None:
        with self.assertRaises(ValueError):
            MovingAverageCrossStrategy(short_window=0, long_window=5)
        with self.assertRaises(ValueError):
            MovingAverageCrossStrategy(short_window=5, long_window=5)

    def test_waits_for_complete_long_window(self) -> None:
        strategy = MovingAverageCrossStrategy(short_window=2, long_window=3)
        history = bars([1, 2])
        self.assertIsNone(strategy.on_bar(0, history[:1]))
        self.assertIsNone(strategy.on_bar(1, history))

    def test_uses_available_closes_and_only_emits_on_state_change(self) -> None:
        strategy = MovingAverageCrossStrategy(short_window=2, long_window=3)
        history = bars([1, 2, 3, 4])
        decision = strategy.on_bar(2, history[:3])
        self.assertEqual(decision.target_weight, 1.0)
        self.assertEqual(decision.signal_time, history[2].timestamp)
        self.assertIsNone(strategy.on_bar(3, history[:4]))

    def test_future_bar_cannot_change_current_signal(self) -> None:
        first = MovingAverageCrossStrategy(short_window=2, long_window=3)
        second = MovingAverageCrossStrategy(short_window=2, long_window=3)
        common = bars([3, 2, 1])
        with_future_up = common + bars([1_000])
        with_future_down = common + bars([0.001])
        left = first.on_bar(2, with_future_up[:3])
        right = second.on_bar(2, with_future_down[:3])
        self.assertEqual(left.target_weight, right.target_weight)
        self.assertEqual(left.signal_time, right.signal_time)
