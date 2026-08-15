import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from father_quant_lab.data import load_bars_csv, validate_bars
from father_quant_lab.models import Bar


def bar(day: int, close: float = 100.0) -> Bar:
    return Bar(
        timestamp=datetime(2026, 1, day, tzinfo=UTC),
        instrument="EUR/USD",
        open=close,
        high=close,
        low=close,
        close=close,
    )


class DataContractTests(unittest.TestCase):
    def test_requires_timezone_aware_timestamp(self) -> None:
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            Bar(datetime(2026, 1, 1), "EUR/USD", 1.0, 1.1, 0.9, 1.0)

    def test_rejects_duplicate_or_unordered_timestamps(self) -> None:
        with self.assertRaisesRegex(ValueError, "strictly ordered"):
            validate_bars([bar(2), bar(1)])

    def test_rejects_mixed_instruments(self) -> None:
        other = Bar(datetime(2026, 1, 2, tzinfo=UTC), "USD/JPY", 100, 100, 100, 100)
        with self.assertRaisesRegex(ValueError, "exactly one instrument"):
            validate_bars([bar(1), other])

    def test_csv_schema_is_strict(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.csv"
            path.write_text("timestamp,instrument,close\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "columns must be exactly"):
                load_bars_csv(path)
