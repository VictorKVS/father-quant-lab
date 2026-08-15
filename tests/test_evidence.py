import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from father_quant_lab.evidence import sha256_file, write_json


class EvidenceTests(unittest.TestCase):
    def test_hash_and_json_passport_are_stable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifact = root / "artifact.txt"
            artifact.write_text("evidence\n", encoding="utf-8")
            expected = hashlib.sha256(b"evidence\n").hexdigest()
            self.assertEqual(sha256_file(artifact), expected)

            passport = write_json(root / "passport.json", {"id": "ART-001"})
            self.assertEqual(json.loads(passport.read_text(encoding="utf-8"))["id"], "ART-001")


if __name__ == "__main__":
    unittest.main()
