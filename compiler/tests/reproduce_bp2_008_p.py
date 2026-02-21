from compiler.parser_v2 import AbilityParserV2
from engine.models.ability import EffectType, TriggerType


def test_bp2_008_p_repro_v2():
    text = "{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}：このメンバーがいるエリアとは別の自分のエリア1つを選ぶ。このメンバーをそのエリアに移動する。選んだエリアにメンバーがいる場合、そのメンバーは、このメンバーがいたエリアに移動させる。"
    parser = AbilityParserV2()
    abilities = parser.parse(text)

    print(f"Parsed {len(abilities)} abilities with V2:")
    for i, abi in enumerate(abilities):
        print(f"  Ability {i}: Trigger={abi.trigger.name}, Text='{abi.raw_text}'")
        for j, eff in enumerate(abi.effects):
            print(f"    Effect {j}: {eff.effect_type.name}")

    # The goal is to have only 1 ability (ACTIVATED)
    assert len(abilities) == 1, f"Expected 1 ability, got {len(abilities)}"
    assert abilities[0].trigger == TriggerType.ACTIVATED

    # It should have the MOVE_MEMBER effects
    has_move = any(e.effect_type == EffectType.MOVE_MEMBER for e in abilities[0].effects)
    assert has_move, "Should have MOVE_MEMBER effect"


if __name__ == "__main__":
    try:
        test_bp2_008_p_repro_v2()
        print("Test PASSED!")
    except Exception as e:
        print(f"Test FAILED: {e}")
