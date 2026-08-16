"""Fail-closed review of vendor answers and bounded offline samples."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REQUIRED_QUESTIONNAIRE_FIELDS = (
    "legal_entity",
    "dataset_ids",
    "pair_coverage",
    "history_and_granularity",
    "price_semantics",
    "timestamp_semantics",
    "venue_and_composite_method",
    "revision_and_versioning",
    "storage_and_reproducibility_rights",
    "sample_delivery",
    "pricing_and_fees",
    "api_security_and_limits",
    "termination_and_deletion",
    "support_and_sla",
    "known_gaps_and_outages",
)


@dataclass(frozen=True, slots=True)
class DossierDecision:
    provider_id: str
    status: str
    blockers: tuple[str, ...]
    pending_questions: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "provider_id": self.provider_id,
            "status": self.status,
            "blockers": list(self.blockers),
            "pending_questions": list(self.pending_questions),
            "purchase_authorized": False,
            "credential_use_authorized": False,
            "trading_data_admitted": False,
        }


def load_dossiers(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != "1.0.0":
        raise ValueError("unsupported vendor dossier schema")
    dossiers = payload.get("dossiers")
    if not isinstance(dossiers, list) or not dossiers:
        raise ValueError("dossier file must contain candidates")
    identifiers = [dossier.get("provider_id") for dossier in dossiers]
    if any(not item for item in identifiers) or len(identifiers) != len(set(identifiers)):
        raise ValueError("provider IDs must be non-empty and unique")
    return payload


def _verified_answer(answer: object) -> bool:
    if not isinstance(answer, dict) or answer.get("status") != "VERIFIED":
        return False
    evidence = answer.get("evidence")
    return (
        isinstance(evidence, list)
        and bool(evidence)
        and all(str(item).startswith("https://") for item in evidence)
    )


def _valid_sample(sample: object) -> bool:
    if not isinstance(sample, dict):
        return False
    sha256 = sample.get("sha256")
    return (
        sample.get("status") == "RECEIVED"
        and isinstance(sha256, str)
        and len(sha256) == 64
        and all(character in "0123456789abcdef" for character in sha256)
        and sample.get("format") in {"CSV", "PARQUET", "JSONL"}
        and isinstance(sample.get("schema"), dict)
        and bool(sample["schema"])
        and sample.get("size_bytes", 0) > 0
        and str(sample.get("retrieval_url", "")).startswith("https://")
        and bool(sample.get("retrieved_at"))
    )


def evaluate_dossier(dossier: dict[str, Any]) -> DossierDecision:
    answers = dossier.get("answers")
    if not isinstance(answers, dict):
        answers = {}
    pending = tuple(
        field for field in REQUIRED_QUESTIONNAIRE_FIELDS if not _verified_answer(answers.get(field))
    )
    blockers: list[str] = []
    evidence = dossier.get("public_evidence", [])
    if not evidence or any(not str(item).startswith("https://") for item in evidence):
        blockers.append("PUBLIC_EVIDENCE_NOT_ADMITTED")
    if pending:
        blockers.append("VENDOR_ANSWERS_INCOMPLETE")
    if not _valid_sample(dossier.get("sample")):
        blockers.append("IMMUTABLE_SAMPLE_NOT_VERIFIED")

    if not blockers:
        status = "ELIGIBLE_FOR_OFFLINE_SAMPLE_REVIEW"
    elif evidence and set(blockers) <= {
        "VENDOR_ANSWERS_INCOMPLETE",
        "IMMUTABLE_SAMPLE_NOT_VERIFIED",
    }:
        status = "READY_FOR_VENDOR_QUERY"
    else:
        status = "BLOCKED"
    return DossierDecision(dossier["provider_id"], status, tuple(blockers), pending)


def evaluate_dossiers(payload: dict[str, Any]) -> dict[str, object]:
    decisions = [evaluate_dossier(dossier) for dossier in payload["dossiers"]]
    sample_ready = [
        decision.provider_id
        for decision in decisions
        if decision.status == "ELIGIBLE_FOR_OFFLINE_SAMPLE_REVIEW"
    ]
    return {
        "schema_version": "1.0.0",
        "gate_id": "FQL-S2-GATE-003",
        "questionnaire_sha256": hashlib.sha256(
            "\n".join(REQUIRED_QUESTIONNAIRE_FIELDS).encode("utf-8")
        ).hexdigest(),
        "sample_ready_providers": sample_ready,
        "overall_status": "PASS" if sample_ready else "BLOCKED",
        "purchase_authorized": False,
        "credential_use_authorized": False,
        "live_orders_forbidden": True,
        "decisions": [decision.to_dict() for decision in decisions],
        "decision": (
            "perform schema and quality checks on the bounded offline sample only"
            if sample_ready
            else "send the versioned questionnaire; do not buy, authenticate, or ingest data"
        ),
    }
