from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class AbilityDictionaryTests(unittest.TestCase):
    def test_dictionary_generator_writes_expected_outputs(self) -> None:
        json_path = ROOT / "data" / "ability_dictionary.json"
        md_path = ROOT / "data" / "ability_dictionary.md"
        script = ROOT / "tools" / "render_ability_dictionary.py"

        result = subprocess.run(
            [sys.executable, str(script)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )

        self.assertEqual(result.returncode, 0)
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema"], "ability_dictionary.v1")
        self.assertEqual(payload["comparison_symbols"]["GE"], ">=")
        self.assertEqual(payload["comparison_codes"][">="], "GE")
        draw = next(item for item in payload["opcodes"] if item["name"] == "DRAW")
        self.assertEqual(draw["template"], "draw {value}")
        count_stage = next(item for item in payload["opcodes"] if item["name"] == "COUNT_STAGE")
        self.assertIn("count(stage)", count_stage["template"])
        self.assertTrue(md_path.exists())


if __name__ == "__main__":
    unittest.main()
