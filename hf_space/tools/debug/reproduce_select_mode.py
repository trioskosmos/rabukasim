import os
import sys

sys.path.append(os.getcwd())

from compiler.parser_v2 import AbilityParserV2


def test_select_mode_parsing():
    parser = AbilityParserV2()

    # Exact pseudocode from the failure report (Card 310)
    text = """TRIGGER: ON_LIVE_START
EFFECT: SELECT_MODE(1) -> SELF {{"options_text": ["自分", "相手"]}}
    Options:
      1: MOVE_TO_DECK(1)->SELF {TO=DECK_BOTTOM}
      2: MOVE_TO_DECK(1)->OPPONENT {TO=DECK_BOTTOM}"""

    print("--- Input Text ---")
    print(text)
    print("------------------")

    abilities = parser.parse(text)

    if not abilities:
        print("FAIL: No abilities parsed.")
        return

    ab = abilities[0]
    print(f"Parsed Ability Trigger: {ab.trigger}")
    print(f"Effects Count: {len(ab.effects)}")

    if not ab.effects:
        print("FAIL: No effects found.")
        return

    eff = ab.effects[0]
    print(f"Effect Type: {eff.effect_type}")
    print(f"Modal Options Present: {bool(eff.modal_options)}")

    if eff.modal_options:
        print(f"Option Count: {len(eff.modal_options)}")
        for i, opt in enumerate(eff.modal_options):
            print(f"  Option {i + 1}: {[e.effect_type.name for e in opt]}")
    else:
        print("FAIL: Modal options not attached!")

    # Check compilation
    bytecode = ab.compile()
    print(f"Compiled Bytecode: {bytecode}")

    expected_header_start = [30, 2]  # SELECT_MODE, 2 Options
    if bytecode[:2] == expected_header_start:
        print("SUCCESS: Bytecode header matches SELECT_MODE with 2 options.")
    else:
        print(f"FAIL: Bytecode header mismatch. Expected {expected_header_start}, got {bytecode[:2]}")


if __name__ == "__main__":
    test_select_mode_parsing()
