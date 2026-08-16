import copy
import unittest
from pathlib import Path

from father_quant_lab.data import load_bars_csv
from father_quant_lab.engine import BacktestEngine
from father_quant_lab.regime_attribution import attribute_result, load_regime_report
from father_quant_lab.strategies import MovingAverageCrossStrategy

DATA = Path("data/samples/eurusd_daily_sample.csv")
REGIMES = Path("evidence/runs/RUN-M0-S6-REGIME-20260816/result.json")


def backtest():
    return BacktestEngine().run(load_bars_csv(DATA), MovingAverageCrossStrategy())


class RegimeAttributionTests(unittest.TestCase):
    def test_modelled_attribution_is_retrospective_and_closed(self) -> None:
        report = attribute_result(
            backtest(),
            load_regime_report(REGIMES),
            dataset_path=DATA,
            regime_report_path=REGIMES,
        )
        self.assertEqual(report["labelled_interval_count"], 7)
        self.assertEqual(report["unlabelled_interval_count"], 4)
        self.assertFalse(report["regimes_used_for_strategy_decisions"])
        self.assertFalse(report["performance_claim_allowed"])
        self.assertTrue(report["live_orders_forbidden"])

    def test_duplicate_regime_timestamp_fails_closed(self) -> None:
        regimes = load_regime_report(REGIMES)
        regimes["labels"].append(copy.deepcopy(regimes["labels"][0]))
        with self.assertRaisesRegex(ValueError, "unique"):
            attribute_result(
                backtest(), regimes, dataset_path=DATA, regime_report_path=REGIMES
            )

    def test_unknown_equity_timestamp_fails_closed(self) -> None:
        regimes = load_regime_report(REGIMES)
        regimes["labels"][0]["timestamp"] = "2030-01-01T00:00:00+00:00"
        regimes["labels"][0]["available_to_system_at"] = "2030-01-01T00:00:00+00:00"
        with self.assertRaisesRegex(ValueError, "equity-curve"):
            attribute_result(
                backtest(), regimes, dataset_path=DATA, regime_report_path=REGIMES
            )

    def test_availability_mismatch_fails_closed(self) -> None:
        regimes = load_regime_report(REGIMES)
        regimes["labels"][0]["available_to_system_at"] = "2030-01-01T00:00:00+00:00"
        with self.assertRaisesRegex(ValueError, "available"):
            attribute_result(
                backtest(), regimes, dataset_path=DATA, regime_report_path=REGIMES
            )
