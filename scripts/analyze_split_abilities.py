#!/usr/bin/env python3
"""Analyze cards_compiled.json to show split abilities and what goes into the file."""

import json
from pathlib import Path

def load_cards_compiled():
    """Load cards_compiled.json."""
    data_dir = Path(__file__).parent.parent / "data"
    fpath = data_dir / "cards_compiled.json"
    
    with open(fpath, "r", encoding="utf-8") as f:
        return json.load(f)

def analyze_split_abilities(data):
    """Find cards with multiple split abilities."""
    results = []
    
    cards = data.get("member_db", {})
    
    for card_id, card in cards.items():
        if not isinstance(card, dict):
            continue
        
        abilities = card.get("abilities", [])
        if not isinstance(abilities, list) or len(abilities) <= 1:
            continue
        
        # Card has multiple abilities
        ability_details = []
        for i, ability in enumerate(abilities):
            if not isinstance(ability, dict):
                continue
            
            # Get frame_program if exists
            frame_program = ability.get("frame_program", [])
            effects = ability.get("effects", [])
            
            ability_details.append({
                "index": i,
                "trigger": ability.get("trigger"),
                "trigger_name": ability.get("trigger_name", "unknown"),
                "frame_count": len(frame_program),
                "effects_count": len(effects),
                "has_empty_effects": len(effects) == 0,
                "opcode_sequence": [f.get("op", "unknown") for f in frame_program[:5]] if frame_program else [],
                "original_text": ability.get("original_text", "")[:100]
            })
        
        results.append({
            "id": card_id,
            "name": card.get("name", "Unknown"),
            "ability_count": len(abilities),
            "abilities": ability_details
        })
    
    return results

def print_split_abilities(cards, count=10):
    """Print cards with multiple split abilities."""
    print(f"\n{'='*100}")
    print(f"CARDS WITH MULTIPLE SPLIT ABILITIES (showing what goes into cards_compiled.json)")
    print(f"{'='*100}\n")
    
    for card in cards[:count]:
        print(f"\n{'='*80}")
        print(f"Card: {card['name']} (ID: {card['id']})")
        print(f"Total Abilities: {card['ability_count']}")
        print(f"{'='*80}")
        
        for ability in card['abilities']:
            print(f"\n  Ability #{ability['index'] + 1}:")
            print(f"    Trigger: {ability['trigger_name']} (code: {ability['trigger']})")
            print(f"    Frame Program: {ability['frame_count']} frames")
            print(f"    Effects Array: {ability['effects_count']} items (empty: {ability['has_empty_effects']})")
            print(f"    Opcodes: {' -> '.join(ability['opcode_sequence'])}")
            if ability['original_text']:
                print(f"    Text: {ability['original_text']}...")
        print()

def main():
    try:
        data = load_cards_compiled()
        print("Loaded cards_compiled.json")
        
        cards = analyze_split_abilities(data)
        print(f"Found {len(cards)} cards with multiple split abilities\n")
        
        print_split_abilities(cards, 20)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
