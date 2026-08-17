import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from father_quant_lab.cli import main


class CliTests(unittest.TestCase):
    def test_cli_runs_modelled_regime_stress_suite(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "stress.json"
            exit_code = main(
                [
                    "run-regime-stress",
                    "--suite",
                    "configs/stress/regime-branch-suite.json",
                    "--output",
                    str(output),
                ]
            )
            result = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(exit_code, 0)
        self.assertEqual(result["status"], "PASS_MECHANICAL_BRANCH_COVERAGE")
        self.assertFalse(result["paper_trading_allowed"])
        self.assertTrue(result["live_orders_forbidden"])

    def test_cli_attributes_regimes_without_using_them_for_decisions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "attribution.json"
            exit_code = main(
                [
                    "attribute-regime-performance",
                    "--data",
                    "data/samples/eurusd_daily_sample.csv",
                    "--regimes",
                    "evidence/runs/RUN-M0-S6-REGIME-20260816/result.json",
                    "--output",
                    str(output),
                ]
            )
            report = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(exit_code, 0)
        self.assertEqual(report["labelled_interval_count"], 7)
        self.assertFalse(report["regimes_used_for_strategy_decisions"])
        self.assertFalse(report["paper_trading_allowed"])

    def test_cli_creates_causal_regime_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "regimes.json"
            exit_code = main(
                [
                    "label-regimes",
                    "--data",
                    "data/samples/eurusd_daily_sample.csv",
                    "--output",
                    str(output),
                    "--lookback-bars",
                    "5",
                ]
            )
            result = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(exit_code, 0)
        self.assertEqual(result["label_count"], 7)
        self.assertEqual(result["causality"], "past_and_current_closed_bars_only")
        self.assertFalse(result["regime_truth_claimed"])
        self.assertTrue(result["live_orders_forbidden"])

    def test_cli_blocks_insufficient_plan_without_opening_trading(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "sufficiency.json"
            exit_code = main(
                [
                    "evaluate-plan-sufficiency",
                    "--plan-result",
                    "evidence/runs/RUN-M0-S4-PLAN-20260816/result.json",
                    "--criteria",
                    "configs/evaluation/m0-mechanical-sufficiency.json",
                    "--output",
                    str(output),
                ]
            )
            result = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(exit_code, 0)
        self.assertEqual(result["status"], "BLOCKED_INSUFFICIENT_BARS")
        self.assertFalse(result["paper_trading_allowed"])
        self.assertTrue(result["live_orders_forbidden"])

    def test_cli_validates_sealed_experiment_plan(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "plan-result.json"
            exit_code = main(
                [
                    "validate-experiment-plan",
                    "--plan",
                    "configs/experiments/BOT-RULE-101-modelled-preregistered.json",
                    "--data",
                    "data/samples/eurusd_daily_sample.csv",
                    "--output",
                    str(output),
                ]
            )
            result = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(exit_code, 0)
        self.assertEqual(result["gate_id"], "FQL-S4-GATE-004")
        self.assertEqual(result["status"], "VALID_MODELLED_ONLY")
        self.assertFalse(result["performance_claim_allowed"])

    def test_run_controls_records_reproducibility_and_safety_config(self) -> None:
        fixture = Path("data/samples/eurusd_daily_sample.csv")
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "controls.json"
            exit_code = main(
                [
                    "run-controls",
                    "--data",
                    str(fixture),
                    "--output",
                    str(output),
                    "--seed",
                    "17",
                ]
            )
            report = json.loads(output.read_text(encoding="utf-8"))
            passport_path = output.with_name("controls.passport.json")
            passport = json.loads(passport_path.read_text(encoding="utf-8"))

        expected_hash = hashlib.sha256(fixture.read_bytes()).hexdigest()
        self.assertEqual(exit_code, 0)
        self.assertEqual(report["mode"], "backtest_only")
        self.assertTrue(report["live_orders_forbidden"])
        self.assertEqual(report["run_config"]["dataset"]["sha256"], expected_hash)
        self.assertEqual(report["run_config"]["dataset"]["classification"], "MODELLED")
        self.assertEqual(report["run_config"]["seed"], 17)
        self.assertFalse(report["run_config"]["risk"]["short_allowed"])
        self.assertFalse(report["run_config"]["risk"]["leverage_allowed"])
        self.assertEqual(len(report["results"]), 4)
        self.assertEqual(passport["passport_type"], "experiment_run")
        self.assertEqual(passport["provenance"]["report_path"], output.as_posix())
        self.assertEqual(passport["provenance"]["dataset_sha256"], expected_hash)
        self.assertTrue(passport["safety"]["live_orders_forbidden"])
        self.assertIn("future profitability", passport["interpretation"]["not_proved"])

    def test_rule_baseline_compares_candidate_to_all_controls(self) -> None:
        fixture = Path("data/samples/eurusd_daily_sample.csv")
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "rule.json"
            exit_code = main(
                [
                    "run-rule-baseline",
                    "--data",
                    str(fixture),
                    "--output",
                    str(output),
                    "--seed",
                    "17",
                    "--short-window",
                    "3",
                    "--long-window",
                    "5",
                ]
            )
            report = json.loads(output.read_text(encoding="utf-8"))
            passport = json.loads(
                output.with_name("rule.passport.json").read_text(encoding="utf-8")
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(len(report["results"]), 5)
        self.assertEqual(
            {result["strategy_id"] for result in report["results"]},
            {"BOT-CTRL-000", "BOT-CTRL-001", "BOT-CTRL-002", "BOT-CTRL-003", "BOT-RULE-101"},
        )
        self.assertEqual(report["run_config"]["rule"]["optimization_performed"], False)
        self.assertEqual(passport["parameters"], {"short_window": 3, "long_window": 5})
        self.assertFalse(passport["safety"]["performance_claim_allowed"])
        self.assertIn("out-of-sample performance", passport["interpretation"]["not_proved"])


if __name__ == "__main__":
    unittest.main()
