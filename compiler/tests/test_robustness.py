from compiler.parser import AbilityParser


def test_debug_parser():
    parser = AbilityParser()

    cases = [
        ("Slash", "{{toujyou.png|登場}}/{{live_start.png|ライブ開始時}} カードを1枚引く。"),
        ("Parens", "{{toujyou.png|登場}} カードを1枚引く。（これは説明文です。）"),
        ("Modal-", "以下から1回を選ぶ。\\n- カードを1枚引く。\\n- スコア+1。"),
        ("Choose2", "以下から2つを選ぶ。\\n・カードを1枚引く。\\n・スコア+1。\\n・エネチャージ。"),
    ]

    # Just verify that parsing these strings produces valid non-empty ability lists
    # without crashing.
    for name, text in cases:
        print(f"Testing case: {name}")
        abs_list = parser.parse_ability_text(text)
        assert len(abs_list) > 0, f"Failed to parse {name}"

        # Additional sanity checks depending on expected logic
        for a in abs_list:
            assert a.trigger is not None, f"Trigger is None for {name}"
