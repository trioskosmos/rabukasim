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
        model = codec.bytecode_to_model(list(ability["bytecode"]), metadata)
        round_tripped = codec.model_to_bytecode(model)

        self.assertEqual(round_tripped, list(ability["bytecode"]))

    def test_sparse_model_preserves_source_words_when_requested(self) -> None:
        metadata = codec.load_json(ROOT / "data" / "metadata.json")
        bytecode = [30, 4, 0, 0, 1]

        model = codec.bytecode_to_model(bytecode, metadata)
        sparse_model = codec.model_to_sparse_model(model, include_raw_words=True)

        self.assertEqual(model["frames"][0]["ability_frame_index"], 0)
        self.assertEqual(sparse_model["frames"][0]["ability_frame_index"], 0)
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

    def test_sparse_semantic_model_can_be_edited_and_re_encoded(self) -> None:
        metadata = codec.load_json(ROOT / "data" / "metadata.json")
        bytecode = [41, pack_v_look_choose(count=5, char_id_1=21, reveal=1, dest_discard=1), 0, 0, 0]

        model = codec.bytecode_to_model(bytecode, metadata)
        sparse_model = codec.model_to_sparse_model(model)

        self.assertIn("semantic", sparse_model["frames"][0])
        self.assertEqual(sparse_model["frames"][0]["ability_frame_index"], 0)
        sparse_model["frames"][0]["semantic"]["value"]["count"] = 2

        reencoded = codec.model_to_bytecode(sparse_model)

        self.assertEqual(reencoded, [41, pack_v_look_choose(count=2, char_id_1=21, reveal=1, dest_discard=1), 0, 0, 0])
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


if __name__ == "__main__":
    unittest.main()
