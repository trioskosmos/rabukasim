import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.append(project_root)

from engine.models.ability import Ability
from engine.models.generated_enums import TriggerType
from tools import frame_codec as codec

ROOT = Path(project_root)


class FrameCodecTests(unittest.TestCase):
    def test_authored_frames_are_signature_based_not_source_word_based(self) -> None:
        metadata = codec.load_json(ROOT / "data" / "metadata.json")
        trigger_id = int(metadata["triggers"]["ON_LIVE_START"])

        base_entry = {
            "trigger_id": trigger_id,
            "frames": [
                {"op": "DRAW", "value": 2, "source_words": [2, 2, 0, 0, 0]},
                {"op": "RETURN", "source_words": [1, 0, 0, 0, 0]},
            ],
            "cards": ["TST-001 | Test Card [member_db:1] (ab#0 ON_LIVE_START)"],
            "card_refs": [{"card_no": "TST-001", "ability_index": 0, "db": "member_db", "card_id": 1, "name": "Test Card", "trigger": "ON_LIVE_START"}],
        }
        changed_words_entry = {
            **base_entry,
            "frames": [
                {"op": "DRAW", "value": 2, "source_words": [999, 2, 3, 4, 5]},
                {"op": "RETURN", "source_words": [111, 0, 0, 0, 0]},
            ],
        }

        payload_a = codec.normalize_authored_ability_index({"abilities": [base_entry], "summary": {}}, metadata)
        payload_b = codec.normalize_authored_ability_index({"abilities": [changed_words_entry], "summary": {}}, metadata)

        self.assertEqual(payload_a["abilities"][0]["signature"], payload_b["abilities"][0]["signature"])
        self.assertEqual(payload_a["abilities"][0]["signature_hash"], payload_b["abilities"][0]["signature_hash"])

    def test_authored_frames_signature_changes_when_frame_semantics_change(self) -> None:
        metadata = codec.load_json(ROOT / "data" / "metadata.json")
        trigger_id = int(metadata["triggers"]["ON_LIVE_START"])

        base_entry = {
            "trigger_id": trigger_id,
            "frames": [
                {
                    "op": "SELECT_MEMBER",
                    "value": 1,
                    "attr": {"target_player": 1, "special_id": 3},
                    "slot": {"target_slot": 4, "source_zone": "STAGE"},
                    "source_words": [1, 2, 3, 4, 5],
                },
                {"op": "ADD_HEARTS", "value": 1, "slot": {"target_slot": 4}},
                {"op": "RETURN", "source_words": [0, 0, 0, 0, 0]},
            ],
            "cards": ["TST-001 | Test Card [member_db:1] (ab#0 ON_LIVE_START)"],
            "card_refs": [{"card_no": "TST-001", "ability_index": 0, "db": "member_db", "card_id": 1, "name": "Test Card", "trigger": "ON_LIVE_START"}],
        }
        changed_semantics_entry = {
            **base_entry,
            "frames": [
                {
                    "op": "SELECT_MEMBER",
                    "value": 1,
                    "attr": {"target_player": 1, "special_id": 7},
                    "slot": {"target_slot": 4, "source_zone": "STAGE"},
                    "source_words": [999, 2, 3, 4, 5],
                },
                {"op": "ADD_HEARTS", "value": 1, "slot": {"target_slot": 4}},
                {"op": "RETURN", "source_words": [111, 0, 0, 0, 0]},
            ],
        }

        payload_a = codec.normalize_authored_ability_index({"abilities": [base_entry], "summary": {}}, metadata)
        payload_b = codec.normalize_authored_ability_index({"abilities": [changed_semantics_entry], "summary": {}}, metadata)

        self.assertNotEqual(payload_a["abilities"][0]["signature"], payload_b["abilities"][0]["signature"])
        self.assertNotEqual(payload_a["abilities"][0]["signature_hash"], payload_b["abilities"][0]["signature_hash"])

    def test_runtime_index_strips_source_words(self) -> None:
        metadata = codec.load_json(ROOT / "data" / "metadata.json")
        trigger_id = int(metadata["triggers"]["ACTIVATED"])

        payload = {
            "abilities": [
                {
                    "trigger_id": trigger_id,
                    "frames": [
                        {"op": "DRAW", "value": 1, "source_words": [2, 1, 0, 0, 0]},
                        {"op": "RETURN", "source_words": [1, 0, 0, 0, 0]},
                    ],
                    "cards": [],
                    "card_refs": [],
                }
            ],
            "summary": {"card_count": 0, "ability_count": 1},
        }

        runtime_payload = codec.build_runtime_ability_index(payload, metadata)
        self.assertEqual(runtime_payload["schema"], "ability_runtime_index.flat.v2")
        self.assertIn("signature_source", runtime_payload["abilities"][0])
        self.assertIn('"frames"', runtime_payload["abilities"][0]["signature_source"])
        self.assertEqual(runtime_payload["abilities"][0]["frames"][0]["source_words"], [2, 1, 0, 0, 0])

    def test_authored_input_normalizes_frame_metadata(self) -> None:
        metadata = codec.load_json(ROOT / "data" / "metadata.json")
        trigger_id = int(metadata["triggers"]["ON_LIVE_START"])

        authored_data = {
            "summary": {"card_count": 1, "ability_count": 1},
            "abilities": [
                {
                    "trigger_id": trigger_id,
                    "frames": [{"op": "DRAW", "options": {"value": 1}}, {"op": "RETURN"}],
                    "card_refs": [{"card_no": "A-001", "ability_index": 0}],
                    "is_once_per_turn": True,
                    "choice_flags": 4,
                    "choice_count": 2,
                }
            ],
        }

        payload = codec.build_compact_ability_index(authored_data, metadata)
        entry = payload["abilities"][0]
        self.assertEqual(payload["schema"], "ability_frame_source.flat.v2")
        self.assertEqual(entry["source_mode"], "frame_authored")
        self.assertEqual([frame["op"] for frame in entry["frames"]], ["DRAW", "RETURN"])
        self.assertEqual(entry["frames"][0]["options"]["value"], 1)
        self.assertTrue(entry["is_once_per_turn"])
        self.assertEqual(entry["choice_flags"], 4)
        self.assertEqual(entry["choice_count"], 2)

    def test_runtime_index_preserves_attr_metadata(self) -> None:
        metadata = codec.load_json(ROOT / "data" / "metadata.json")
        trigger_id = int(metadata["triggers"]["ON_LIVE_START"])

        payload = {
            "abilities": [
                {
                    "trigger_id": trigger_id,
                    "frames": [
                        {
                            "op": "HAS_KEYWORD",
                            "attr": {"group_enabled": 1, "group_id": 2, "keyword_energy": 1},
                            "slot": {"target_slot": 48},
                        },
                        {"op": "RETURN"},
                    ],
                    "cards": [],
                    "card_refs": [],
                }
            ],
            "summary": {"card_count": 0, "ability_count": 1},
        }

        runtime_payload = codec.build_runtime_ability_index(payload, metadata)
        frame = runtime_payload["abilities"][0]["frames"][0]
        self.assertEqual(frame["attr"]["group_id"], 2)
        self.assertEqual(frame["attr"]["keyword_energy"], 1)
        self.assertEqual(runtime_payload["abilities"][0]["frames"][0]["op"], "HAS_KEYWORD")

    def test_runtime_index_preserves_original_frame_shape(self) -> None:
        metadata = codec.load_json(ROOT / "data" / "metadata.json")
        trigger_id = int(metadata["triggers"]["ON_LIVE_START"])

        payload = {
            "abilities": [
                {
                    "trigger_id": trigger_id,
                    "frames": [
                        {
                            "opcode": "SELECT_MEMBER",
                            "opcode_id": 65,
                            "decoded": "SELECT_MEMBER | count=1, filter=[target=self, group=Aqours]",
                            "value": 1,
                            "attr": {"target_player": 1, "group_enabled": 1, "group_id": 1},
                            "slot": {"target_slot": 4, "source_zone": "STAGE"},
                        },
                        "Return",
                    ],
                    "cards": ["TST-459 | Test Live [live_db:459] (ab#0 ON_LIVE_START)"],
                }
            ],
            "summary": {"card_count": 1, "ability_count": 1},
        }

        runtime_payload = codec.build_runtime_ability_index(payload, metadata)
        frame = runtime_payload["abilities"][0]["frames"][0]
        self.assertEqual(frame["opcode"], "SELECT_MEMBER")
        self.assertEqual(frame["opcode_id"], 65)
        self.assertIn("decoded", frame)

    def test_runtime_index_adds_authored_text_and_opcode_catalog(self) -> None:
        metadata = codec.load_json(ROOT / "data" / "metadata.json")
        trigger_id = int(metadata["triggers"]["ON_LIVE_START"])

        payload = {
            "abilities": [
                {
                    "trigger_id": trigger_id,
                    "frames": [
                        {"op": "DRAW", "value": 1},
                        {"op": "SUM_VALUE"},
                        {"op": "RETURN"},
                    ],
                    "cards": ["TST-001 | Test Card [member_db:1] (ab#0 ON_LIVE_START)"],
                }
            ],
            "summary": {"card_count": 1, "ability_count": 1},
        }
        card_db = {
            "member_db": {
                "1": {
                    "card_id": 1,
                    "card_no": "TST-001",
                    "name": "Test Card",
                    "original_text": "{{live_start.png|ライブ開始時}}カードを1枚引く。",
                    "original_text_en": "{{live_start.png|On live start}} Draw 1 card.",
                    "abilities": [{"trigger": trigger_id}],
                }
            }
        }

        runtime_payload = codec.build_runtime_ability_index(payload, metadata, card_db)
        entry = runtime_payload["abilities"][0]

        self.assertEqual(entry["primary_text_jp"], "{{live_start.png|ライブ開始時}}カードを1枚引く。")
        self.assertEqual(entry["primary_text_en"], "{{live_start.png|On live start}} Draw 1 card.")
        self.assertEqual(entry["source_ability_texts"][0]["card_examples"], ["TST-001 | Test Card [member_db:1] (ab#0 ON_LIVE_START)"])
        self.assertEqual(runtime_payload["summary"]["text_covered_ability_count"], 1)
        self.assertEqual(runtime_payload["summary"]["text_missing_ability_count"], 0)

        opcode_catalog = runtime_payload["opcode_catalog"]
        self.assertEqual(opcode_catalog["unknown_count"], 0)
        used_names = {(item["name"], item["section"], item["opcode_id"]) for item in opcode_catalog["used_entries"]}
        self.assertIn(("DRAW", "opcodes", 10), used_names)
        self.assertIn(("SUM_VALUE", "conditions", 312), used_names)

    def test_runtime_index_adds_readable_frame_overlay(self) -> None:
        metadata = codec.load_json(ROOT / "data" / "metadata.json")
        trigger_id = int(metadata["triggers"]["ON_LIVE_START"])

        payload = {
            "abilities": [
                {
                    "trigger_id": trigger_id,
                    "frames": [
                        {
                            "opcode_id": 45,
                            "opcode": "COLOR_SELECT",
                            "value": 1,
                            "attr": {"target_player": 1, "color_mask": 74},
                            "slot": {"target_slot": 4},
                            "semantic": {
                                "opcode_id": 45,
                                "opcode_name": "COLOR_SELECT",
                                "opcode_section": "opcodes",
                                "decoded": "COLOR_SELECT | value=1, filter=[target=self, colors=red/green/any], slot=[target=Context Card]",
                                "metadata_refs": ["opcodes.COLOR_SELECT", "slot_indices.CONTEXT"],
                            },
                        },
                        {
                            "opcode_id": 12,
                            "opcode": "ADD_HEARTS",
                            "value": 1,
                            "attr": {"target_player": 1, "compare_accumulated": 1},
                            "slot": {
                                "remainder_zone": int(metadata["multiplier_count_sources"]["SUCCESS_PILE_COUNT"]),
                                "is_dynamic": 1,
                            },
                            "params": {
                                "scalar_dynamic": {
                                    "base_value": 1,
                                    "divisor": 1,
                                }
                            },
                            "semantic": {
                                "opcode_id": 12,
                                "opcode_name": "ADD_HEARTS",
                                "opcode_section": "opcodes",
                                "decoded": "ADD_HEARTS | count=1, filter=[target=self, compare_accumulated], slot=[multiplier_source=SUCCESS_PILE_COUNT, dynamic]",
                                "metadata_refs": ["opcodes.ADD_HEARTS"],
                            },
                        },
                        {"op": "RETURN"},
                    ],
                    "cards": ["TST-002 | Readable Card [member_db:2] (ab#0 ON_LIVE_START)"],
                }
            ],
            "summary": {"card_count": 1, "ability_count": 1},
        }

        runtime_payload = codec.build_runtime_ability_index(payload, metadata)
        color_frame = runtime_payload["abilities"][0]["frames"][0]
        heart_frame = runtime_payload["abilities"][0]["frames"][1]

        self.assertEqual(color_frame["readable"]["attr"]["target_player"], "SELF")
        self.assertEqual(color_frame["readable"]["attr"]["color_mask"], ["RED", "GREEN", "ANY"])
        self.assertEqual(color_frame["readable"]["slot"]["target_slot"], "CONTEXT")
        self.assertNotIn("metadata_refs", color_frame["semantic"])

        self.assertEqual(heart_frame["readable"]["value"]["base_value"], 1)
        self.assertEqual(heart_frame["readable"]["value"]["divisor"], 1)
        self.assertEqual(heart_frame["readable"]["value"]["resolved"], "1 x SUCCESS_PILE_COUNT")
        self.assertEqual(heart_frame["readable"]["slot"]["multiplier_source"], "SUCCESS_PILE_COUNT")
        self.assertEqual(heart_frame["semantic"]["display"]["attr"]["target_player"], "SELF")
        self.assertIn("count=1 x SUCCESS_PILE_COUNT", heart_frame["semantic"]["decoded"])
        self.assertNotIn("metadata_refs", heart_frame["semantic"])

    def test_ability_to_frame_program_prefers_existing_frames(self) -> None:
        ability = Ability(
            raw_text="authored",
            trigger=TriggerType.CONSTANT,
            effects=[],
            frame_program={"frames": [{"op": "DRAW", "options": {"value": 1}}, {"op": "RETURN"}]},
        )

        with patch.object(Ability, "compile", side_effect=AssertionError("compile() should not run")):
            frames = ability.to_frame_program()

        self.assertEqual([frame["op"] if isinstance(frame, dict) else frame for frame in frames], ["DRAW", "RETURN"])

    def test_bytecode_no_longer_drives_frame_program_generation(self) -> None:
        ability = Ability(
            raw_text="legacy",
            trigger=TriggerType.CONSTANT,
            effects=[],
            frame_program={"frames": [{"op": "DRAW", "options": {"value": 1}}, {"op": "RETURN"}]},
            bytecode=[999, 888, 777, 666, 555],
        )

        with patch.object(Ability, "compile", side_effect=AssertionError("compile() should not run")):
            frames = ability.to_frame_program()

        self.assertEqual([frame["op"] if isinstance(frame, dict) else frame for frame in frames], ["DRAW", "RETURN"])
        self.assertEqual(ability.frame_program["frames"][0]["op"], "DRAW")

if __name__ == "__main__":
    unittest.main()
