import os
import sys

sys.path.append(os.getcwd())

from compiler.parser_v2 import AbilityParserV2


def test_audit_card_0():
    parser = AbilityParserV2()

    # Corrected Pseudocode for Card 0, Ability 2
    # Based on Japanese text: You may discard 3 specific cards... Boost score by 3 until end of live.
    corrected_pcode = """TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(3) {NAMES=["上原歩夢", "澁谷かのん", "日野下花帆"]} (Optional)
EFFECT: BOOST_SCORE(3) -> PLAYER {UNTIL=LIVE_END}"""

    abilities = parser.parse(corrected_pcode)
    ab = abilities[0]
    new_bytecode = ab.compile()

    # Original Bytecode from cards_compiled.json for Card 0, Ability 2
    original_bytecode = [21, 3, 0, 1, 18, 1, 0, 7, 16, 3, 0, 7, 21, 1, 0, 7, 1, 0, 0, 0]

    print(f"Original BC: {original_bytecode}")
    print(f"Corrected BC: {new_bytecode}")

    if new_bytecode == original_bytecode:
        print("MATCH")
    else:
        print("MISMATCH")
        print(f"Lengths: Orig={len(original_bytecode)}, New={len(new_bytecode)}")


if __name__ == "__main__":
    test_audit_card_0()
