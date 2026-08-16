"""Deterministic admission gate for external market-data providers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

TRADABLE_SEMANTICS = {"BID_ASK", "TRADES", "OHLC_BID", "OHLC_ASK"}


@dataclass(frozen=True, slots=True)
class ProviderDecision:
    provider_id: str
    status: str
    blockers: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "provider_id": self.provider_id,
            "status": self.status,
            "blockers": list(self.blockers),
        }


def load_registry(path: str | Path) -> dict[str, Any]:
    registry = json.loads(Path(path).read_text(encoding="utf-8"))
    if registry.get("schema_version") != "1.0.0":
        raise ValueError("unsupported provider registry schema")
    providers = registry.get("providers")
    if not isinstance(providers, list) or not providers:
        raise ValueError("provider registry must contain candidates")
    identifiers = [provider.get("provider_id") for provider in providers]
    if len(identifiers) != len(set(identifiers)) or any(not item for item in identifiers):
        raise ValueError("provider IDs must be non-empty and unique")
    return registry


def evaluate_provider(
    provider: dict[str, Any], *, required_start: date = date(1992, 1, 1)
) -> ProviderDecision:
    blockers: list[str] = []
    evidence = provider.get("evidence", [])
    if not evidence or any(not str(item).startswith("https://") for item in evidence):
        blockers.append("EVIDENCE_NOT_ADMITTED")

    if provider.get("license_status") != "VERIFIED":
        blockers.append("LICENSE_NOT_VERIFIED")
    if provider.get("storage_allowed") is not True:
        blockers.append("STORAGE_RIGHT_NOT_VERIFIED")

    semantics = set(provider.get("price_semantics", []))
    if not semantics.intersection(TRADABLE_SEMANTICS):
        blockers.append("NOT_TRADABLE_PRICE_SEMANTICS")

    history_start = provider.get("history_start")
    if not history_start:
        blockers.append("HISTORY_START_NOT_VERIFIED")
    elif date.fromisoformat(history_start) > required_start:
        blockers.append("INSUFFICIENT_HISTORY")
    if provider.get("coverage_status") != "VERIFIED":
        blockers.append("PAIR_COVERAGE_NOT_VERIFIED")
    if provider.get("timestamp_status") != "VERIFIED":
        blockers.append("TIMESTAMP_SEMANTICS_NOT_VERIFIED")
    if provider.get("revision_status") != "VERIFIED":
        blockers.append("REVISION_POLICY_NOT_VERIFIED")

    status = "ELIGIBLE_FOR_PILOT" if not blockers else "BLOCKED"
    return ProviderDecision(provider["provider_id"], status, tuple(blockers))


def evaluate_registry(
    registry: dict[str, Any], *, required_start: date = date(1992, 1, 1)
) -> dict[str, object]:
    decisions = [
        evaluate_provider(provider, required_start=required_start)
        for provider in registry["providers"]
    ]
    eligible = [item.provider_id for item in decisions if item.status == "ELIGIBLE_FOR_PILOT"]
    return {
        "schema_version": "1.0.0",
        "gate_id": "FQL-S2-GATE-002",
        "required_start": required_start.isoformat(),
        "live_orders_forbidden": True,
        "eligible_providers": eligible,
        "overall_status": "PASS" if eligible else "BLOCKED",
        "decisions": [item.to_dict() for item in decisions],
        "decision": (
            "start a bounded ingestion pilot"
            if eligible
            else "do not ingest a tradable dataset until at least one provider clears all gates"
        ),
    }
