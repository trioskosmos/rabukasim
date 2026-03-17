import json

# Load raw cards.json
with open("engine/data/cards.json", "r", encoding="utf-8") as f:
    raw = json.load(f)

# Load compiled data
with open("engine/data/cards_compiled.json", "r", encoding="utf-8") as f:
    compiled = json.load(f)

# Find PL!-sd1-007-SD and PL!-sd1-008-SD in raw
for k in ["PL!-sd1-007-SD", "PL!-sd1-008-SD"]:
    if k in raw:
        print(f"--- RAW {k} ---")
        print(f"Ability: {raw[k].get('ability', '')}")

# Find them in compiled
for mid, card in compiled["member_db"].items():
    if card["card_no"] in ["PL!-sd1-007-SD", "PL!-sd1-008-SD"]:
        print(f"--- COMPILED {card['card_no']} (ID {mid}) ---")
        print(f"Ability Text: {card.get('ability_text', '')}")
        for i, ab in enumerate(card["abilities"]):
            print(f"  Ability {i}: Trigger={ab['trigger']}")
            for j, eff in enumerate(ab["effects"]):
                print(f"    Effect {j}: Type={eff['effect_type']} Val={eff.get('value')}")
