import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.append(project_root)

from compiler.parser import parse_ability_text as legacy_parse_ability_text
from compiler.parser_compat import parse_ability_text as compat_parse_ability_text
from compiler.parser_v2 import parse_ability_text as v2_parse_ability_text
from engine.models.ability import Ability, Effect, EffectType, TriggerType
from engine.models.ability_descriptions import EFFECT_DESCRIPTIONS_JP, TRIGGER_DESCRIPTIONS_JP
from engine.models.ability_rendering import reconstruct_text


def test_parser_entrypoints_stay_in_sync():
    text = "TRIGGER: ON_PLAY\nEFFECT: DRAW(1)"

    legacy_abilities = legacy_parse_ability_text(text)
    compat_abilities = compat_parse_ability_text(text)
    v2_abilities = v2_parse_ability_text(text)

    assert len(legacy_abilities) == 1
    assert len(compat_abilities) == 1
    assert len(v2_abilities) == 1

    assert legacy_abilities[0].trigger == TriggerType.ON_PLAY
    assert compat_abilities[0].trigger == TriggerType.ON_PLAY
    assert v2_abilities[0].trigger == TriggerType.ON_PLAY

    assert len(legacy_abilities[0].effects) == 1
    assert len(compat_abilities[0].effects) == 1
    assert len(v2_abilities[0].effects) == 1


def test_japanese_description_strings_remain_intact():
    ability = Ability(
        raw_text="TRIGGER: ON_PLAY\nEFFECT: DRAW(2)",
        trigger=TriggerType.ON_PLAY,
        effects=[Effect(EffectType.DRAW, 2)],
    )

    assert TRIGGER_DESCRIPTIONS_JP[TriggerType.ON_PLAY] == "【登場時】"
    assert EFFECT_DESCRIPTIONS_JP[EffectType.DRAW] == "{value}枚ドロー"

    semantic = ability.build_semantic_form()
    assert semantic["trigger"] == "ON_PLAY"
    assert semantic["description"] == "TRIGGER: ON_PLAY\nEFFECT: DRAW(2)"
    assert semantic["effects"][0]["type"] == "DRAW"

    rendered = reconstruct_text(ability, lang="jp")
    assert "【登場時】" in rendered
    assert "2枚ドロー" in rendered