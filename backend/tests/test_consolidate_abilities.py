import os
import sys
import unittest
from pathlib import Path

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.append(project_root)

from tools import bytecode_codec as legacy_codec
from tools import frame_codec as codec

ROOT = Path(project_root)


class ConsolidateAbilitiesTests(unittest.TestCase):
    def test_normalizes_authored_frames_and_preserves_card_refs(self) -> None:
        metadata = codec.load_json(ROOT / "data" / "metadata.json")
        trigger_id = int(metadata["triggers"]["ON_LIVE_START"])

        authored_data = {
            "summary": {"card_count": 2, "ability_count": 2},
            "abilities": [
                {
                    "trigger_id": trigger_id,
                    "frames": [{"op": "SELECT_MODE", "value": 2}, "Return"],
                    "pseudocode": "A",
                    "cards": ["A-001 | Card A [member_db:1] (ab#0 ON_LIVE_START)", "A-002 | Card B [member_db:2] (ab#0 ON_LIVE_START)"],
                    "card_refs": [
                        {"card_no": "A-001", "ability_index": 0, "db": "member_db", "card_id": 1, "name": "Card A", "trigger": "ON_LIVE_START"},
                        {"card_no": "A-002", "ability_index": 0, "db": "member_db", "card_id": 2, "name": "Card B", "trigger": "ON_LIVE_START"},
                    ],
                },
                {
                    "trigger_id": int(metadata["triggers"]["CONSTANT"]),
                    "frames": [{"op": "RETURN"}],
                    "card_refs": [{"card_no": "A-003", "ability_index": 0}],
                },
            ],
        }

        payload = codec.build_compact_ability_index(authored_data, metadata)
        self.assertEqual(payload["summary"]["card_count"], 2)
        self.assertEqual(payload["summary"]["ability_count"], 2)
        self.assertEqual(payload["summary"]["unique_ability_count"], 2)

        entry = next(item for item in payload["abilities"] if item["trigger"] == "ON_LIVE_START")
        self.assertEqual(len(entry["cards"]), 2)
        self.assertEqual(len(entry["card_refs"]), 2)
        self.assertEqual(entry["opcode_sequence"], ["SELECT_MODE", "RETURN"])
        self.assertEqual(entry["rust_opcode_sequence"], ["O_SELECT_MODE", "O_RETURN"])
        self.assertEqual(entry["card_refs"][0]["card_no"], "A-001")

    def test_frame_to_sparse_omits_zero_fields(self) -> None:
        sparse = legacy_codec.frame_to_sparse(
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

    def test_compact_index_uses_write_friendly_frames(self) -> None:
        metadata = codec.load_json(ROOT / "data" / "metadata.json")
        trigger_id = int(metadata["triggers"]["ON_LIVE_START"])

        authored_data = {
            "summary": {"card_count": 1, "ability_count": 1},
            "abilities": [
                {
                    "trigger_id": trigger_id,
                    "frames": [
                        {"op": "DRAW", "value": 1, "slot": {"target_slot": int(metadata["slot_indices"]["CONTEXT"])}},
                        "Return",
                    ],
                    "card_refs": [{"card_no": "TST-200", "ability_index": 0}],
                }
            ],
        }

        payload = codec.build_compact_ability_index(authored_data, metadata)
        entry = payload["abilities"][0]
        self.assertEqual(payload["schema"], "ability_frames.flat.v2")
        self.assertTrue(all("op" in frame for frame in entry["frames"]))
        rebuilt = legacy_codec.model_to_bytecode({"frames": entry["frames"]}, metadata)
        self.assertEqual(
            rebuilt,
            [
                int(metadata["opcodes"]["DRAW"]),
                1,
                0,
                0,
                int(metadata["slot_indices"]["CONTEXT"]),
                int(metadata["opcodes"]["RETURN"]),
                0,
                0,
                0,
                0,
            ],
        )


if __name__ == "__main__":
    unittest.main()
