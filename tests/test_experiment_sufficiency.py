import copy
import json
import tempfile
import unittest
from pathlib import Path

from father_quant_lab.experiment_sufficiency import (
    evaluate_sufficiency,
    load_plan_result,
    load_sufficiency_criteria,
)

RESULT_PATH = Path("evidence/runs/RUN-M0-S4-PLAN-20260816/result.json")
CRITERIA_PATH = Path("configs/evaluation/m0-mechanical-sufficiency.json")


class ExperimentSufficiencyTests(unittest.TestCase):
    def test_current_modelled_plan_is_blocked(self) -> None:
        result = evaluate_sufficiency(
            load_plan_result(RESULT_PATH),
            load_sufficiency_criteria(CRITERIA_PATH),
            result_path=RESULT_PATH,
            criteria_path=CRITERIA_PATH,
        )
        self.assertEqual(result["status"], "BLOCKED_INSUFFICIENT_BARS")
        self.assertEqual(result["strategy_lookback_bars"], 5)
        self.assertEqual([item["deficit_bars"] for item in result["decisions"]], [21, 21, 21])
        self.assertFalse(result["statistical_sufficiency_proved"])
        self.assertFalse(result["performance_claim_allowed"])
        self.assertTrue(result["live_orders_forbidden"])

    def test_positive_mechanical_path_does_not_claim_statistics(self) -> None:
        plan = load_plan_result(RESULT_PATH)
        for split in plan["splits"]:
            split["bar_count"] = 25
        result = evaluate_sufficiency(
            plan,
            load_sufficiency_criteria(CRITERIA_PATH),
            result_path=RESULT_PATH,
            criteria_path=CRITERIA_PATH,
        )
        self.assertEqual(result["status"], "PASS_MECHANICAL_MINIMUM")
        self.assertFalse(result["statistical_sufficiency_proved"])
        self.assertFalse(result["paper_trading_allowed"])

    def test_missing_strategy_window_fails_closed(self) -> None:
        plan = load_plan_result(RESULT_PATH)
        plan["strategy"]["parameters"] = {"position_mode": "long_flat"}
        with self.assertRaisesRegex(ValueError, "window"):
            evaluate_sufficiency(
                plan,
                load_sufficiency_criteria(CRITERIA_PATH),
                result_path=RESULT_PATH,
                criteria_path=CRITERIA_PATH,
            )

    def test_unregistered_criteria_are_rejected(self) -> None:
        payload = json.loads(CRITERIA_PATH.read_text(encoding="utf-8"))
        payload["status"] = "DRAFT"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "criteria.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "PRE_REGISTERED"):
                load_sufficiency_criteria(path)

    def test_boolean_bar_count_is_rejected(self) -> None:
        plan = copy.deepcopy(load_plan_result(RESULT_PATH))
        plan["splits"][0]["bar_count"] = True
        with self.assertRaisesRegex(ValueError, "bar_count"):
            evaluate_sufficiency(
                plan,
                load_sufficiency_criteria(CRITERIA_PATH),
                result_path=RESULT_PATH,
                criteria_path=CRITERIA_PATH,
            )
