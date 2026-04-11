#!/usr/bin/env python3
import json
import sys

def find_ability(card_no):
    with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for idx, ability in enumerate(data['abilities']):
        for ref in ability.get('card_refs', []):
            if ref.get('card_no') == card_no:
                print(f'=== Ability #{idx} - {card_no} ===')
                print(f"\nText (JP): {ability.get('primary_text_jp', 'N/A')}")
                print(f"\nTrigger: {ability.get('trigger', 'N/A')} (ID: {ability.get('trigger_id', 'N/A')})")
                print(f"\nFrames ({len(ability.get('frames', []))} total):")
                for i, frame in enumerate(ability.get('frames', [])):
                    print(f"  [{i}] {frame.get('op', 'UNKNOWN')}")
                    if 'value' in frame:
                        print(f"       value: {frame['value']}")
                    if 'attr' in frame:
                        print(f"       attr: {frame['attr']}")
                    if 'slot' in frame:
                        print(f"       slot: {frame['slot']}")
                print()
                return ability, idx
    print(f'Card {card_no} not found')
    return None, None

if __name__ == '__main__':
    if len(sys.argv) > 1:
        find_ability(sys.argv[1])
    else:
        # Find the critical abilities from audit
        print("Finding critical abilities from audit report...\n")
        find_ability('PL!S-bp2-001-P')
        print("\n" + "="*60 + "\n")
        find_ability('PL!S-pb1-009-P+')
