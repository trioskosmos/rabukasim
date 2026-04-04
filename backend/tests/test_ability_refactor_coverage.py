import os
import sys
import unittest

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.append(project_root)

from compiler.parser import parse_ability_text as legacy_parse_ability_text
from compiler.parser_compat import parse_ability_text as compat_parse_ability_text
from compiler.parser_v2 import parse_ability_text as v2_parse_ability_text
from engine.compiler.semantic_processor import populate_semantic_from_frames
from engine.models.ability import Ability, Effect, EffectType, TriggerType
from engine.models.generated_enums import AbilityCostType, ConditionType
from engine.models.ability_descriptions import EFFECT_DESCRIPTIONS_JP, TRIGGER_DESCRIPTIONS_JP


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
        self.assertIn(EffectType.DRAW, EFFECT_DESCRIPTIONS_JP)

    def test_semantic_processor_preserves_bare_opcode_conditions_and_effects(self) -> None:
        ability = Ability(
            raw_text="TRIGGER: ON_PLAY\nEFFECT: DRAW(1)",
            trigger=TriggerType.ON_PLAY,
            effects=[],
            frame_program={
                "frames": [
                    {"opcode": "COUNT_HAND", "value": 2, "is_negated": True},
                    {"opcode": "PAY_ENERGY", "value": 1, "is_cost": True},
                    {"opcode": "ACTIVATE_ENERGY", "value": 1},
                    {"opcode": "LOOK_AND_CHOOSE", "value": 3, "slot": {"target_slot": 6}},
                    {"opcode": "RETURN"},
                ]
            },
        )

        populate_semantic_from_frames([ability], card_no="TST-001")

        self.assertEqual(len(ability.conditions), 1)
        self.assertEqual(ability.conditions[0].type, ConditionType.COUNT_HAND)
        self.assertEqual(ability.conditions[0].value, 2)
        self.assertTrue(ability.conditions[0].is_negated)

        self.assertEqual(len(ability.costs), 1)
        self.assertEqual(ability.costs[0].type, AbilityCostType.ENERGY)
        self.assertEqual(ability.costs[0].value, 1)

        effect_types = [effect.effect_type for effect in ability.effects]
        self.assertIn(EffectType.ACTIVATE_ENERGY, effect_types)
        self.assertIn(EffectType.LOOK_AND_CHOOSE, effect_types)
        self.assertTrue(any(effect.target.name == "CARD_HAND" for effect in ability.effects))


if __name__ == "__main__":
    unittest.main()
