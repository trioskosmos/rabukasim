"""Test unit token matching logic"""

# Exact strings from compiled JSON
tag_str_raw = '"UNIT_CERISE/UNIT_DOLL/UNIT_MIRAKURA"'

print("=== Test Unit Matching ===")
print(f"Raw tag_str: {tag_str_raw}")

# Process like in the code
raw = str(tag_str_raw).strip()
print(f"After strip: {raw}")

if (raw.startswith('"') and raw.endswith('"')) or (raw.startswith("'") and raw.endswith("'")):
    raw = raw[1:-1]
    
print(f"After quote removal: {raw}")

token_to_unit = {
    "UNIT_CERISE": 13,
    "UNIT_DOLL": 14,
    "UNIT_MIRAKURA": 15,
}

found_units = set()
for key, val in token_to_unit.items():
    is_match = key in raw
    print(f"  '{key}' in '{raw}': {is_match}")
    if is_match:
        found_units.add(val)

print(f"\nFinal found_units: {sorted(found_units)}")
print(f"Expected: [13, 14, 15]")
print(f"Match: {sorted(found_units) == [13, 14, 15]}")
