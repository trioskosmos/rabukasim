import json
import sys

with open('data/consolidated_abilities.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

found = False
for key, val in data.items():
    cards = val.get('card_refs', [])
    for card in cards:
        if card.get('card_id') == 423:
            found = True
            print(f"Card ID: {card.get('card_id')}")
            print(f"Name: {card.get('name', 'N/A')}")
            print(f"Card No: {card.get('card_no', 'N/A')}")
            print(f"Trigger: {card.get('trigger', 'N/A')}")
            print(f"Ability Index: {card.get('ability_index', 'N/A')}")
            print(f"\nKey text: {key[:100]}")
            print(f"\nPseudocode: {val.get('pseudocode', 'N/A')}")
            print(f"\nFrames ({len(val.get('frames', []))} total):")
            for i, frame in enumerate(val.get('frames', [])[:10]):
                decoded = frame.get('decoded', 'N/A')
                opcode = frame.get('opcode', 'N/A')
                value = frame.get('value', frame.get('v', 'N/A'))
                print(f"  {i}: {opcode} (value={value}) | {decoded[:70]}")
            break
    if found:
        break

if not found:
    print("Card ID 423 not found")
