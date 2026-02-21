from compiler.parser_v2 import AbilityParserV2


def run_debug():
    with open("debug_output.txt", "w", encoding="utf-8") as f:
        parser = AbilityParserV2()
        text = "自分の成功ライブカード置き場にあるカードを1枚手札に加える。"

        f.write(f"Input text repr: {repr(text)}\n")

        # Manually invoke extraction to test registry
        results = parser.registry.match_all(
            text,
            parser.registry.get_patterns(parser.registry._patterns[list(parser.registry._patterns.keys())[2]].phase)[
                0
            ].phase,
        )
        # Accessing PatternPhase.EFFECT safely

        from compiler.patterns.base import PatternPhase

        results = parser.registry.match_all(text, PatternPhase.EFFECT)

        f.write(f"Matches found: {len(results)}\n")
        for p, m, d in results:
            f.write(f"Matched: {p.name}\n")

        # Check specific pattern
        patterns = parser.registry.get_patterns(PatternPhase.EFFECT)
        target = next((p for p in patterns if p.name == "recover_from_success"), None)
        if target:
            f.write(f"Target pattern found: {target.name}\n")
            f.write(f"Target keywords: {target.keywords}\n")
            f.write(f"Target regex: {target.regex}\n")
            m = target.matches(text)
            f.write(f"Target match result: {m}\n")
        else:
            f.write("Target pattern NOT found in registry.\n")


if __name__ == "__main__":
    run_debug()
