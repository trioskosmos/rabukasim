from compiler.patterns.effects import EFFECT_PATTERNS


def _get_pattern(patterns, name):
    return next((p for p in patterns if p.name == name), None)


test_cases = [
    # Draw patterns
    ("draw_cards", "カードを2枚引く", True),
    ("draw_cards", "カードを３枚引く", True),
    ("draw_one", "引く", True),
    ("draw_one", "引き入れる", False),  # Excluded
    # Blade patterns (with verbose regex)
    ("add_blades", "ブレード+1", True),
    ("add_blades", "ブレード＋２", True),
    ("add_blades", "ブレード＋３", True),
    ("add_blades", "ブレードスコア場合", False),  # Excluded context
    # Heart patterns (with verbose regex)
    ("add_hearts", "ハート+1", True),
    ("add_hearts", "ハート＋２", True),
    # Recovery patterns
    ("recover_member", "控え室から手札に加える", True),
    ("recover_live", "控え室からライブカードを手札に加える", True),
    # Look patterns
    ("look_deck_top", "デッキの一番上を見る", True),
    ("look_deck", "デッキを3枚見て", True),
    # New patterns (gap coverage)
    ("recover_from_success_zone", "成功ライブカード置き場から手札に加える", True),
    ("play_from_hand", "手札からステージに出す", True),
]

failed = False
print("Running manual test_effect_matches...")
for name, text, should_match in test_cases:
    pattern = _get_pattern(EFFECT_PATTERNS, name)
    if pattern is None:
        print(f"ERROR: Pattern '{name}' not found")
        failed = True
        continue

    match = pattern.matches(text)
    matched = bool(match)
    if matched != should_match:
        print(f"FAIL: {name} on '{text}' -> Got {matched}, Expected {should_match}")
        failed = True
    else:
        # print(f"PASS: {name} on '{text}'")
        pass

if not failed:
    print("ALL TESTS PASSED")
else:
    print("SOME TESTS FAILED")
