import json

with open('data/cards_compiled.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

card = data['live_db']['207']
ab = card['abilities'][0]  # First ability (ADD_TAG one)
eff = ab['effects'][0]
tag = eff['params'].get('tag')

print("=== Card 207 First Ability ===")
print(f"Ability trigger: {ab['trigger']}")  # Should be 6 (CONSTANT)
print(f"Effect type: {eff['effect_type']}")  # Should be 29 (META_RULE)
print(f"Tag value: {repr(tag)}")
print(f"Tag bytes: {tag.encode('utf-8') if tag else 'None'}")

# Now test the matching logic
token_to_unit = {
    "UNIT_CERISE": 13,
    "UNIT_DOLL": 14,
    "UNIT_MIRAKURA": 15,
}

print("\n=== Matching Logic ===")
raw = str(tag).strip() if tag else ""
print(f"After strip: {repr(raw)}")

# Check for quotes
has_start_quote = raw.startswith('"')
has_end_quote = raw.endswith('"')
print(f"Starts with \": {has_start_quote}")
print(f"Ends with \": {has_end_quote}")

if has_start_quote and has_end_quote:
    raw = raw[1:-1]
    print(f"After quote removal: {repr(raw)}")

found_units = set()
for key, val in token_to_unit.items():
    match = key in raw
    print(f"  '{key}' in raw: {match}")
    if match:
        found_units.add(val)

print(f"\nFinal units: {sorted(found_units)}")
print(f"Card units field: {card.get('units', [])}")
