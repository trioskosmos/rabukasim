import os
import sys
import tempfile
import unittest
from pathlib import Path

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.append(project_root)

from tools import frame_codec as codec

ROOT = Path(project_root)
AUTHORED_SOURCE_PATH = ROOT / "data" / "ability_frame_source.json"


def _load_authored_entries() -> list[dict]:
    payload = codec.load_authored_payload(AUTHORED_SOURCE_PATH)
    return payload["abilities"]


class ConsolidateAbilitiesTests(unittest.TestCase):
    def test_load_authored_payload_accepts_utf8_bom_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            source_path = Path(tmp_dir) / "bom_authored.json"
            source_path.write_text('{"abilities": [{"trigger_id": 1, "frames": [{"op": "RETURN"}]}]}', encoding="utf-8-sig")

            payload = codec.load_authored_payload(source_path)

            self.assertEqual(len(payload["abilities"]), 1)
            self.assertEqual(payload["abilities"][0]["trigger_id"], 1)

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

    def test_compact_index_keeps_source_only_fields_with_sorted_entries(self) -> None:
        metadata = codec.load_json(ROOT / "data" / "metadata.json")
        trigger_id = int(metadata["triggers"]["ON_LIVE_START"])

        authored_data = {
            "summary": {"card_count": 2, "ability_count": 2},
            "abilities": [
                {
                    "trigger_id": trigger_id,
                    "frames": [{"op": "RETURN"}],
                    "cards": ["B-001 | Sort Later (ab#0)"],
                },
                {
                    "trigger_id": trigger_id,
                    "frames": [{"op": "DRAW", "value": 1}, {"op": "RETURN"}],
                    "cards": ["A-001 | Sort First (ab#0)", "A-002 | Sort First Too (ab#0)"],
                    "choice_flags": 7,
                    "choice_count": 2,
                    "is_once_per_turn": True,
                    "requires_selection": True,
                },
            ],
        }

        payload = codec.build_compact_ability_index(authored_data, metadata)
        entry = next(item for item in payload["abilities"] if item["opcode_sequence"] == ["DRAW", "RETURN"])

        self.assertEqual(entry["choice_flags"], 7)
        self.assertEqual(entry["choice_count"], 2)
        self.assertTrue(entry["is_once_per_turn"])
        self.assertTrue(entry["requires_selection"])

    def test_authored_source_uses_named_categorical_identifiers(self) -> None:
        authored_entries = _load_authored_entries()
        slot_keys = {"target_slot", "comparison", "source_zone", "dest_zone", "remainder_zone"}
        attr_keys = {
            "target_player",
            "card_type",
            "group_id",
            "unit_id",
            "char_id_1",
            "char_id_2",
            "char_id_3",
            "color_mask",
            "zone_mask",
            "special_id",
            "keyword",
        }

        bad_fields: list[str] = []
        for entry in authored_entries:
            signature = entry.get("signature", "<missing-signature>")
            for frame in entry.get("frames", []):
                for key in slot_keys:
                    value = frame.get("slot", {}).get(key)
                    if value is not None and not isinstance(value, str):
                        bad_fields.append(f"{signature}: slot.{key}={value!r}")
                for key in attr_keys:
                    value = frame.get("attr", {}).get(key)
                    if value is not None and not isinstance(value, str):
                        bad_fields.append(f"{signature}: attr.{key}={value!r}")

        self.assertEqual(bad_fields, [], "\n".join(bad_fields))

    def test_ll_bp1_001_r_plus_uses_ayumu_kanon_kaho_filter(self) -> None:
        authored_entries = _load_authored_entries()

        target_entry = next(
            entry
            for entry in authored_entries
            if any(
                ref.get("card_no") == "LL-bp1-001-R+" and ref.get("ability_index") == 1
                for ref in entry.get("card_refs", [])
            )
        )

        move_frame = target_entry["frames"][0]
        self.assertEqual(move_frame["op"], "MOVE_TO_DISCARD")
        self.assertEqual(move_frame["attr"].get("char_id_1"), "AYUMU")
        self.assertEqual(move_frame["attr"].get("char_id_2"), "KANON")
        self.assertEqual(move_frame["attr"].get("char_id_3"), "KAHO")
        self.assertNotIn("unit_id", move_frame["attr"])


if __name__ == "__main__":
    unittest.main()
