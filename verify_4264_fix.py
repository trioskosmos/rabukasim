#!/usr/bin/env python3
import json

with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Card with ID 4264 appears to be a different variant
# Let's check multiple candidates
candidates = ["145", "168", "4264"]

for card_id in candidates:
    if card_id in data.get("member_db", {}):
        card = data["member_db"][card_id]
        if "乙宗" in str(card.get("name", "")):
            print(f"\n{'='*60}")
            print(f"Card ID {card_id}: {card['name']} ({card.get('card_no')})")
            print(f"{'='*60}")
            print(f"Unit: {card.get('units', 'N/A')}")
            print(f"Series/Group: {card.get('groups', 'N/A')}")
            
            # Check the abilities
            for ab_idx, ability in enumerate(card.get("abilities", [])):
                print(f"\nAbility {ab_idx}:")
                print(f"  Trigger: {ability.get('trigger')}")
                
                # Check filters
                if "filters" in ability:
                    for f_idx, filt in enumerate(ability["filters"]):
                        print(f"  Filter {f_idx}:")
                        print(f"    group_enabled: {filt.get('group_enabled')}")
                        if filt.get('group_enabled'):
                            print(f"    group_id: {filt.get('group_id')}")
                        print(f"    unit_enabled: {filt.get('unit_enabled')}")  # ← KEY LINE
                        if filt.get('unit_enabled'):
                            print(f"    unit_id: {filt.get('unit_id')}")
                        if filt.get('value_enabled'):
                            print(f"    value_threshold: {filt.get('value_threshold')}")
                            print(f"    is_le: {filt.get('is_le')}")
                            print(f"    is_cost_type: {filt.get('is_cost_type')}")
