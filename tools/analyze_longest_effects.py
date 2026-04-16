#!/usr/bin/env python3
"""
Find longest costless_text and explain how it's parsed.
This script reads: data/simple_effects_extracted.json
"""

import json

with open('data/simple_effects_extracted.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Find longest costless_text
longest = max(data, key=lambda x: len(x['costless_text']))

print("=" * 80)
print("LONGEST COSTLESS_TEXT")
print("=" * 80)
print(f"Length: {len(longest['costless_text'])} characters")
print(f"Text: {longest['costless_text']}")
print(f"\nParsed: {longest['parsed']}")
print(f"\nTriggers: {longest['triggers']}")
print(f"Card count: {longest['card_count']}")

# Count lines in parse_backwards function
with open('tools/ability_extraction/extract_simple_effects.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("\n" + "=" * 80)
print("CODE EXPLANATION")
print("=" * 80)
print("The parse_backwards function works as follows:")
print("1. Removes the final period (。)")
print("2. Iterates through action_patterns dict to find matching action verb")
print("3. Splits text at action to get context (everything before the action)")
print("4. Calls parse_context_backwards() on the context")
print("5. parse_context_backwards() uses regex and string matching to extract variables:")
print("   - count (e.g., '1枚', '2枚')")
print("   - max (e.g., '1枚まで')")
print("   - source (e.g., '控え室' → waitroom, 'デッキ' → deck)")
print("   - card_type (e.g., 'ライブカード' → live_card)")
print("   - group (e.g., '『虹ヶ咲』' → 虹ヶ咲)")
print("   - cost_limit (e.g., 'コスト2以下' or '2コスト以下' → 2)")
print("   - target (e.g., '相手' → opponent, '自分' → self)")

print(f"\nTotal lines in extract_simple_effects.py: {len(lines)}")
print(f"parse_backwards function: ~35 lines")
print(f"parse_context_backwards function: ~30 lines")
