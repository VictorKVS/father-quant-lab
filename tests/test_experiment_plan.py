import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from father_quant_lab.data import load_bars_csv
from father_quant_lab.experiment_plan import evaluate_experiment_plan, load_experiment_plan

DATA = Path("data/samples/eurusd_daily_sample.csv")
PLAN = Path("configs/experiments/BOT-RULE-101-modelled-preregistered.json")


class ExperimentPlanTests(unittest.TestCase):
    def load(self) -> dict[str, object]:
        return load_experiment_plan(PLAN)

    def write_and_load(self, payload: dict[str, object]) -> dict[str, object]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plan.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            return load_experiment_plan(path)

    def test_registered_plan_matches_dataset_and_keeps_claims_closed(self) -> None:
        result = evaluate_experiment_plan(self.load(), dataset_path=DATA, bars=load_bars_csv(DATA))
        self.assertEqual(result["status"], "VALID_MODELLED_ONLY")
        self.assertEqual([split["bar_count"] for split in result["splits"]], [4, 4, 4])
        self.assertFalse(result["performance_claim_allowed"])
        self.assertFalse(result["paper_trading_allowed"])
        self.assertTrue(result["live_orders_forbidden"])

    def test_dataset_hash_mismatch_fails_closed(self) -> None:
        plan = self.load()
        plan["dataset"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            evaluate_experiment_plan(plan, dataset_path=DATA, bars=load_bars_csv(DATA))

    def test_unsealed_plan_is_rejected(self) -> None:
        payload = json.loads(PLAN.read_text(encoding="utf-8"))
        payload["registration_status"] = "DRAFT"
        with self.assertRaisesRegex(ValueError, "SEALED"):
            self.write_and_load(payload)

    def test_wrong_split_order_is_rejected(self) -> None:
        payload = json.loads(PLAN.read_text(encoding="utf-8"))
        payload["splits"][1]["name"] = "OUT_OF_SAMPLE"
        with self.assertRaisesRegex(ValueError, "TRAIN, VALIDATION"):
            self.write_and_load(payload)

    def test_malformed_split_fails_as_validation_error(self) -> None:
        payload = json.loads(PLAN.read_text(encoding="utf-8"))
        payload["splits"][1] = "not-an-object"
        with self.assertRaisesRegex(ValueError, "splits must be"):
            self.write_and_load(payload)

    def test_overlap_is_rejected(self) -> None:
        plan = self.load()
        plan["splits"][1]["start"] = plan["splits"][0]["end"]
        with self.assertRaisesRegex(ValueError, "overlap"):
            evaluate_experiment_plan(plan, dataset_path=DATA, bars=load_bars_csv(DATA))

    def test_registered_embargo_is_enforced_in_bar_space(self) -> None:
        plan = self.load()
        plan["embargo_bars"] = 1
        with self.assertRaisesRegex(ValueError, "embargo"):
            evaluate_experiment_plan(plan, dataset_path=DATA, bars=load_bars_csv(DATA))

    def test_future_change_does_not_change_registered_hash(self) -> None:
        original = hashlib.sha256(DATA.read_bytes()).hexdigest()
        payload = copy.deepcopy(self.load())
        self.assertEqual(payload["dataset"]["sha256"], original)
