import json
import re

# Load master DB
with open('data/cards_compiled.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

card_map = {}
for cid, card in data.get('member_db', {}).items():
    card_map[card['card_no']] = card['card_id']
for cid, card in data.get('live_db', {}).items():
    card_map[card['card_no']] = card['card_id']

# Extract all card nos from test_helpers.rs
with open('engine_rust_src/src/test_helpers.rs', 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern for card_no strings
nos = re.findall(r'"(PL![^"]+)"', content)
nos = sorted(list(set(nos)))

print("--- Mapping All Revealed Card Nos in test_helpers.rs ---")
for no in nos:
    official_id = card_map.get(no, 'MISSING')
    print(f"{no} -> {official_id}")
