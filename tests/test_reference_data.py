import json
import tempfile
import unittest
from datetime import UTC, date, datetime
from pathlib import Path

from father_quant_lab.data import load_bars_csv
from father_quant_lab.reference_data import (
    ECB_SERIES_KEY,
    build_ecb_url,
    build_reference_passport,
    parse_ecb_csv,
    write_passport,
    write_reference_csv,
)


FIXTURE = Path("tests/fixtures/ecb_eurusd_reference.csv")


class EcbReferenceDataTests(unittest.TestCase):
    def test_url_is_fixed_to_official_series_and_bounded_dates(self) -> None:
        url = build_ecb_url(date(2026, 1, 1), date(2026, 1, 31))
        self.assertIn("/EXR/D.USD.EUR.SP00.A?", url)
        self.assertIn("startPeriod=2026-01-01", url)
        self.assertIn("endPeriod=2026-01-31", url)
        with self.assertRaisesRegex(ValueError, "start date"):
            build_ecb_url(date(2026, 2, 1), date(2026, 1, 1))

    def test_parse_preserves_reference_semantics(self) -> None:
        observations = parse_ecb_csv(FIXTURE.read_bytes())
        self.assertEqual(len(observations), 2)
        self.assertEqual(observations[0].instrument, "EUR/USD")
        self.assertEqual(observations[0].source_series, ECB_SERIES_KEY)
        self.assertEqual(observations[0].observation_type, "ECB_REFERENCE_RATE")

    def test_rejects_wrong_series_and_unordered_dates(self) -> None:
        wrong = FIXTURE.read_text(encoding="utf-8").replace(
            ECB_SERIES_KEY, "EXR.D.JPY.EUR.SP00.A", 1
        )
        with self.assertRaisesRegex(ValueError, "series key"):
            parse_ecb_csv(wrong.encode())
        lines = FIXTURE.read_text(encoding="utf-8").splitlines()
        unordered = "\n".join([lines[0], lines[2], lines[1]]) + "\n"
        with self.assertRaisesRegex(ValueError, "unique and ordered"):
            parse_ecb_csv(unordered.encode())

    def test_rejects_incomplete_schema_and_wrong_frequency(self) -> None:
        incomplete = b"TIME_PERIOD,OBS_VALUE\n2026-01-02,1.1721\n"
        with self.assertRaisesRegex(ValueError, "missing required"):
            parse_ecb_csv(incomplete)
        wrong_frequency = FIXTURE.read_text(encoding="utf-8").replace(
            f"{ECB_SERIES_KEY},D,", f"{ECB_SERIES_KEY},M,", 1
        )
        with self.assertRaisesRegex(ValueError, "frequency"):
            parse_ecb_csv(wrong_frequency.encode())

    def test_passport_blocks_reference_rate_from_backtest(self) -> None:
        observations = parse_ecb_csv(FIXTURE.read_bytes())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw = root / "raw.csv"
            raw.write_bytes(FIXTURE.read_bytes())
            canonical = write_reference_csv(root / "reference.csv", observations)
            passport = build_reference_passport(
                source_url=build_ecb_url(date(2026, 1, 1), date(2026, 1, 31)),
                raw_path=raw,
                canonical_path=canonical,
                observations=observations,
                retrieved_at=datetime(2026, 2, 1, tzinfo=UTC),
            )
            saved = write_passport(root / "passport.json", passport)
            loaded = json.loads(saved.read_text(encoding="utf-8"))
            mandatory = {
                "artifact_id",
                "artifact_type",
                "purpose",
                "owner_role",
                "source_basis",
                "inputs",
                "outputs",
                "relations",
                "version",
                "sha256",
                "status",
                "limitations",
                "verification",
                "decision",
                "lessons",
            }
            self.assertTrue(mandatory.issubset(loaded))
            self.assertFalse(loaded["safety"]["backtest_eligible"])
            with self.assertRaisesRegex(ValueError, "columns must be exactly"):
                load_bars_csv(canonical)


if __name__ == "__main__":
    unittest.main()
