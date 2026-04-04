import os
import sys
import unittest
from pathlib import Path

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.append(project_root)

from engine.compiler import main as compiler_main
from engine.compiler.semantic_processor import populate_semantic_from_frames
from engine.models.ability import Ability
from engine.models.generated_enums import TriggerType, EffectType


ROOT = Path(project_root)


class CompilerPseudocodeSourceTests(unittest.TestCase):
    def test_pseudocode_counts_as_ability_source(self) -> None:
        self.assertTrue(compiler_main._card_has_ability_source({"pseudocode": "TRIGGER: ON_PLAY; EFFECT: DRAW(1)"}))

    def test_runtime_export_keeps_raw_text_and_frame_program(self) -> None:
        exclude_ability_fields, _ = compiler_main._build_export_excludes("runtime")

        self.assertNotIn("raw_text", exclude_ability_fields)
        self.assertNotIn("frame_program", exclude_ability_fields)

    def test_look_and_choose_inference_updates_frame_program(self) -> None:
        ability = Ability(
            raw_text="デッキの上からカードを7枚見る。その中からメンバーカードを3枚まで公開して手札に加えてもよい。",
            trigger=TriggerType.ON_PLAY,
            effects=[],
            frame_program={
                "frames": [
                    {
                        "op": "LOOK_AND_CHOOSE",
                        "value": {"count": 7, "reveal": 1},
                        "slot": {"target_slot": 6},
                    }
                ]
            },
        )

        populate_semantic_from_frames([ability])

        self.assertEqual(len(ability.effects), 1)
        self.assertEqual(ability.effects[0].effect_type, EffectType.LOOK_AND_CHOOSE)
        self.assertEqual(ability.effects[0].params.get("choose_count"), 3)
        self.assertEqual(
            ability.frame_program["frames"][0]["params"].get("choose_count"),
            3,
        )
        self.assertEqual(
            ability.frame_program["frames"][0]["value"].get("choose_count"),
            3,
        )


if __name__ == "__main__":
    unittest.main()