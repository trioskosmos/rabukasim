import os
import sys
import unittest

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.append(project_root)

from compiler.parser import parse_ability_text as legacy_parse_ability_text
from compiler.parser_compat import parse_ability_text as compat_parse_ability_text
from compiler.parser_v2 import parse_ability_text as v2_parse_ability_text
from engine.models.ability import Ability, Effect, EffectType, TriggerType
from engine.models.ability_descriptions import EFFECT_DESCRIPTIONS_JP, TRIGGER_DESCRIPTIONS_JP
from engine.models.ability_rendering import reconstruct_text


class AbilityRefactorCoverageTests(unittest.TestCase):
    def test_parser_entrypoints_stay_in_sync(self) -> None:
        text = "TRIGGER: ON_PLAY\nEFFECT: DRAW(1)"

        legacy_abilities = legacy_parse_ability_text(text)
        compat_abilities = compat_parse_ability_text(text)
        v2_abilities = v2_parse_ability_text(text)

        self.assertEqual(len(legacy_abilities), 1)
        self.assertEqual(len(compat_abilities), 1)
        self.assertEqual(len(v2_abilities), 1)

        self.assertEqual(legacy_abilities[0].trigger, TriggerType.ON_PLAY)
        self.assertEqual(compat_abilities[0].trigger, TriggerType.ON_PLAY)
        self.assertEqual(v2_abilities[0].trigger, TriggerType.ON_PLAY)

        self.assertEqual(len(legacy_abilities[0].effects), 1)
        self.assertEqual(len(compat_abilities[0].effects), 1)
        self.assertEqual(len(v2_abilities[0].effects), 1)

    def test_japanese_description_strings_remain_intact(self) -> None:
        ability = Ability(
            raw_text="TRIGGER: ON_PLAY\nEFFECT: DRAW(2)",
            trigger=TriggerType.ON_PLAY,
            effects=[Effect(EffectType.DRAW, 2)],
        )

        self.assertTrue(TRIGGER_DESCRIPTIONS_JP[TriggerType.ON_PLAY])
        self.assertTrue(EFFECT_DESCRIPTIONS_JP[EffectType.DRAW].startswith("{value}"))

        semantic = ability.build_semantic_form()
        self.assertEqual(semantic["trigger"], "ON_PLAY")
        self.assertEqual(semantic["description"], "TRIGGER: ON_PLAY\nEFFECT: DRAW(2)")
        self.assertEqual(semantic["effects"][0]["type"], "DRAW")

        rendered = reconstruct_text(ability, lang="jp")
        self.assertTrue(rendered)
        self.assertIn("2", rendered)


if __name__ == "__main__":
    unittest.main()
