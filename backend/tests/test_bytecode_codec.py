import os
import sys
import unittest
from pathlib import Path

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.append(project_root)

from engine.models.generated_packer import pack_a_heart_cost, pack_v_heart_counts, pack_v_look_choose
from tools import bytecode_codec as codec

ROOT = Path(project_root)


class BytecodeCodecTests(unittest.TestCase):
    def test_real_card_round_trip_preserves_bytecode(self) -> None:
        compiled = codec.load_json(ROOT / "data" / "cards_compiled.json")
        metadata = codec.load_json(ROOT / "data" / "metadata.json")

        target_card = None
        for db_name in ("member_db", "live_db", "energy_db"):
            for card in compiled.get(db_name, {}).values():
                if card.get("name") == "Bloom the smile, Bloom the dream!":
                    target_card = card
                    break
            if target_card is not None:
                break

        self.assertIsNotNone(target_card, "Expected to find Bloom the smile, Bloom the dream! in compiled data")
        ability = target_card["abilities"][0]
        frame_program = ability.get("frame_program")
        if isinstance(frame_program, dict) and frame_program.get("frames"):
            model = codec.frame_program_to_model(frame_program)
            round_tripped = codec.model_to_bytecode(model)
            self.assertGreater(len(round_tripped), 0)
        else:
            self.assertIn("bytecode", ability, "Legacy compiled data should still expose bytecode when no frame program is present")
            model = codec.bytecode_to_model(list(ability["bytecode"]), metadata)
            round_tripped = codec.model_to_bytecode(model)
            self.assertEqual(round_tripped, list(ability["bytecode"]))

    def test_sparse_model_preserves_source_words_when_requested(self) -> None:
        metadata = codec.load_json(ROOT / "data" / "metadata.json")
        bytecode = [30, 4, 0, 0, 1]

        model = codec.bytecode_to_model(bytecode, metadata)
        sparse_model = codec.model_to_sparse_model(model, include_raw_words=True)

        self.assertEqual(model["frames"][0]["ability_frame_index"], 0)
        self.assertEqual(model["frames"][0]["rust_opcode"], "O_SELECT_MODE")
        self.assertEqual(sparse_model["frames"][0]["ability_frame_index"], 0)
        self.assertEqual(sparse_model["frames"][0]["rust_opcode"], "O_SELECT_MODE")
        self.assertEqual(sparse_model["frames"][0]["source_words"], bytecode)
        self.assertEqual(sparse_model["bytecode"], bytecode)

        compiled_data = {
            "member_db": {
                "card_a": {
                    "card_no": "TST-001",
                    "name": "Test Card",
                    "abilities": [
                        {
                            "trigger": int(metadata["triggers"]["ON_LIVE_START"]),
                            "bytecode": bytecode,
                            "pseudocode": "TRIGGER: ON_LIVE_START\nEFFECT: SELECT_MODE(4) -> PLAYER",
                        }
                    ],
                }
            }
        }

        index = codec.build_ability_index(compiled_data, metadata)
        self.assertEqual(index["summary"]["ability_count"], 1)
        self.assertEqual(index["abilities"][0]["source_words"], bytecode)
        self.assertEqual(index["abilities"][0]["opcode_sequence"], ["SELECT_MODE"])
        self.assertEqual(index["abilities"][0]["rust_opcode_sequence"], ["O_SELECT_MODE"])

    def test_sparse_semantic_model_can_be_edited_and_re_encoded(self) -> None:
        metadata = codec.load_json(ROOT / "data" / "metadata.json")
        bytecode = [41, pack_v_look_choose(count=5, char_id_1=21, reveal=1, dest_discard=1), 0, 0, 0]

        model = codec.bytecode_to_model(bytecode, metadata)
        sparse_model = codec.model_to_sparse_model(model)

        self.assertIn("semantic", sparse_model["frames"][0])
        self.assertEqual(sparse_model["frames"][0]["ability_frame_index"], 0)
        sparse_model["frames"][0]["semantic"]["value"]["count"] = 2

        reencoded = codec.model_to_bytecode(sparse_model)

        self.assertEqual(reencoded, [41, codec._to_i32(pack_v_look_choose(count=2, char_id_1=21, reveal=1, dest_discard=1)), 0, 0, 0])
        self.assertNotEqual(reencoded, bytecode)

    def test_select_mode_frame_round_trip(self) -> None:
        metadata = codec.load_json(ROOT / "data" / "metadata.json")

        frame = {"words": [30, 4, 0, 0, 1]}
        lookups = codec.load_lookups(metadata)
        decoded = codec.decode_frame(frame["words"], lookups)
        encoded = codec.encode_frame(decoded, lookups)

        self.assertEqual(encoded, frame["words"])
        self.assertEqual(decoded["opcode_name"], "SELECT_MODE")

    def test_special_packed_frames_round_trip(self) -> None:
        metadata = codec.load_json(ROOT / "data" / "metadata.json")
        lookups = codec.load_lookups(metadata)

        look_frame = [41, pack_v_look_choose(count=5, char_id_1=21, reveal=1, dest_discard=1), 0, 0, 6]
        heart_frame = [83, pack_v_heart_counts(pink=1, red=1, yellow=0, green=0, blue=0, purple=0, any=0), pack_a_heart_cost(req_1=1, req_2=1), 0, 0]

        look_model = codec.decode_frame(look_frame, lookups)
        heart_model = codec.decode_frame(heart_frame, lookups)

        self.assertEqual(codec.encode_frame(look_model, lookups), look_frame)
        self.assertEqual(codec.encode_frame(heart_model, lookups), heart_frame)
        self.assertEqual(look_model["payload"]["v"]["count"], 5)
        self.assertEqual(heart_model["payload"]["a"]["req_1"], 1)

    # ------------------ NEW: frame-first model tests ------------------

    def test_sparse_index_entries_have_no_top_level_bytecode(self) -> None:
        """build_sparse_ability_index must not include a top-level bytecode field per entry."""
        metadata = codec.load_json(ROOT / "data" / "metadata.json")
        trigger_id = int(metadata["triggers"]["ON_LIVE_START"])
        opcode_id = int(metadata["opcodes"]["DRAW"])

        compiled_data = {
            "member_db": {
                "card_x": {
                    "card_no": "TST-100",
                    "name": "Frame Test Card",
                    "abilities": [{"trigger": trigger_id, "bytecode": [opcode_id, 3, 0, 0, 0, 1, 0, 0, 0, 0], "pseudocode": "EFFECT: DRAW(3)"}],
                }
            }
        }
        payload = codec.build_sparse_ability_index(compiled_data, metadata)
        for entry in payload["abilities"]:
            self.assertNotIn("bytecode", entry, "Sparse index entry must not carry top-level bytecode field")
            self.assertIn("frames", entry, "Sparse index entry must have a frames list")

    def test_sparse_index_frames_round_trip_to_bytecode(self) -> None:
        """Frames in a sparse index entry can be re-encoded to recreate the original bytecode."""
        metadata = codec.load_json(ROOT / "data" / "metadata.json")
        trigger_id = int(metadata["triggers"]["ON_LIVE_START"])
        opcode_id = int(metadata["opcodes"]["DRAW"])
        original_bytecode = [opcode_id, 3, 0, 0, 0, 1, 0, 0, 0, 0]

        compiled_data = {
            "member_db": {
                "card_x": {
                    "card_no": "TST-100",
                    "name": "Frame Test Card",
                    "abilities": [{"trigger": trigger_id, "bytecode": original_bytecode, "pseudocode": "EFFECT: DRAW(3)"}],
                }
            }
        }
        payload = codec.build_sparse_ability_index(compiled_data, metadata)
        entry = payload["abilities"][0]
        rebuilt = codec.model_to_bytecode({"frames": entry["frames"]})
        self.assertEqual(rebuilt, original_bytecode, "Frames must round-trip to original bytecode")

    def test_sunny_day_song_compact_frames_round_trip(self) -> None:
        """The long Sunny Day Song ability can be edited in compact form and re-encoded."""
        compiled = codec.load_json(ROOT / "data" / "cards_compiled.json")
        metadata = codec.load_json(ROOT / "data" / "metadata.json")

        card = compiled["live_db"]["669"]
        ability = card["abilities"][0]
        frame_program = ability.get("frame_program", {})
        if isinstance(frame_program, dict) and frame_program.get("frames"):
            model = codec.frame_program_to_model(frame_program)
        else:
            model = codec.bytecode_to_model(list(ability["bytecode"]), metadata)
        compact_model = codec.model_to_compact_model(model)

        self.assertGreaterEqual(len(compact_model["frames"]), 10)
        self.assertTrue(all("op" in frame for frame in compact_model["frames"]))

        rebuilt = codec.model_to_bytecode({"frames": compact_model["frames"]}, metadata)
        self.assertGreater(len(rebuilt), 0)

        round_tripped = codec.bytecode_to_model(rebuilt, metadata)
        self.assertEqual(len(round_tripped["frames"]), len(compact_model["frames"]))
        self.assertEqual(codec.model_to_bytecode(round_tripped, metadata), rebuilt)


if __name__ == "__main__":
    unittest.main()
