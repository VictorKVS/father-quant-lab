"""Official reference-rate ingestion kept separate from tradable OHLC bars."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ECB_SERIES_KEY = "EXR.D.USD.EUR.SP00.A"
ECB_API_ROOT = "https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A"


@dataclass(frozen=True, slots=True)
class ReferenceObservation:
    """A published reference value; it is not a tradable market bar."""

    observed_on: date
    instrument: str
    value: float
    source_series: str = ECB_SERIES_KEY
    observation_type: str = "ECB_REFERENCE_RATE"

    def __post_init__(self) -> None:
        if self.value <= 0:
            raise ValueError("reference value must be positive")
        if self.instrument != "EUR/USD":
            raise ValueError("ECB adapter supports exactly EUR/USD")


def build_ecb_url(start: date, end: date) -> str:
    if start > end:
        raise ValueError("start date must not exceed end date")
    query = urlencode(
        {
            "startPeriod": start.isoformat(),
            "endPeriod": end.isoformat(),
            "format": "csvdata",
        }
    )
    return f"{ECB_API_ROOT}?{query}"


def fetch_ecb_csv(url: str, *, timeout: float = 30.0) -> bytes:
    """Download raw official bytes. Network use is isolated in this function."""
    request = Request(url, headers={"User-Agent": "FATHER-Quant-Lab/0.1"})
    with urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed HTTPS origin
        if response.geturl().split("?", 1)[0] != ECB_API_ROOT:
            raise ValueError("unexpected ECB redirect target")
        return response.read()


def parse_ecb_csv(raw: bytes) -> tuple[ReferenceObservation, ...]:
    """Parse and validate the ECB CSVDATA representation."""
    text = raw.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    required = {
        "KEY",
        "FREQ",
        "CURRENCY",
        "CURRENCY_DENOM",
        "EXR_TYPE",
        "EXR_SUFFIX",
        "TIME_PERIOD",
        "OBS_VALUE",
    }
    if not reader.fieldnames or not required.issubset(reader.fieldnames):
        raise ValueError("ECB CSV is missing required series or observation columns")

    observations: list[ReferenceObservation] = []
    for row in reader:
        if row["KEY"] != ECB_SERIES_KEY:
            raise ValueError("unexpected ECB series key")
        if row["FREQ"] != "D":
            raise ValueError("unexpected ECB frequency")
        if row["CURRENCY"] != "USD":
            raise ValueError("unexpected ECB currency")
        if row["CURRENCY_DENOM"] != "EUR":
            raise ValueError("unexpected ECB denominator")
        if row["EXR_TYPE"] != "SP00" or row["EXR_SUFFIX"] != "A":
            raise ValueError("unexpected ECB exchange-rate semantics")
        observations.append(
            ReferenceObservation(
                observed_on=date.fromisoformat(row["TIME_PERIOD"]),
                instrument="EUR/USD",
                value=float(row["OBS_VALUE"]),
            )
        )

    if not observations:
        raise ValueError("ECB response contains no observations")
    dates = [item.observed_on for item in observations]
    if dates != sorted(set(dates)):
        raise ValueError("ECB observations must be unique and ordered")
    return tuple(observations)


def write_reference_csv(
    path: str | Path, observations: tuple[ReferenceObservation, ...]
) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(
            ["date", "instrument", "value", "observation_type", "source_series"]
        )
        for item in observations:
            writer.writerow(
                [
                    item.observed_on.isoformat(),
                    item.instrument,
                    item.value,
                    item.observation_type,
                    item.source_series,
                ]
            )
    return destination


def build_reference_passport(
    *,
    source_url: str,
    raw_path: str | Path,
    canonical_path: str | Path,
    observations: tuple[ReferenceObservation, ...],
    retrieved_at: datetime,
) -> dict[str, object]:
    if retrieved_at.tzinfo is None or retrieved_at.utcoffset() is None:
        raise ValueError("retrieved_at must be timezone-aware")
    raw = Path(raw_path)
    canonical = Path(canonical_path)
    raw_hash = hashlib.sha256(raw.read_bytes()).hexdigest()
    canonical_hash = hashlib.sha256(canonical.read_bytes()).hexdigest()
    return {
        "schema_version": "1.0.0",
        "artifact_id": f"DATA-ECB-EURUSD-{observations[0].observed_on}-{observations[-1].observed_on}",
        "artifact_type": "reference_rate_dataset",
        "purpose": "official macro reference and provenance validation",
        "owner_role": "DATA_ENGINEER",
        "source_basis": [
            "ECB Data Portal",
            ECB_SERIES_KEY,
            source_url,
        ],
        "inputs": [raw.as_posix()],
        "outputs": [canonical.as_posix()],
        "provenance": {
            "publisher": "European Central Bank",
            "retrieved_at": retrieved_at.astimezone(UTC).isoformat(),
            "raw_path": raw.as_posix(),
            "raw_sha256": raw_hash,
            "canonical_path": canonical.as_posix(),
            "canonical_sha256": canonical_hash,
            "observation_count": len(observations),
            "first_observation": observations[0].observed_on.isoformat(),
            "last_observation": observations[-1].observed_on.isoformat(),
        },
        "relations": ["FQL-S2-FR-001", "ADR-0004"],
        "version": "1.0.0",
        "sha256": canonical_hash,
        "status": "ingested_unreviewed",
        "limitations": [
            "reference rate is not an executable bid, ask, trade or OHLC bar",
            "dataset is forbidden as direct input to BacktestEngine",
            "publication timing must be modelled before event studies",
        ],
        "verification": ["tests/test_reference_data.py"],
        "decision": "admit for provenance and macro context only",
        "lessons": ["official does not mean tradable", "observation time differs from availability time"],
        "safety": {"backtest_eligible": False, "live_orders_forbidden": True},
    }


def write_passport(path: str | Path, passport: dict[str, object]) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(passport, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return destination
