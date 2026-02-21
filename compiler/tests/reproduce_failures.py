import os
import sys
from dataclasses import dataclass
from typing import List

# Add project root to path
if __name__ == "__main__":
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from compiler.parser_v2 import AbilityParserV2


@dataclass
class ExpectedAbility:
    trigger: str
    effects: List[str]  # Just types for simple check, or dicts for detailed
    costs: List[str] = None
    conditions: List[str] = None
    effect_values: List[int] = None  # Optional: check values of effects in order


def check_parser_strict(text: str, expected: ExpectedAbility, name: str = "") -> bool:
    parser = AbilityParserV2()
    print(f"Test: {name}")
    try:
        abilities = parser.parse(text)
        if not abilities:
            print("  FAILURE: No abilities parsed")
            return False

        ab = abilities[0]  # Assuming single ability

        # Verify Trigger
        if ab.trigger.name != expected.trigger:
            print(f"  FAILURE: Trigger mismatch. Expected {expected.trigger}, got {ab.trigger.name}")
            return False

        # Verify Effects
        actual_effects = [e.effect_type.name for e in ab.effects]
        missing_effects = [e for e in expected.effects if e not in actual_effects]
        if missing_effects:
            print(f"  FAILURE: Missing effects. Expected {expected.effects}, got {actual_effects}")
            return False

        # Verify Effect Values
        if expected.effect_values:
            actual_values = [e.value for e in ab.effects]
            # Check length first
            if len(actual_values) < len(expected.effect_values):
                print(
                    f"  FAILURE: Effect value count mismatch. Expected {len(expected.effect_values)}, got {len(actual_values)}"
                )
                return False

            for i, val in enumerate(expected.effect_values):
                if actual_values[i] != val:
                    print(f"  FAILURE: Effect value mismatch at index {i}. Expected {val}, got {actual_values[i]}")
                    return False

        # Verify Costs
        if expected.costs:
            actual_costs = [c.type.name for c in ab.costs]
            missing_costs = [c for c in expected.costs if c not in actual_costs]
            if missing_costs:
                print(f"  FAILURE: Missing costs. Expected {expected.costs}, got {actual_costs}")
                return False

        print("  SUCCESS")
        return True

    except Exception as e:
        import traceback

        traceback.print_exc()
        print(f"  ERROR: {e}")
        return False


def run_tests():
    tests = [
        (
            "Mill Effect (PL!-sd1-007-SD)",
            "{{toujyou.png|登場}}自分のデッキの上からカードを5枚控え室に置く。",
            ExpectedAbility(
                trigger="ON_PLAY",
                effects=["SWAP_CARDS"],
                effect_values=[5],  # Should be 5
            ),
        ),
        (
            "Reveal Cost (PL!-sd1-006-SD)",
            "{{toujyou.png|登場}}手札のライブカードを1枚公開してもよい：自分の成功ライブカード置き場にあるカードを1枚手札に加える。",
            ExpectedAbility(trigger="ON_PLAY", effects=["RECOVER_LIVE"], costs=["REVEAL_HAND"]),
        ),
        (
            "Optional Cost (PL!-sd1-003-SD)",
            "{{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：{{heart_01.png|heart01}}か{{heart_03.png|heart03}}か{{heart_06.png|heart06}}のうち、1つを選ぶ。",
            ExpectedAbility(trigger="ON_LIVE_START", effects=["SELECT_MODE"], costs=["DISCARD_HAND"]),
        ),
        (
            "Swap 10 Cards (PL!-sd1-008-SD)",
            "{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分のデッキの上からカードを10枚控え室に置く。",
            ExpectedAbility(trigger="ACTIVATED", effects=["SWAP_CARDS"], costs=["ENERGY"], effect_values=[10]),
        ),
        (
            "Search Deck (Generic)",
            "{{toujyou.png|登場}}自分のデッキから『μ's』のメンバーカードを1枚まで手札に加える。デッキをシャッフルする。",
            ExpectedAbility(
                trigger="ON_PLAY",
                effects=["SEARCH_DECK", "META_RULE"],
            ),
        ),
        (
            "Score Boost",
            "{{jyouji.png|常時}}ライブの合計スコアを＋1する。",
            ExpectedAbility(trigger="CONSTANT", effects=["BOOST_SCORE"], effect_values=[1]),
        ),
        (
            "Add Blades",
            "{{live_start.png|ライブ開始時}}{{icon_blade.png|ブレード}}を1つ得る。",
            ExpectedAbility(trigger="ON_LIVE_START", effects=["ADD_BLADES"], effect_values=[1]),
        ),
        (
            "Recover Member",
            "{{toujyou.png|登場}}自分の控え室からメンバーカードを1枚まで手札に加える。",
            ExpectedAbility(trigger="ON_PLAY", effects=["RECOVER_MEMBER"], effect_values=[1]),
        ),
        (
            "Recover Live",
            "{{toujyou.png|登場}}自分の控え室からライブカードを1枚まで手札に加える。",
            ExpectedAbility(trigger="ON_PLAY", effects=["RECOVER_LIVE"], effect_values=[1]),
        ),
    ]

    print(f"Running {len(tests)} parser tests...")
    print("=" * 60)

    passed = 0
    failed = 0

    for name, text, expected in tests:
        if check_parser_strict(text, expected, name):
            passed += 1
        else:
            failed += 1

    print("=" * 60)
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
