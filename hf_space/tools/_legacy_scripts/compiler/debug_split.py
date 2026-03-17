import os
import sys

# Add project root to path
if __name__ == "__main__":
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from compiler.parser_v2 import AbilityParserV2


def test_split():
    parser = AbilityParserV2()

    # Actual text for PL!N-pb1-004-P＋
    text = "{{jyouji.png|常時}}このターンにこのメンバーが移動していない場合、このメンバーのライブP＋2。{{live_start.png|ライブ開始時}}自分のデッキの一番上のカードを公開する。そのカードが{{icon_blade.png|ブレード}}を持つ場合、このメンバーとチェンジする。それ以外の場合、公開したカードを控え室に置く。{{live_success.png|ライブ成功時}}カードを1枚引く。"

    print(f"Original Text:\n{text}")
    print("-" * 20)

    sentences = parser._split_sentences(text)
    print(f"Sentences ({len(sentences)}):")
    for i, s in enumerate(sentences):
        print(f"{i}: {s}")
        print(f"   is_continuation: {parser._is_continuation(s, i)}")

    print("-" * 20)
    abilities = parser.parse(text)
    print(f"Parsed Abilities: {len(abilities)}")
    for i, ab in enumerate(abilities):
        print(f"Ability {i}: Trigger={ab.trigger}")
        print(f"   Raw: {ab.raw_text}")


if __name__ == "__main__":
    test_split()
