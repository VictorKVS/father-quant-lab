import json
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from father_quant_lab.engine import BacktestEngine, ExecutionCostModel
from father_quant_lab.models import Bar
from father_quant_lab.reporting import league_report, write_report
from father_quant_lab.strategies import NoTradeStrategy


class ReportingTests(unittest.TestCase):
    def test_report_is_json_serializable_and_blocks_live_orders(self) -> None:
        bars = [
            Bar(datetime(2026, 1, 1, tzinfo=UTC), "EUR/USD", 1, 1, 1, 1),
            Bar(datetime(2026, 1, 2, tzinfo=UTC), "EUR/USD", 1, 1, 1, 1),
        ]
        result = BacktestEngine(
            costs=ExecutionCostModel(spread_bps=0, slippage_bps=0, commission_bps=0)
        ).run(bars, NoTradeStrategy())
        report = league_report([result], run_config={"dataset": {"sha256": "fixture"}})
        serialized = json.dumps(report)
        self.assertIn("BOT-CTRL-000", serialized)
        self.assertTrue(report["live_orders_forbidden"])
        self.assertEqual(report["run_config"]["dataset"]["sha256"], "fixture")

        with tempfile.TemporaryDirectory() as directory:
            destination = write_report(Path(directory) / "report.json", report)
            loaded = json.loads(destination.read_text(encoding="utf-8"))
            self.assertEqual(loaded["schema_version"], "1.0.0")
