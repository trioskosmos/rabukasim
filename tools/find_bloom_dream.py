import json

# Search for "bloom" or "dream" in cards.json
with open('data/cards.json', 'r', encoding='utf-8') as f:
    cards = json.load(f)

print("Searching for 'bloom' or 'dream' in cards.json...")
for card_no, card in cards.items():
    ability = card.get('ability', '')
    name = card.get('name', '')
    if 'bloom' in ability.lower() or 'dream' in ability.lower() or 'bloom' in name.lower() or 'dream' in name.lower():
        print(f"\nCard: {name} ({card_no})")
        print(f"Ability: {ability}")

# Search for "bloom" or "dream" in ability_frame_source.json
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("\n\nSearching for 'bloom' or 'dream' in ability_frame_source.json...")
for i, ability in enumerate(data['abilities']):
    primary_text = ability.get('primary_text_jp', '')
    if 'bloom' in primary_text.lower() or 'dream' in primary_text.lower():
        print(f"\nAbility index {i}")
        print(f"Primary text: {primary_text[:200]}")
