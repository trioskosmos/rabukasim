import os
import sys

# Add project root to sys.path
sys.path.append(os.getcwd())

from compiler.parser_v2 import AbilityParserV2


def debug():
    parser = AbilityParserV2()
    text = "TRIGGER: ON_LIVE_START\nEFFECT: SELECT_MODE(1) -> PLAYER\n  OPTION: チョコミント/ストロベリー/クッキー＆クリーム | EFFECT: DISCARD_HAND(1) -> PLAYER; DISCARD_HAND(1) -> OPPONENT\n  OPTION: あなた | EFFECT: DRAW(1) -> PLAYER; DRAW(1) -> OPPONENT\n  OPTION: その他 | EFFECT: BUFF_POWER(1) -> PLAYER; BUFF_POWER(1) -> OPPONENT"
    try:
        abilities = parser.parse(text)
        print("Successfully parsed!")
    except Exception:
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    debug()
