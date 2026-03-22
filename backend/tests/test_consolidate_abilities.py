import os
import sys
import unittest
from pathlib import Path

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.append(project_root)

from tools import bytecode_codec as codec

ROOT = Path(project_root)


class ConsolidateAbilitiesTests(unittest.TestCase):
    def test_groups_same_trigger_and_bytecode_together(self) -> None:
        metadata = codec.load_json(ROOT / "data" / "metadata.json")
        trigger_id = int(metadata["triggers"]["ON_LIVE_START"])
        opcode_id = int(metadata["opcodes"]["SELECT_MODE"])

        compiled_data = {
            "member_db": {
                "card_a": {
                    "card_no": "A-001",
                    "name": "Card A",
                    "abilities": [
                        {"trigger": trigger_id, "bytecode": [opcode_id, 1, 0, 0, 1], "pseudocode": "A"},
                        {"trigger": trigger_id, "bytecode": [opcode_id, 2, 0, 0, 1], "pseudocode": "B"},
                    ],
                },
                "card_b": {
                    "card_no": "A-002",
                    "name": "Card B",
                    "abilities": [
                        {"trigger": trigger_id, "bytecode": [opcode_id, 1, 0, 0, 1], "pseudocode": "A"},
                    ],
                },
                "card_c": {
                    "card_no": "A-003",
                    "name": "Card C",
                    "abilities": [
                        {"trigger": int(metadata["triggers"]["CONSTANT"]), "bytecode": [opcode_id, 1, 0, 0, 1]},
                    ],
                },
            }
        }

        payload = codec.build_sparse_ability_index(compiled_data, metadata)
        self.assertEqual(payload["summary"]["card_count"], 3)
        self.assertEqual(payload["summary"]["ability_count"], 4)
        self.assertEqual(payload["summary"]["unique_ability_count"], 3)

        grouped = {
            entry["signature"]: entry
            for entry in payload["abilities"]
        }
        same_signature = next(
            entry["signature"]
            for entry in payload["abilities"]
            if entry["trigger"] == "ON_LIVE_START" and entry["frames"][0]["opcode_id"] == opcode_id
        )
        self.assertEqual(len(grouped[same_signature]["cards"]), 2)
        # cards are formatted strings like "A-001 | Card A [...] (ab#0 ON_LIVE_START)"
        card_strings = grouped[same_signature]["cards"]
        self.assertTrue(any("Card A" in c for c in card_strings))
        self.assertTrue(any("Card B" in c for c in card_strings))
        self.assertTrue(grouped[same_signature]["round_trip_matches"])
        self.assertIn("frames", grouped[same_signature])
        self.assertTrue(all("opcode" in frame for frame in grouped[same_signature]["frames"]))

    def test_frame_to_sparse_omits_zero_fields(self) -> None:
        sparse = codec.frame_to_sparse(
            {
                "opcode_name": "SET_HEART_COST",
                "payload": {
                    "v": {"pink": 1, "red": 0, "yellow": 0, "green": 0, "blue": 0, "purple": 0, "any": 0},
                    "a": {"req_1": 1, "req_2": 1, "req_3": 0},
                    "s": {"raw": 0},
                },
            }
        )

        self.assertEqual(sparse["opcode"], "SET_HEART_COST")
        self.assertEqual(sparse["value"], {"pink": 1})
        self.assertEqual(sparse["attr"], {"req_1": 1, "req_2": 1})
        self.assertNotIn("slot", sparse)


if __name__ == "__main__":
    unittest.main()
