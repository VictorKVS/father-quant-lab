"""Market-data loading with strict validation and no silent repair."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from .models import Bar


def _parse_timestamp(value: str) -> datetime:
    normalized = value.strip().replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def validate_bars(bars: list[Bar]) -> tuple[Bar, ...]:
    if len(bars) < 2:
        raise ValueError("at least two bars are required")
    instruments = {bar.instrument for bar in bars}
    if len(instruments) != 1:
        raise ValueError("one backtest run must contain exactly one instrument")
    for previous, current in zip(bars, bars[1:]):
        if current.timestamp <= previous.timestamp:
            raise ValueError("bars must be strictly ordered with no duplicate timestamps")
    return tuple(bars)


def load_bars_csv(path: str | Path) -> tuple[Bar, ...]:
    rows: list[Bar] = []
    with Path(path).open("r", encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source)
        expected = {"timestamp", "instrument", "open", "high", "low", "close"}
        if set(reader.fieldnames or ()) != expected:
            raise ValueError(f"CSV columns must be exactly {sorted(expected)}")
        for line_number, row in enumerate(reader, start=2):
            try:
                rows.append(
                    Bar(
                        timestamp=_parse_timestamp(row["timestamp"]),
                        instrument=row["instrument"],
                        open=float(row["open"]),
                        high=float(row["high"]),
                        low=float(row["low"]),
                        close=float(row["close"]),
                    )
                )
            except (TypeError, ValueError) as error:
                raise ValueError(f"invalid market data at CSV line {line_number}: {error}") from error
    return validate_bars(rows)
