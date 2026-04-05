import os
import sys
import unittest
from pathlib import Path

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.append(project_root)

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
                    "frames": [{"op": "SELECT_MODE", "options": {"value": 2}}, {"op": "RETURN"}],
                    "pseudocode": "A",
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
        self.assertEqual(payload["summary"]["card_count"], 3)
        self.assertEqual(payload["summary"]["ability_count"], 3)
        self.assertEqual(payload["summary"]["unique_ability_count"], 2)

        entry = next(item for item in payload["abilities"] if item["trigger"] == "ON_LIVE_START")
        self.assertEqual(len(entry["cards"]), 2)
        self.assertEqual(len(entry["card_refs"]), 2)
        self.assertEqual(entry["opcode_sequence"], ["SELECT_MODE", "RETURN"])
        self.assertEqual(entry["frames"][0]["options"]["value"], 2)
        self.assertEqual(entry["card_refs"][0]["card_no"], "A-001")

    def test_normalize_frame_supports_return_shorthand(self) -> None:
        self.assertEqual(codec._normalize_frame("Return", 0), {"op": "RETURN", "frame_index": 0})
        self.assertEqual(codec._normalize_frame({"Return": {}}, 1), {"op": "RETURN", "frame_index": 1})

    def test_compact_index_uses_write_friendly_frames(self) -> None:
        metadata = codec.load_json(ROOT / "data" / "metadata.json")
        trigger_id = int(metadata["triggers"]["ON_LIVE_START"])

        authored_data = {
            "summary": {"card_count": 1, "ability_count": 1},
            "abilities": [
                {
                    "trigger_id": trigger_id,
                    "frames": [
                        {
                            "op": "DRAW",
                            "options": {"value": 1, "slot": {"target_slot": int(metadata["slot_indices"]["CONTEXT"])}},
                        },
                        {"op": "RETURN"},
                    ],
                    "card_refs": [{"card_no": "TST-200", "ability_index": 0}],
                }
            ],
        }

        payload = codec.build_compact_ability_index(authored_data, metadata)
        entry = payload["abilities"][0]
        self.assertEqual(payload["schema"], "ability_frame_source.flat.v2")
        self.assertTrue(all("op" in frame for frame in entry["frames"]))
        self.assertEqual(entry["frames"][0]["op"], "DRAW")
        self.assertEqual(entry["frames"][0]["options"]["value"], 1)
        self.assertEqual(
            entry["frames"][0]["options"]["slot"]["target_slot"],
            int(metadata["slot_indices"]["CONTEXT"]),
        )
        self.assertEqual(entry["frames"][1]["op"], "RETURN")

    def test_compact_index_backfills_structured_card_refs(self) -> None:
        metadata = codec.load_json(ROOT / "data" / "metadata.json")
        trigger_id = int(metadata["triggers"]["ON_LIVE_START"])

        authored_data = {
            "summary": {"card_count": 1, "ability_count": 1},
            "abilities": [
                {
                    "trigger_id": trigger_id,
                    "frames": [{"op": "DRAW", "value": 1}, {"op": "RETURN"}],
                    "cards": ["TST-200 | Test Card [member_db:200] (ab#0 ON_LIVE_START)"],
                }
            ],
        }
        card_db = {
            "member_db": {
                "200": {
                    "card_id": 200,
                    "card_no": "TST-200",
                    "name": "Test Card",
                    "abilities": [{"trigger": trigger_id}],
                }
            }
        }

        payload = codec.build_compact_ability_index(authored_data, metadata, card_db)
        entry = payload["abilities"][0]

        self.assertEqual(len(entry["card_refs"]), 1)
        self.assertEqual(entry["card_refs"][0]["card_no"], "TST-200")
        self.assertEqual(entry["card_refs"][0]["ability_index"], 0)
        self.assertEqual(entry["card_refs"][0]["card_id"], 200)
        self.assertEqual(entry["card_refs"][0]["db"], "member_db")

    def test_real_compact_index_preserves_opcode_sequences(self) -> None:
        metadata = codec.load_json(ROOT / "data" / "metadata.json")
        source_path = ROOT / "data" / "ability_frame_source.json"
        authored_data = codec.load_authored_payload(source_path)

        payload = codec.build_compact_ability_index(authored_data, metadata)

        for entry in payload["abilities"]:
            frames = entry["frames"]
            opcodes = [frame["op"] for frame in frames]

            self.assertTrue(all(opcodes), msg=f"missing opcode in {entry.get('signature')}")
            self.assertEqual(
                entry["opcode_sequence"],
                opcodes,
                msg=f"opcode sequence mismatch in {entry.get('signature')}",
            )
            self.assertEqual(entry["frame_count"], len(frames))


if __name__ == "__main__":
    unittest.main()
