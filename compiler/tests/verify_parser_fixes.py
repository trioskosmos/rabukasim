import os
import sys

# Add project root to sys.path
sys.path.append(os.getcwd())

from compiler.parser_v2 import AbilityParserV2
from engine.models.ability import EffectType, TargetType, TriggerType


def test_negation():
    parser = AbilityParserV2()
    text = "TRIGGER: ON_PLAY\nCONDITION: !MOVED_THIS_TURN\nEFFECT: DRAW(1)"
    abilities = parser.parse(text)
    ability = abilities[0]
    condition = ability.conditions[0]
    print(f"Condition: {condition.type.name}, Negated: {condition.is_negated}")
    assert condition.is_negated == True


def test_variable_targeting():
    parser = AbilityParserV2()
    # Sequence: Look Deck to Hand -> Draw for Target
    text = "TRIGGER: ON_PLAY\nEFFECT: LOOK_DECK(3) -> CARD_HAND; DRAW(1) -> TARGET"
    abilities = parser.parse(text)
    effects = abilities[0].effects
    print(f"Effect 0 Target: {effects[0].target.name}")
    print(f"Effect 1 Target: {effects[1].target.name}")
    assert effects[1].target == TargetType.CARD_HAND


def test_aliases():
    parser = AbilityParserV2()
    text = "TRIGGER: ON_YELL_SUCCESS\nEFFECT: CHARGE_SELF(1)"
    abilities = parser.parse(text)
    ability = abilities[0]
    print(f"Trigger: {ability.trigger.name}")
    print(f"Effect: {ability.effects[0].effect_type.name}, Target: {ability.effects[0].target.name}")
    assert ability.trigger == TriggerType.ON_REVEAL
    assert ability.effects[0].effect_type == EffectType.ENERGY_CHARGE
    assert ability.effects[0].target == TargetType.MEMBER_SELF


if __name__ == "__main__":
    try:
        test_negation()
        test_variable_targeting()
        test_aliases()
        print("All tests passed!")
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback

        traceback.print_exc()
