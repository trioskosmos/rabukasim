from compiler.parser_v2 import AbilityParserV2


def debug_sd1_006():
    parser = AbilityParserV2()
    text = "{{toujyou.png|登場}}手札のライブカードを1枚公開してもよい：自分の成功ライブカード置き場にあるカードを1枚手札に加える。そうした場合、これにより公開したカードを自分の成功ライブカード置き場に置く。"

    print(f"Parsing: {text}")
    print("-" * 50)

    # Manually split to see what parser_v2 sees
    sentences = parser._split_sentences(parser._preprocess(text))
    print(f"Sentences: {sentences}")

    parsed = parser.parse(text)

    print("\nParsed Abilities:")
    for i, ab in enumerate(parsed):
        print(f"Ability {i}:")
        print(f"  Raw: {ab.raw_text}")
        print(f"  Trigger: {ab.trigger}")
        print(f"  Effects: {len(ab.effects)}")
        for eff in ab.effects:
            print(f"    - Type: {eff.effect_type}")
            print(f"      Val: {eff.value}")
            print(f"      Params: {eff.params}")


if __name__ == "__main__":
    debug_sd1_006()
