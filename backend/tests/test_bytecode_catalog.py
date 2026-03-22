import os
import sys
import unittest
from pathlib import Path

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.append(project_root)

from engine.models.generated_packer import pack_a_heart_cost, pack_v_heart_counts
from tools import bytecode_catalog as catalog

ROOT = Path(project_root)


class BytecodeCatalogTests(unittest.TestCase):
    def test_select_mode_frame_annotation_uses_metadata_and_code_refs(self) -> None:
        metadata = catalog.load_json(ROOT / "data" / "metadata.json")

        frame = [30, 4, 0, 0, 1]
        annotation = catalog.annotate_frame(frame, metadata)

        self.assertEqual(annotation["opcode_name"], "SELECT_MODE")
        self.assertEqual(annotation["words"][0]["metadata_refs"], ["metadata.opcodes.SELECT_MODE"])
        self.assertEqual(annotation["words"][1]["role"], "option_count")
        self.assertTrue(any("Ability.compile" in ref for ref in annotation["code_refs"]))
        self.assertIn("SELECT_MODE", annotation["decoded"])

    def test_set_heart_cost_frame_annotation_unpacks_packed_fields(self) -> None:
        metadata = catalog.load_json(ROOT / "data" / "metadata.json")

        frame = [
            83,
            pack_v_heart_counts(pink=1, red=1, yellow=0, green=0, blue=0, purple=0, any=0),
            pack_a_heart_cost(req_1=1, req_2=1),
            0,
            0,
        ]
        annotation = catalog.annotate_frame(frame, metadata)

        self.assertEqual(annotation["opcode_name"], "SET_HEART_COST")
        self.assertEqual(annotation["payload"]["v"]["pink"], 1)
        self.assertEqual(annotation["payload"]["a"]["req_1"], 1)
        self.assertEqual(annotation["words"][1]["role"], "heart_value")
        self.assertTrue(any("pack_a_heart_cost" in ref for ref in annotation["code_refs"]))

    def test_build_card_entry_collects_frames(self) -> None:
        metadata = catalog.load_json(ROOT / "data" / "metadata.json")
        card = {
            "card_no": "TST-001",
            "name": "Test Card",
            "abilities": [
                {
                    "trigger": 2,
                    "raw_text": "TRIGGER: ON_LIVE_START\nEFFECT: SELECT_MODE(1) -> PLAYER",
                    "pseudocode": "TRIGGER: ON_LIVE_START\nEFFECT: SELECT_MODE(1) -> PLAYER",
                    "bytecode": [30, 2, 0, 0, 1, 1, 0, 0, 0, 0],
                    "semantic_form": {"instructions_summary": "Effect(SELECT_MODE)"},
                }
            ],
        }

        entry = catalog.build_card_entry("member_db", "1", card, metadata)

        self.assertEqual(entry["ability_count"], 1)
        self.assertEqual(entry["abilities"][0]["frames"][0]["opcode_name"], "SELECT_MODE")
        self.assertEqual(entry["abilities"][0]["frames"][1]["opcode_name"], "RETURN")

    def test_render_markdown_includes_summary_and_card(self) -> None:
        metadata = catalog.load_json(ROOT / "data" / "metadata.json")
        compiled_data = {
            "member_db": {
                "1": {
                    "card_no": "TST-001",
                    "name": "Test Card",
                    "abilities": [
                        {
                            "trigger": 2,
                            "raw_text": "TRIGGER: ON_LIVE_START\nEFFECT: SELECT_MODE(1) -> PLAYER",
                            "pseudocode": "TRIGGER: ON_LIVE_START\nEFFECT: SELECT_MODE(1) -> PLAYER",
                            "bytecode": [30, 2, 0, 0, 1, 1, 0, 0, 0, 0],
                            "semantic_form": {"instructions_summary": "Effect(SELECT_MODE)"},
                        }
                    ],
                }
            },
            "live_db": {},
            "energy_db": {},
        }

        catalog_data = catalog.build_catalog(compiled_data, metadata)
        rendered = catalog.render_markdown(catalog_data)

        self.assertIn("# Bytecode Catalog", rendered)
        self.assertIn("Cards indexed", rendered)
        self.assertIn("Test Card", rendered)
        self.assertIn("SELECT_MODE", rendered)


if __name__ == "__main__":
    unittest.main()
