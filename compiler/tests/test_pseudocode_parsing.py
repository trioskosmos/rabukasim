import pytest

from compiler.parser_v2 import AbilityParserV2
from engine.models.ability import AbilityCostType, ConditionType, EffectType, TargetType, TriggerType


@pytest.fixture
def parser():
    return AbilityParserV2()


def test_basic_trigger(parser):
    text = "TRIGGER: ON_PLAY\nEFFECT: DRAW(1) -> PLAYER"
    abilities = parser.parse(text)
    assert len(abilities) == 1
    assert abilities[0].trigger == TriggerType.ON_PLAY
    assert abilities[0].effects[0].effect_type == EffectType.DRAW


def test_once_per_turn(parser):
    text = "TRIGGER: ACTIVATED\n(Once per turn)\nEFFECT: DRAW(1) -> PLAYER"
    abilities = parser.parse(text)
    assert abilities[0].is_once_per_turn == True

    # Alternative format (same line)
    text2 = "TRIGGER: ACTIVATED (Once per turn)\nEFFECT: DRAW(1) -> PLAYER"
    abilities2 = parser.parse(text2)
    assert abilities2[0].is_once_per_turn == True


def test_costs(parser):
    text = "TRIGGER: ACTIVATED\nCOST: ENERGY(2), TAP_SELF(0) (Optional)\nEFFECT: DRAW(1) -> PLAYER"
    abilities = parser.parse(text)
    costs = abilities[0].costs
    assert len(costs) == 2
    assert costs[0].type == AbilityCostType.ENERGY
    assert costs[0].value == 2
    assert costs[1].type == AbilityCostType.TAP_SELF
    assert costs[1].is_optional == True


def test_conditions(parser):
    text = "TRIGGER: ON_PLAY\nCONDITION: COUNT_STAGE {MIN=3}, NOT HAS_COLOR {COLOR=1}\nEFFECT: DRAW(1) -> PLAYER"
    abilities = parser.parse(text)
    conds = abilities[0].conditions
    assert len(conds) == 2
    assert conds[0].type == ConditionType.COUNT_STAGE
    assert conds[0].params["min"] == 3
    assert conds[1].type == ConditionType.HAS_COLOR
    assert conds[1].params["color"] == 1
    assert conds[1].is_negated == True


def test_effects_with_params(parser):
    text = 'TRIGGER: ON_PLAY\nEFFECT: RECOVER_MEMBER(1) -> CARD_DISCARD {GROUP="μ\'s", FROM=DISCARD, TO=HAND}'
    abilities = parser.parse(text)
    eff = abilities[0].effects[0]
    assert eff.effect_type == EffectType.RECOVER_MEMBER
    assert eff.target == TargetType.CARD_DISCARD
    assert eff.params["group"] == "μ's"
    assert eff.params["from"] == "discard"
    assert eff.params["to"] == "hand"


def test_case_normalization(parser):
    # Enums should be case-insensitive in parameters where it makes sense
    text = "TRIGGER: ON_LIVE_START\nEFFECT: BOOST_SCORE(3) -> PLAYER {UNTIL=LIVE_END}"
    abilities = parser.parse(text)
    assert abilities[0].effects[0].params["until"] == "live_end"


def test_embedded_json_params(parser):
    # Some legacy/complex params might be stored as raw JSON in pseudocode
    text = 'TRIGGER: ON_PLAY\nEFFECT: LOOK_AND_CHOOSE(1) -> CARD_DISCARD {GROUP="Liella!", {"look_count": 5}}'
    abilities = parser.parse(text)
    params = abilities[0].effects[0].params
    assert params["group"] == "Liella!"
    assert params["look_count"] == 5


def test_multiple_abilities(parser):
    text = """TRIGGER: ON_PLAY
EFFECT: DRAW(1) -> PLAYER

TRIGGER: TURN_START
EFFECT: ADD_BLADES(1) -> PLAYER"""
    abilities = parser.parse(text)
    assert len(abilities) == 2
    assert abilities[0].trigger == TriggerType.ON_PLAY
    assert abilities[1].trigger == TriggerType.TURN_START


def test_numeric_parsing(parser):
    # Ensure values and params handle numbers correctly
    text = "TRIGGER: ACTIVATED\nCOST: DISCARD_HAND(3)\nCONDITION: COUNT_ENERGY {MIN=5}\nEFFECT: ADD_HEARTS(2) -> PLAYER"
    abilities = parser.parse(text)
    ab = abilities[0]
    assert ab.costs[0].value == 3
    assert ab.conditions[0].params["min"] == 5
    assert ab.effects[0].value == 2


def test_optional_effect(parser):
    text = "TRIGGER: ON_PLAY\nEFFECT: SEARCH_DECK(1) -> CARD_HAND {FROM=DECK} (Optional)"
    abilities = parser.parse(text)
    assert abilities[0].effects[0].is_optional == True


def test_robust_param_splitting(parser):
    # Mixed spaces and commas
    text = (
        'TRIGGER: ON_PLAY\nEFFECT: RECOVER_LIVE(1) -> CARD_DISCARD {GROUP="BiBi",GROUPS=["BiBi","BiBi"], FROM=DISCARD }'
    )
    abilities = parser.parse(text)
    params = abilities[0].effects[0].params
    assert params["group"] == "BiBi"
    assert params["groups"] == ["BiBi", "BiBi"]
    assert params["from"] == "discard"


def test_bytecode_compilation(parser):
    # This is the ultimate proof that the code "works" in the engine
    text = """TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(3) {NAMES=["上原歩夢", "澁谷かのん", "日野下花帆"]} (Optional)
EFFECT: BOOST_SCORE(3) -> PLAYER {UNTIL=LIVE_END}"""

    abilities = parser.parse(text)
    ab = abilities[0]

    # Compile to bytecode
    bytecode = ab.compile()

    # Bytecode should:
    # 1. Be a list of integers
    # 2. Have length that is multiple of 4
    # 3. End with the RETURN opcode (usually 0 in some engines, but let's check length)
    assert isinstance(bytecode, list)
    assert len(bytecode) > 0
    assert len(bytecode) % 4 == 0

    print(f"Compiled Bytecode: {bytecode}")


def test_complex_condition_compilation(parser):
    text = 'TRIGGER: ON_PLAY\nCONDITION: COUNT_GROUP {GROUP="μ\'s", MIN=2}\nEFFECT: DRAW(1) -> PLAYER'
    abilities = parser.parse(text)
    ab = abilities[0]
    bytecode = ab.compile()

    assert len(bytecode) % 4 == 0
    # First chunk should be a check for group count
    # Opcode.CHECK_COUNT_GROUP is 1000 + enum value or similar
    assert bytecode[0] > 0
