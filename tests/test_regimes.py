import unittest
from datetime import UTC, datetime, timedelta

from father_quant_lab.models import Bar
from father_quant_lab.regimes import CausalRegimeClassifier, build_regime_report


def bars(closes: list[float]) -> tuple[Bar, ...]:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    return tuple(
        Bar(start + timedelta(days=index), "EUR/USD", value, value, value, value)
        for index, value in enumerate(closes)
    )


class RegimeClassifierTests(unittest.TestCase):
    def test_parameters_fail_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least 2"):
            CausalRegimeClassifier(lookback_bars=1)
        with self.assertRaisesRegex(ValueError, "trend_threshold"):
            CausalRegimeClassifier(trend_threshold_bps=0)
        with self.assertRaisesRegex(ValueError, "high_volatility"):
            CausalRegimeClassifier(high_volatility_threshold_bps=-1)

    def test_warmup_requires_lookback_plus_current_origin(self) -> None:
        classifier = CausalRegimeClassifier(lookback_bars=5)
        self.assertIsNone(classifier.classify(bars([1.0] * 5)))
        self.assertIsNotNone(classifier.classify(bars([1.0] * 6)))

    def test_classifies_up_down_and_range_with_fixed_threshold(self) -> None:
        classifier = CausalRegimeClassifier(
            lookback_bars=2,
            trend_threshold_bps=20,
            high_volatility_threshold_bps=10_000,
        )
        self.assertEqual(classifier.classify(bars([1.0, 1.001, 1.01])).trend, "UP")
        self.assertEqual(classifier.classify(bars([1.0, 0.999, 0.99])).trend, "DOWN")
        self.assertEqual(classifier.classify(bars([1.0, 1.0005, 1.001])).trend, "RANGE")

    def test_future_bar_cannot_change_past_label(self) -> None:
        classifier = CausalRegimeClassifier(lookback_bars=2)
        prefix = bars([1.0, 1.01, 1.02])
        before = classifier.classify(prefix)
        future = Bar(
            prefix[-1].timestamp + timedelta(days=1),
            "EUR/USD",
            9.0,
            9.0,
            9.0,
            9.0,
        )
        after = classifier.classify_all(prefix + (future,))[0]
        self.assertEqual(before, after)

    def test_high_volatility_branch_uses_registered_threshold(self) -> None:
        classifier = CausalRegimeClassifier(
            lookback_bars=2,
            trend_threshold_bps=20,
            high_volatility_threshold_bps=50,
        )
        label = classifier.classify(bars([1.0, 1.02, 0.99]))
        self.assertEqual(label.volatility, "HIGH")

    def test_report_keeps_all_trading_claims_closed(self) -> None:
        sample = bars([1.0, 1.001, 1.002, 1.003, 1.004, 1.005])
        report = build_regime_report(sample, CausalRegimeClassifier(), dataset_sha256="a" * 64)
        self.assertEqual(report["label_count"], 1)
        self.assertFalse(report["regime_truth_claimed"])
        self.assertFalse(report["performance_claim_allowed"])
        self.assertFalse(report["paper_trading_allowed"])
        self.assertTrue(report["live_orders_forbidden"])
