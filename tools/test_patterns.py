#!/usr3/env python3
"""
Test key DSL_PATTERNS regex individually to identify errors.
"""

import re

# Test key patterns directly
test_patterns = [
    (r"\{\{[^}]+\}", "icon_trigger"),
    (r"\{\{[^}]+\}\}+", "icon_energy_payment"),
    (r"常時", "duration_permanent"),
    (r"ライブ終了時まで", "duration_end_live"),
    (r"このターン", "duration_end_turn"),
    (r"ライブ終了まで、\{\{[^}]+\}を得る", "duration_gain_with_icon"),
    (r"てもよい", "optional"),
    (r"カードを(\d+)枚引く", "draw_cards"),
    (r"([^。]+)を([^。]+)に置く", "discard_to_zone"),
    (r"([^。]+)を([^。]+)に加える", "add_to_zone"),
    (r"自分の控え室からライブカードを(\d+)枚手札に加える", "add_live_card_from_discard"),
    (r"自分の控え室からメンバーカードを(\d+)枚手札に加える", "add_member_card_from_discard"),
    (r"([^。]+)に([^。]+)がいる場合、([^。]+)", "conditional_presence"),
    (r"([^。]+)に『([^』]+)』のメンバーがいる場合、([^。]+)", "conditional_group_presence"),
    (r"([^。]+)を([^。]+)に置いてもよい：([^。]+)", "cost_effect"),
    (r"([^。]+)とき、([^。]+)", "trigger_timing"),
    (r"([^。]+)(\d+)枚につき、([^。]+)", "per_unit"),
    (r".+", "catchall_any"),
]

print("Testing key patterns...")
errors = []
for regex_str, name in test_patterns:
    try:
        re.compile(regex_str)
        print(f"OK: {name}")
    except re.error as e:
        print(f"ERROR: {name} - {e}")
        errors.append((name, str(e)))

if errors:
    print(f"\nFound {len(errors)} errors")
else:
    print("\nAll patterns compiled successfully!")

# Load abilities and test pattern matching
with open('data/abilities_extracted.json', encoding='utf-8') as f:
    abilities = json.load(f)

print(f"\nTesting pattern matching on {len(abilities)} abilities...")
pattern_matches = {}

for ability in abilities:
    for clause in ability['clauses']:
        for regex_str, name in test_patterns:
            try:
                if re.search(regex_str, clause):
                    if name not in pattern_matches:
                        pattern_matches[name] = 0
                    pattern_matches[name] += 1
                    break
            except re.error as e:
                errors.append((name, str(e)))

print(f"\nPattern match results:")
for name, count in sorted(pattern_matches.items(), key=lambda x: -x[1]):
    print(f"  {name}: {count}")

print(f"\nTotal matched: {sum(pattern_matches.values())}")
print(f"Total clauses: {sum(len(a['clauses']) for a in abilities)}")
