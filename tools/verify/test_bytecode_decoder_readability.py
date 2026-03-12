from engine.models.ability import Ability, Condition, Effect, explain_filter_attr, format_filter_attr
from engine.models.generated_enums import ConditionType, EffectType, TargetType, TriggerType
from tools.verify.bytecode_decoder import decode_bytecode


def test_any_stage_filter_summary_uses_named_fields():
    ability = Ability(raw_text="test", trigger=TriggerType.CONSTANT, effects=[])
    condition = Condition(type=ConditionType.COUNT_STAGE, params={"filter": "COST_GE_13", "area": "ANY_STAGE"})

    packed_attr = ability._pack_filter_attr(condition)
    explained = explain_filter_attr(packed_attr)

    assert explained["target_player"] == 3
    assert explained["value_threshold"] == 13
    assert explained["is_cost_type"] is True
    assert "target=both" in format_filter_attr(packed_attr)
    assert "cost>=13" in format_filter_attr(packed_attr)


def test_decoder_renders_named_filter_summary_for_compiled_condition():
    condition = Condition(type=ConditionType.COUNT_STAGE, params={"filter": "COST_GE_13", "area": "ANY_STAGE"}, value=1)
    effect = Effect(effect_type=EffectType.ADD_BLADES, value=2, target=TargetType.SELF)
    ability = Ability(raw_text="test", trigger=TriggerType.CONSTANT, effects=[effect], conditions=[condition])

    decoded = decode_bytecode(ability.compile())

    assert "target=both" in decoded
    assert "cost>=13" in decoded