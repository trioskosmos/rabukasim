import json

path = 'data/cards_compiled.json'
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

card = data['live_db']['207']

print("--- Card 207 Final Verification ---")
found = False
for i, ab in enumerate(card.get('abilities', [])):
    for eff_idx, eff in enumerate(ab.get('effects', [])):
        if eff.get('effect_type') == 16: # O_BOOST_SCORE
            attr = eff.get('params', {}).get('A', 0)
            group_enabled = (attr >> 4) & 1
            group_id = (attr >> 5) & 0x7F
            print(f"Ability {i}, Effect {eff_idx} (O_BOOST_SCORE):")
            print(f"  Attribute A: {attr}")
            print(f"  Group Enabled: {group_enabled}")
            print(f"  Group ID: {group_id} (Expected: 4 for Hasunosora)")
            found = True

if not found:
    print("O_BOOST_SCORE not found in card abilities.")

print("\n--- Card 207 Units ---")
print(f"Units: {card.get('units')} (Expected: [13, 14, 15] for Cerise Bouquet, DOLLCHESTRA, Mira-Cra Park!)")
