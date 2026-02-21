from compiler.parser_v2 import AbilityParserV2
from engine.models.ability import EffectType


def test_sd1_006():
    parser = AbilityParserV2()
    text = "{{toujyou.png|登場}}手札のライブカードを1枚公開してもよい：自分の成功ライブカード置き場にあるカードを1枚手札に加える。そうした場合、これにより公開したカードを自分の成功ライブカード置き場に置く。"

    print(f"Parsing: {text}")
    print("-" * 50)

    parsed = parser.parse(text)

    print("\nParsed Effects:")
    for ability in parsed:
        for effect in ability.effects:
            print(f"Effect: {effect.effect_type}")
            print(f"Params: {effect.params}")
            print("-" * 30)

    # Check if RECOVER_LIVE is present
    has_recover = any(e.effect_type == EffectType.RECOVER_LIVE for ab in parsed for e in ab.effects)
    if has_recover:
        print("\nSUCCESS: RECOVER_LIVE found.")
    else:
        print("\nFAILURE: RECOVER_LIVE not found.")


if __name__ == "__main__":
    test_sd1_006()
