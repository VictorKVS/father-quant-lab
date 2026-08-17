import copy
import json
import tempfile
import unittest
from pathlib import Path

from father_quant_lab.regime_crosscheck import crosscheck_regime_result

SUITE = Path("configs/stress/regime-branch-suite.json")
PRIMARY = Path("evidence/runs/RUN-M0-S6-STRESS-20260817/result.json")


class RegimeCrosscheckTests(unittest.TestCase):
    def test_independent_decimal_oracle_matches_all_registered_labels(self) -> None:
        result = crosscheck_regime_result(suite_path=SUITE, primary_result_path=PRIMARY)
        self.assertEqual(result["status"], "PASS_INDEPENDENT_LABEL_EQUIVALENCE")
        self.assertEqual(result["scenario_count"], 4)
        self.assertEqual(result["label_count"], 28)
        self.assertEqual(result["field_comparison_count"], 196)
        self.assertEqual(result["mismatch_count"], 0)
        self.assertFalse(result["oracle"]["imports_primary_classifier"])
        self.assertTrue(result["live_orders_forbidden"])

    def test_crosscheck_is_deterministic(self) -> None:
        self.assertEqual(
            crosscheck_regime_result(suite_path=SUITE, primary_result_path=PRIMARY),
            crosscheck_regime_result(suite_path=SUITE, primary_result_path=PRIMARY),
        )

    def test_tampered_classification_is_reported_as_blocked(self) -> None:
        primary = json.loads(PRIMARY.read_text(encoding="utf-8"))
        primary["scenarios"][0]["regime_report"]["labels"][0]["trend"] = "UP"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "primary.json"
            path.write_text(json.dumps(primary), encoding="utf-8")
            result = crosscheck_regime_result(suite_path=SUITE, primary_result_path=path)
        self.assertEqual(result["status"], "BLOCKED_CROSSCHECK_MISMATCH")
        self.assertEqual(result["mismatch_count"], 1)
        self.assertEqual(result["mismatches"][0]["field"], "trend")

    def test_tampered_numeric_metric_is_reported_as_blocked(self) -> None:
        primary = json.loads(PRIMARY.read_text(encoding="utf-8"))
        primary["scenarios"][0]["regime_report"]["labels"][0]["rms_log_return"] += 0.01
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "primary.json"
            path.write_text(json.dumps(primary), encoding="utf-8")
            result = crosscheck_regime_result(suite_path=SUITE, primary_result_path=path)
        self.assertEqual(result["status"], "BLOCKED_CROSSCHECK_MISMATCH")
        self.assertEqual(result["mismatches"][0]["field"], "rms_log_return")

    def test_wrong_suite_identity_fails_closed(self) -> None:
        primary = copy.deepcopy(json.loads(PRIMARY.read_text(encoding="utf-8")))
        primary["suite_id"] = "OTHER"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "primary.json"
            path.write_text(json.dumps(primary), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "suite ID"):
                crosscheck_regime_result(suite_path=SUITE, primary_result_path=path)
