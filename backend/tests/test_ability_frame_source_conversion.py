import os
import sys
import tempfile
import unittest
from pathlib import Path

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.append(project_root)

from tools.ability_frame_source_converter import (
    canonical_to_compact_payload,
    comparison_code_to_symbol,
    comparison_symbol_to_code,
    compact_to_canonical_payload,
    load_json,
)


ROOT = Path(project_root)
SOURCE_PATH = ROOT / "data" / "ability_frame_source.json"


class AbilityFrameSourceConversionTests(unittest.TestCase):
    def test_compact_round_trip_preserves_canonical_payload(self) -> None:
        original = load_json(SOURCE_PATH)
        compact = canonical_to_compact_payload(original)
        restored = compact_to_canonical_payload(compact)

        self.assertEqual(restored, original)

    def test_compact_file_can_be_written_and_reexpanded(self) -> None:
        original = load_json(SOURCE_PATH)
        compact = canonical_to_compact_payload(original)
        restored = compact_to_canonical_payload(compact)

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            compact_path = tmp_path / "ability_frame_source.compact.json"
            canonical_path = tmp_path / "ability_frame_source.roundtrip.json"

            from tools.ability_frame_source_converter import dump_json

            dump_json(compact_path, compact)
            dump_json(canonical_path, restored)

            self.assertTrue(compact_path.exists())
            self.assertTrue(canonical_path.exists())
            self.assertEqual(load_json(canonical_path), original)

    def test_comparison_codes_round_trip_to_symbols(self) -> None:
        cases = {
            "GE": ">=",
            "GT": ">",
            "LE": "<=",
            "LT": "<",
            "EQ": "==",
            "NE": "!=",
        }

        for code, symbol in cases.items():
            self.assertEqual(comparison_code_to_symbol(code), symbol)
            self.assertEqual(comparison_symbol_to_code(symbol), code)


if __name__ == "__main__":
    unittest.main()
