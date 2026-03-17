import os
import sys

# Ensure project root is in path
sys.path.insert(0, os.getcwd())

from compiler.parser import AbilityParser
from engine.models.ability import ConditionType, EffectType, TriggerType


def test_honoka():
    text = "【登場時】自分の成功ライブカード置き場にカードが2枚以上ある場合、自分の控え室からライブカードを1枚手札に加える。"
    abilities = AbilityParser.parse_ability_text(text)
    print(f"Honoka parsed: {len(abilities)} abilities")
    for abi in abilities:
        print(f"  Trigger: {abi.trigger}")
        print(f"  Conditions: {[c.type.name for c in abi.conditions]}")
        print(f"  Effects: {[e.effect_type.name for e in abi.effects]}")

    assert len(abilities) == 1
    assert abilities[0].trigger == TriggerType.ON_PLAY
    assert len(abilities[0].conditions) == 1
    assert abilities[0].conditions[0].type == ConditionType.COUNT_SUCCESS_LIVE
    assert len(abilities[0].effects) == 1
    assert abilities[0].effects[0].effect_type == EffectType.RECOVER_LIVE
    print("Honoka test passed!")


def test_ginko():
    text = "【登場時】手札を1枚捨ててもよい：そうしたら、デッキの上から5枚見る。その中からメンバーを1枚まで公開し、手札に加える。残りを山札の一番下に望む順番で置く。"
    abilities = AbilityParser.parse_ability_text(text)
    print(f"Ginko parsed: {len(abilities)} abilities")
    abi = abilities[0]
    print(f"  Effects: {[e.effect_type.name for e in abi.effects]}")

    # Check if member filter is captured
    look_and_choose = [e for e in abi.effects if e.effect_type == EffectType.LOOK_AND_CHOOSE][0]
    print(f"  Look and Choose Filter: {look_and_choose.params.get('filter')}")

    assert look_and_choose.params.get("filter") == "member"
    print("Ginko test passed!")


def test_pr033():
    text = "【登場時】山札の上から3枚見る。その中から好きな枚数を好きな順番で山札の上に戻し、残りを控え室に置く。"
    abilities = AbilityParser.parse_ability_text(text)
    print(f"PR-033 parsed: {len(abilities)} abilities")
    abi = abilities[0]
    print(f"  Effects: {[e.effect_type.name for e in abi.effects]}")

    # Expected: 1. LOOK_DECK (3), 2. LOOK_AND_CHOOSE (any_number=True, reorder=True, destination=deck_top, on_fail=discard)
    assert len(abi.effects) == 2
    assert abi.effects[0].effect_type == EffectType.LOOK_DECK
    assert abi.effects[0].value == 3
    assert abi.effects[1].effect_type == EffectType.LOOK_AND_CHOOSE
    params = abi.effects[1].params
    assert params.get("any_number") is True
    assert params.get("reorder") is True
    assert params.get("destination") == "deck_top"
    assert params.get("on_fail") == "discard"
    print("PR-033 test passed!")


def test_mari():
    text = "{{jyouji.png|常時}}自分のステージのエリアすべてに『Aqours』のメンバーが登場しており、かつ名前が異なる場合、「{{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中にライブカードが1枚以上ある場合、ライブの合計スコアを＋１する。ライブカードが3枚以上ある場合、代わりに合計スコアを＋２する。」を得る。"
    abilities = AbilityParser.parse_ability_text(text)
    print(f"Mari parsed: {len(abilities)} abilities")
    # Should identify trigger as ON_LIVE_SUCCESS (3) due to fix
    found_success = any(abi.trigger == TriggerType.ON_LIVE_SUCCESS for abi in abilities)
    assert found_success, "Mari should have ON_LIVE_SUCCESS trigger"
    print("Mari test passed!")


def test_rise_up_high():
    text = "{{live_start.png|ライブ開始時}}このゲームの1ターン目のライブフェイズの場合、このカードのスコアを＋１し、ライブ終了時まで、自分のステージにいる『虹ヶ咲』のメンバー1人は、{{icon_blade.png|ブレード}}を得る。"
    abilities = AbilityParser.parse_ability_text(text)
    print(f"Rise Up High parsed: {len(abilities)} abilities")
    abi = abilities[0]
    effects = [e.effect_type for e in abi.effects]
    assert EffectType.BOOST_SCORE in effects, "Rise Up High should have BOOST_SCORE"
    assert EffectType.MODIFY_SCORE_RULE not in effects, (
        "Rise Up High should NOT have MODIFY_SCORE_RULE (misinterpreting 'gain')"
    )
    print("Rise Up High test passed!")


def test_yume_no_tobira():
    text = "{{live_start.png|ライブ開始時}}自分のデッキの上から、自分と相手のステージにいるメンバー1人につき、1枚公開する。それらの中にあるライブカード1枚につき、このカードのスコアを＋１する。その後、これにより公開したカードを控え室に置く。"
    abilities = AbilityParser.parse_ability_text(text)
    print(f"Yume no Tobira parsed: {len(abilities)} abilities")
    effects = [e.effect_type.name for e in abilities[0].effects]
    assert "REVEAL_CARDS" in effects, "Should reveal cards"
    assert "BOOST_SCORE" in effects, "Should boost score"
    print("Yume no Tobira test passed!")


def test_natsuiro():
    text = "{{live_start.png|ライブ開始時}}自分の成功ライブカード置き場にカードがある場合、{{heart_01.png|heart01}}か{{heart_03.png|heart03}}か{{heart_06.png|heart06}}のうち、1つを選ぶ。ライブ終了時まで、自分のステージにいる『μ's』のメンバー1人は、選んだハートを1つ得る。<br>{{live_start.png|ライブ開始時}}自分の成功ライブカード置き場にカードが2枚以上ある場合、このカードのスコアを＋１する。"
    abilities = AbilityParser.parse_ability_text(text)
    print(f"Natsuiro parsed: {len(abilities)} abilities")
    assert len(abilities) == 2, f"Should have 2 abilities, got {len(abilities)}"

    eff1 = [e.effect_type.name for e in abilities[0].effects]
    assert "SELECT_MODE" in eff1, "Ability 1 should have SELECT_MODE"
    assert "ADD_HEARTS" in eff1, "Ability 1 should have ADD_HEARTS"

    eff2 = [e.effect_type.name for e in abilities[1].effects]
    assert "BOOST_SCORE" in eff2, "Ability 2 should have BOOST_SCORE"
    assert "ADD_HEARTS" not in eff2, "Ability 2 should NOT have ADD_HEARTS"
    print("Natsuiro test passed!")


if __name__ == "__main__":
    tests = [
        ("Honoka", test_honoka),
        ("Ginko", test_ginko),
        ("PR-033", test_pr033),
        ("Mari", test_mari),
        ("Rise Up High", test_rise_up_high),
        ("Yume no Tobira", test_yume_no_tobira),
        ("Natsuiro", test_natsuiro),
    ]
    passed = 0
    for name, func in tests:
        try:
            print(f"--- Running {name} test ---")
            func()
            passed += 1
        except Exception as e:
            print(f"--- {name} test FAILED ---")
            print(f"Error: {e}")
            # traceback.print_exc()

    print(f"\nSummary: {passed}/{len(tests)} passed.")
    if passed == len(tests):
        print("ALL PARSER DIAGNOSTICS PASSED!")
    else:
        sys.exit(1)
