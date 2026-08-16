import hashlib
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from father_quant_lab.provider_gate import evaluate_provider, evaluate_registry, load_registry


REGISTRY = Path("configs/data-providers/fx_provider_registry.json")
EVIDENCE = Path("evidence/runs/RUN-S2-GATE-002-20260816")


def eligible_provider() -> dict[str, object]:
    return {
        "provider_id": "TEST",
        "license_status": "VERIFIED",
        "storage_allowed": True,
        "price_semantics": ["BID_ASK"],
        "history_start": "1990-01-01",
        "coverage_status": "VERIFIED",
        "timestamp_status": "VERIFIED",
        "revision_status": "VERIFIED",
        "evidence": ["https://example.test/primary"],
    }


class ProviderGateTests(unittest.TestCase):
    def test_current_registry_is_valid_and_blocks_all_candidates(self) -> None:
        registry = load_registry(REGISTRY)
        result = evaluate_registry(registry)
        self.assertEqual(result["overall_status"], "BLOCKED")
        self.assertEqual(result["eligible_providers"], [])
        self.assertTrue(result["live_orders_forbidden"])
        self.assertEqual(len(result["decisions"]), 6)

    def test_reference_rate_cannot_pass_tradable_gate(self) -> None:
        provider = eligible_provider()
        provider["price_semantics"] = ["REFERENCE_RATE"]
        decision = evaluate_provider(provider)
        self.assertIn("NOT_TRADABLE_PRICE_SEMANTICS", decision.blockers)

    def test_history_after_1992_is_rejected(self) -> None:
        provider = eligible_provider()
        provider["history_start"] = "2005-01-01"
        decision = evaluate_provider(provider, required_start=date(1992, 1, 1))
        self.assertIn("INSUFFICIENT_HISTORY", decision.blockers)

    def test_only_fully_verified_candidate_can_enter_pilot(self) -> None:
        decision = evaluate_provider(eligible_provider())
        self.assertEqual(decision.status, "ELIGIBLE_FOR_PILOT")
        self.assertEqual(decision.blockers, ())

    def test_duplicate_provider_ids_are_rejected(self) -> None:
        provider = eligible_provider()
        payload = {"schema_version": "1.0.0", "providers": [provider, provider]}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "registry.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unique"):
                load_registry(path)

    def test_gate_passport_tracks_immutable_result(self) -> None:
        passport = json.loads((EVIDENCE / "passport.json").read_text(encoding="utf-8"))
        result_hash = hashlib.sha256((EVIDENCE / "result.json").read_bytes()).hexdigest()
        self.assertEqual(passport["sha256"], result_hash)
        self.assertEqual(passport["provenance"]["eligible_count"], 0)
        self.assertFalse(passport["safety"]["purchase_authorized"])


if __name__ == "__main__":
    unittest.main()
