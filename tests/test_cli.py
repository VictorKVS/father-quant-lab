import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from father_quant_lab.cli import main


class CliTests(unittest.TestCase):
    def test_run_controls_records_reproducibility_and_safety_config(self) -> None:
        fixture = Path("data/samples/eurusd_daily_sample.csv")
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "controls.json"
            exit_code = main(
                [
                    "run-controls",
                    "--data",
                    str(fixture),
                    "--output",
                    str(output),
                    "--seed",
                    "17",
                ]
            )
            report = json.loads(output.read_text(encoding="utf-8"))

        expected_hash = hashlib.sha256(fixture.read_bytes()).hexdigest()
        self.assertEqual(exit_code, 0)
        self.assertEqual(report["mode"], "backtest_only")
        self.assertTrue(report["live_orders_forbidden"])
        self.assertEqual(report["run_config"]["dataset"]["sha256"], expected_hash)
        self.assertEqual(report["run_config"]["dataset"]["classification"], "MODELLED")
        self.assertEqual(report["run_config"]["seed"], 17)
        self.assertFalse(report["run_config"]["risk"]["short_allowed"])
        self.assertFalse(report["run_config"]["risk"]["leverage_allowed"])
        self.assertEqual(len(report["results"]), 4)


if __name__ == "__main__":
    unittest.main()
