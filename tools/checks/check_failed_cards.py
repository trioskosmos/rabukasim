"""Check the failed cards"""

import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from game.ability import AbilityParser

cards = json.load(open("data/cards.json", encoding="utf-8"))

failed = ["PL!HS-bp1-019-L", "PL!SP-sd1-023-SD", "PL!HS-bp1-018-L"]

for cid in failed:
    c = cards.get(cid, {})
    print(f"\n=== {cid}: {c.get('name', '?')} ===")
    ability = c.get("ability", "NO ABILITY")
    print(f"Text: {ability}")

    parsed = AbilityParser.parse_ability_text(ability)
    print(f"Parsed: {len(parsed)} abilities")
    for a in parsed:
        print(f"  {a}")
