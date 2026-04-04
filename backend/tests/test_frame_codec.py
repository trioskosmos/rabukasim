import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.append(project_root)

from compiler.ability_compiler import AbilityCompiler
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

    def test_runtime_index_strips_source_words(self) -> None:
        metadata = codec.load_json(ROOT / "data" / "metadata.json")
        trigger_id = int(metadata["triggers"]["ACTIVATED"])

        payload = {
            "abilities": [
                {
                    "trigger_id": trigger_id,
                    "instructions": [
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
        self.assertEqual(runtime_payload["schema"], "ability_frame_index.flat.v2")
        self.assertIn("signature_source", runtime_payload["abilities"][0])
        self.assertEqual(runtime_payload["abilities"][0]["instructions"][0]["source_words"], [2, 1, 0, 0, 0])

    def test_authored_input_normalizes_frame_metadata(self) -> None:
        metadata = codec.load_json(ROOT / "data" / "metadata.json")
        trigger_id = int(metadata["triggers"]["ON_LIVE_START"])

        authored_data = {
            "summary": {"card_count": 1, "ability_count": 1},
            "abilities": [
                {
                    "trigger_id": trigger_id,
                    "instructions": [{"op": "DRAW", "options": {"value": 1}}, {"op": "RETURN"}],
                    "card_refs": [{"card_no": "A-001", "ability_index": 0}],
                    "is_once_per_turn": True,
                    "choice_flags": 4,
                    "choice_count": 2,
                }
            ],
        }

        payload = codec.build_compact_ability_index(authored_data, metadata)
        entry = payload["abilities"][0]
        self.assertEqual(payload["schema"], "ability_frames.flat.v2")
        self.assertEqual(entry["source_mode"], "frame_authored")
        self.assertEqual([frame["op"] for frame in entry["instructions"]], ["DRAW", "RETURN"])
        self.assertEqual(entry["instructions"][0]["options"]["value"], 1)
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
                    "instructions": [
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
        instruction = runtime_payload["abilities"][0]["instructions"][0]
        self.assertEqual(instruction["attr"]["group_id"], 2)
        self.assertEqual(instruction["attr"]["keyword_energy"], 1)
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

    def test_ability_to_frame_program_prefers_existing_frames(self) -> None:
        ability = Ability(
            raw_text="authored",
            trigger=TriggerType.CONSTANT,
            effects=[],
            frame_program={"instructions": [{"op": "DRAW", "options": {"value": 1}}, {"op": "RETURN"}]},
        )

        with patch.object(Ability, "compile", side_effect=AssertionError("compile() should not run")):
            frames = ability.to_frame_program()

        self.assertEqual([frame["op"] if isinstance(frame, dict) else frame for frame in frames], ["DRAW", "RETURN"])

    def test_compiler_compile_to_frames_uses_authored_source(self) -> None:
        ability = Ability(
            raw_text="authored",
            trigger=TriggerType.CONSTANT,
            effects=[],
            frame_program={"instructions": [{"op": "DRAW", "options": {"value": 1}}, {"op": "RETURN"}]},
        )
        compiler = AbilityCompiler()

        with patch.object(compiler, "compile_to_bytecode", side_effect=AssertionError("bytecode path should not run")):
            frames = compiler.compile_to_frames(ability)

        self.assertEqual([frame["op"] if isinstance(frame, dict) else frame for frame in frames], ["DRAW", "RETURN"])

    def test_bytecode_no_longer_drives_frame_program_generation(self) -> None:
        ability = Ability(
            raw_text="legacy",
            trigger=TriggerType.CONSTANT,
            effects=[],
            frame_program={"instructions": [{"op": "DRAW", "options": {"value": 1}}, {"op": "RETURN"}]},
            bytecode=[999, 888, 777, 666, 555],
        )

        with patch.object(Ability, "compile", side_effect=AssertionError("compile() should not run")):
            frames = ability.to_frame_program()

        self.assertEqual([frame["op"] if isinstance(frame, dict) else frame for frame in frames], ["DRAW", "RETURN"])
        self.assertEqual(ability.frame_program["instructions"][0]["op"], "DRAW")

    def test_compiler_compile_to_frames_uses_authored_frames_even_with_bytecode_present(self) -> None:
        ability = Ability(
            raw_text="legacy",
            trigger=TriggerType.CONSTANT,
            effects=[],
            frame_program={"instructions": [{"op": "DRAW", "options": {"value": 1}}, {"op": "RETURN"}]},
            bytecode=[999, 888, 777, 666, 555],
        )
        compiler = AbilityCompiler()

        with patch.object(compiler, "compile_to_bytecode", side_effect=AssertionError("bytecode path should not run")):
            frames = compiler.compile_to_frames(ability)

        self.assertEqual([frame["op"] if isinstance(frame, dict) else frame for frame in frames], ["DRAW", "RETURN"])


if __name__ == "__main__":
    unittest.main()
