import os
import sys

# quick hack to import parser
sys.path.append(os.getcwd())

import json

from compiler.parser import AbilityParser

with open("card_dump.json", "r", encoding="utf-8") as f:
    data = json.load(f)
    card = data[0]
    text = card["ability"]
    print(f"DEBUG: Parsing Card {card.get('card_no')}")
    print(f"DEBUG: Text (repr): {repr(text)}")

# Try parsing
print("Parsing text:")
print(text)
abilities = AbilityParser.parse_ability_text(text)

for i, ab in enumerate(abilities):
    print(f"Ability {i}: Trigger={ab.trigger}")
    for eff in ab.effects:
        print(f"  Action: Type={eff.effect_type.value} ({getattr(eff.effect_type, 'name', '')}) Val={eff.value}")
