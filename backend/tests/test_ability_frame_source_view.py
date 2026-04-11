import os
import sys
import unittest

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.append(project_root)

from tools.render_ability_frame_source_view import render_simple_view
from tools.render_ability_frame_source_view import parse_simple_view


class AbilityFrameSourceViewTests(unittest.TestCase):
    def test_renders_readable_rules_text(self) -> None:
        payload = {
            "abilities": [
                {
                    "trigger": "ON_PLAY",
                    "card_refs": [{"card_no": "TST-001"}],
                    "frames": [
                        {"op": "COUNT_STAGE", "value": 1, "slot": {"target_slot": "STAGE_0", "comparison": "GE"}},
                        {"op": "JUMP_IF_FALSE", "value": 2},
                        {"op": "DRAW", "value": 1},
                        {"op": "RETURN"},
                    ],
                }
            ]
        }

        rendered = render_simple_view(payload)

        self.assertIn("on_play", rendered)
        self.assertIn("if count(stage) >= 1:", rendered)
        self.assertIn("draw 1", rendered)
        self.assertIn("meta:", rendered)

    def test_render_parse_round_trip_preserves_payload(self) -> None:
        payload = {
            "schema": "ability_frame_source.flat.v2",
            "abilities": [
                {
                    "trigger": "ON_PLAY",
                    "trigger_id": 1,
                    "primary_text_jp": "test",
                    "card_refs": [{"card_no": "TST-001", "ability_index": 0}],
                    "frames": [
                        {"op": "COUNT_STAGE", "value": 1, "slot": {"target_slot": "STAGE_0", "comparison": "GE"}},
                        {"op": "JUMP_IF_FALSE", "value": 2},
                        {"op": "DRAW", "value": 1},
                        {"op": "RETURN"},
                    ],
                }
            ],
        }

        rendered = render_simple_view(payload)
        parsed = parse_simple_view(rendered)

        self.assertEqual(parsed, payload)


if __name__ == "__main__":
    unittest.main()
