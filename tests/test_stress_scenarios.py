import copy
import json
import tempfile
import unittest
from pathlib import Path

from father_quant_lab.stress_scenarios import load_stress_suite, run_stress_suite

SUITE = Path("configs/stress/regime-branch-suite.json")


class StressScenarioTests(unittest.TestCase):
    def test_registered_suite_covers_every_regime_branch(self) -> None:
        result = run_stress_suite(load_stress_suite(SUITE), suite_path=SUITE)
        self.assertEqual(result["status"], "PASS_MECHANICAL_BRANCH_COVERAGE")
        self.assertEqual(result["observed_trend_classes"], ["DOWN", "RANGE", "UP"])
        self.assertEqual(result["observed_volatility_classes"], ["HIGH", "NORMAL"])
        self.assertFalse(result["historical_likelihood_claimed"])
        self.assertFalse(result["performance_claim_allowed"])
        self.assertTrue(result["live_orders_forbidden"])

    def test_suite_is_deterministic(self) -> None:
        payload = load_stress_suite(SUITE)
        self.assertEqual(
            run_stress_suite(payload, suite_path=SUITE),
            run_stress_suite(payload, suite_path=SUITE),
        )

    def test_duplicate_ids_fail_closed(self) -> None:
        payload = json.loads(SUITE.read_text(encoding="utf-8"))
        payload["scenarios"][1]["scenario_id"] = payload["scenarios"][0]["scenario_id"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "suite.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unique"):
                load_stress_suite(path)

    def test_impossible_return_fails_closed(self) -> None:
        payload = copy.deepcopy(json.loads(SUITE.read_text(encoding="utf-8")))
        payload["scenarios"][0]["returns_bps"][0] = -10_000
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "suite.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "greater than"):
                load_stress_suite(path)
