import os
import sys
import unittest
from pathlib import Path

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.append(project_root)

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
        self.assertEqual(runtime_payload["schema"], "ability_frame_index.flat.v2")
        self.assertNotIn("signature_source", runtime_payload["abilities"][0])
        self.assertTrue(all("source_words" not in frame for frame in runtime_payload["abilities"][0]["frames"]))

    def test_legacy_compiled_input_bootstraps_into_authored_frames(self) -> None:
        metadata = codec.load_json(ROOT / "data" / "metadata.json")
        trigger_id = int(metadata["triggers"]["ON_LIVE_START"])
        draw_opcode = int(metadata["opcodes"]["DRAW"])
        return_opcode = int(metadata["opcodes"]["RETURN"])

        compiled_data = {
            "member_db": {
                "card_a": {
                    "card_no": "A-001",
                    "name": "Bootstrap Card",
                    "abilities": [
                        {"trigger": trigger_id, "bytecode": [draw_opcode, 1, 0, 0, 0, return_opcode, 0, 0, 0, 0]}
                    ],
                }
            }
        }

        payload = codec.build_compact_ability_index(compiled_data, metadata)
        entry = payload["abilities"][0]
        self.assertEqual(payload["schema"], "ability_frames.flat.v2")
        self.assertEqual(entry["source_mode"], "legacy_bootstrap")
        self.assertEqual([frame["op"] for frame in entry["frames"]], ["DRAW", "RETURN"])


if __name__ == "__main__":
    unittest.main()