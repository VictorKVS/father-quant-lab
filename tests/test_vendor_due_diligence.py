import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from father_quant_lab.cli import main
from father_quant_lab.vendor_due_diligence import (
    REQUIRED_QUESTIONNAIRE_FIELDS,
    evaluate_dossier,
    evaluate_dossiers,
    load_dossiers,
)


DOSSIERS = Path("configs/data-providers/vendor_dossiers.json")
EVIDENCE = Path("evidence/runs/RUN-S2-GATE-003-20260816")


def verified_dossier() -> dict[str, object]:
    answers = {
        field: {"status": "VERIFIED", "evidence": [f"https://example.test/{field}"]}
        for field in REQUIRED_QUESTIONNAIRE_FIELDS
    }
    return {
        "provider_id": "SYNTHETIC_VENDOR",
        "public_evidence": ["https://example.test/product"],
        "answers": answers,
        "sample": {
            "status": "RECEIVED",
            "format": "CSV",
            "schema": {"timestamp": "UTC nanoseconds", "bid": "decimal", "ask": "decimal"},
            "sha256": hashlib.sha256(b"synthetic sample").hexdigest(),
            "size_bytes": 16,
            "retrieval_url": "https://example.test/sample.csv",
            "retrieved_at": "2026-08-16T07:00:00Z",
        },
    }


class VendorDueDiligenceTests(unittest.TestCase):
    def test_current_candidates_are_query_ready_but_sample_blocked(self) -> None:
        result = evaluate_dossiers(load_dossiers(DOSSIERS))
        self.assertEqual(result["overall_status"], "BLOCKED")
        self.assertEqual(result["sample_ready_providers"], [])
        self.assertEqual(
            {item["status"] for item in result["decisions"]}, {"READY_FOR_VENDOR_QUERY"}
        )
        self.assertFalse(result["purchase_authorized"])
        self.assertFalse(result["credential_use_authorized"])
        self.assertTrue(result["live_orders_forbidden"])

    def test_complete_synthetic_dossier_only_allows_offline_review(self) -> None:
        decision = evaluate_dossier(verified_dossier())
        self.assertEqual(decision.status, "ELIGIBLE_FOR_OFFLINE_SAMPLE_REVIEW")
        self.assertEqual(decision.blockers, ())
        self.assertFalse(decision.to_dict()["trading_data_admitted"])
        self.assertFalse(decision.to_dict()["purchase_authorized"])

    def test_missing_one_answer_fails_closed(self) -> None:
        dossier = verified_dossier()
        del dossier["answers"]["timestamp_semantics"]
        decision = evaluate_dossier(dossier)
        self.assertIn("VENDOR_ANSWERS_INCOMPLETE", decision.blockers)
        self.assertIn("timestamp_semantics", decision.pending_questions)

    def test_malformed_sample_hash_is_rejected(self) -> None:
        dossier = verified_dossier()
        dossier["sample"]["sha256"] = "not-a-sha"
        self.assertIn("IMMUTABLE_SAMPLE_NOT_VERIFIED", evaluate_dossier(dossier).blockers)

    def test_unverifiable_answer_evidence_fails_closed(self) -> None:
        dossier = verified_dossier()
        dossier["answers"]["legal_entity"]["evidence"] = ["sales-brochure.pdf"]
        decision = evaluate_dossier(dossier)
        self.assertIn("legal_entity", decision.pending_questions)

    def test_missing_public_evidence_is_blocked_not_query_ready(self) -> None:
        dossier = verified_dossier()
        dossier["public_evidence"] = []
        decision = evaluate_dossier(dossier)
        self.assertEqual(decision.status, "BLOCKED")
        self.assertIn("PUBLIC_EVIDENCE_NOT_ADMITTED", decision.blockers)

    def test_duplicate_dossier_ids_are_rejected(self) -> None:
        dossier = verified_dossier()
        payload = {"schema_version": "1.0.0", "dossiers": [dossier, dossier]}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dossiers.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unique"):
                load_dossiers(path)

    def test_cli_writes_machine_readable_gate_result(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "result.json"
            exit_code = main(
                ["evaluate-vendor-dossiers", "--dossiers", str(DOSSIERS), "--output", str(output)]
            )
            result = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(exit_code, 0)
        self.assertEqual(result["gate_id"], "FQL-S2-GATE-003")
        self.assertFalse(result["purchase_authorized"])

    def test_passport_tracks_result_and_negative_boundary(self) -> None:
        passport = json.loads((EVIDENCE / "passport.json").read_text(encoding="utf-8"))
        result_hash = hashlib.sha256((EVIDENCE / "result.json").read_bytes()).hexdigest()
        self.assertEqual(passport["sha256"], result_hash)
        self.assertEqual(passport["provenance"]["sample_ready_count"], 0)
        self.assertFalse(passport["safety"]["purchase_authorized"])


if __name__ == "__main__":
    unittest.main()
