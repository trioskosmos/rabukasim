from __future__ import annotations

import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.append(project_root)

from compiler.parser_v2 import AbilityParserV2
from engine.models.ability import Cost, EffectType
from engine.models.opcodes import Opcode


def _single_effect(text: str):
    parser = AbilityParserV2()
    abilities = parser.parse(text)
    assert len(abilities) == 1, text
    assert len(abilities[0].effects) >= 0
    return abilities[0]


def main() -> None:
    # Trigger / condition routing
    cond_ability = _single_effect("TRIGGER: ON_PLAY\nCONDITION: ALL_MEMBERS {FILTER=\"GROUP_ID=0\"}\nEFFECT: DRAW(1)")
    assert cond_ability.conditions, "expected condition to parse"

    # Effect alias routing
    effect_ability = _single_effect("TRIGGER: ON_PLAY\nEFFECT: MOVE_TO_HAND(1) -> CARD_HAND")
    assert effect_ability.effects[0].effect_type == EffectType.ADD_TO_HAND

    # Grammar convenience routing
    select_mode_ability = _single_effect("TRIGGER: ON_PLAY\nEFFECT: SELECT_OPTION(1) -> PLAYER")
    assert select_mode_ability.effects[0].effect_type == EffectType.SELECT_MODE

    # Semantic special case routing
    reveal_ability = _single_effect(
        'TRIGGER: ON_PLAY\nEFFECT: LOOK_AND_CHOOSE_REVEAL(3) {FILTER="TYPE_LIVE"} -> CARD_HAND'
    )
    assert reveal_ability.effects[0].effect_type == EffectType.LOOK_AND_CHOOSE

    # Cost routing
    cost_ability = _single_effect("TRIGGER: ON_LIVE_SUCCESS\nCOST: PLACE_ENERGY_WAIT(1) (Optional)\nEFFECT: DRAW(1)")
    cost_steps = [step for step in cost_ability.instructions if isinstance(step, Cost)]
    assert any(c.params.get("wait") for c in cost_steps), "expected wait flag on optional energy placement"
    assert Opcode.PLACE_ENERGY_FROM_DECK == 39

    print("parser smoke checks passed")


if __name__ == "__main__":
    main()
