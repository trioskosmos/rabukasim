#!/usr/bin/env python3
"""Analyze cards.json to find longest/complex abilities for unification examples."""

import json
from pathlib import Path

def load_cards():
    """Load cards from data directory."""
    data_dir = Path(__file__).parent.parent / "data"
    
    # Try cards.json first, then cards_compiled.json
    for fname in ["cards.json", "cards_compiled.json"]:
        fpath = data_dir / fname
        if fpath.exists():
            with open(fpath, "r", encoding="utf-8") as f:
                return json.load(f), fname
    raise FileNotFoundError("No cards.json or cards_compiled.json found")

def analyze_abilities(data, source_file):
    """Find cards with longest ability texts."""
    results = []
    
    # Handle both formats
    if "member_db" in data:
        # cards_compiled.json format
        cards = data["member_db"]
    else:
        # cards.json format (flat dictionary)
        cards = data
    
    for card_id, card in cards.items():
        if not isinstance(card, dict):
            continue
            
        # Get ability text
        ability_text = ""
        if "ability" in card:
            ability_text = card["ability"]
        elif "original_text" in card:
            ability_text = card["original_text"]
        elif "abilities" in card and card["abilities"]:
            abilities = card["abilities"]
            if isinstance(abilities, list) and len(abilities) > 0:
                ability_text = abilities[0].get("original_text", "")
        
        if ability_text and len(ability_text) > 30:  # Filter out empty/short
            results.append({
                "id": card_id,
                "name": card.get("name", "Unknown"),
                "text": ability_text,
                "length": len(ability_text),
                "has_abilities": "abilities" in card and card["abilities"],
                "ability_count": len(card.get("abilities", [])) if isinstance(card.get("abilities"), list) else 0
            })
    
    # Sort by length descending
    results.sort(key=lambda x: x["length"], reverse=True)
    return results

def print_complex_examples(cards, count=10):
    """Print top N most complex abilities."""
    print(f"\n{'='*80}")
    print(f"TOP {count} LONGEST ABILITIES (for unification examples)")
    print(f"{'='*80}\n")
    
    for i, card in enumerate(cards[:count], 1):
        print(f"\n{i}. Card: {card['name']} (ID: {card['id']})")
        print(f"   Length: {card['length']} chars")
        print(f"   Multiple Abilities: {card['ability_count']}")
        print(f"   Text: {card['text'][:200]}{'...' if len(card['text']) > 200 else ''}")
        print()

def main():
    try:
        data, source = load_cards()
        print(f"Loaded {source}")
        
        cards = analyze_abilities(data, source)
        print(f"Found {len(cards)} cards with abilities")
        
        print_complex_examples(cards, 15)
        
        # Also print cards with multiple abilities
        multi = [c for c in cards if c["ability_count"] > 1][:5]
        if multi:
            print(f"\n{'='*80}")
            print("CARDS WITH MULTIPLE ABILITIES")
            print(f"{'='*80}\n")
            for card in multi:
                print(f"- {card['name']}: {card['ability_count']} abilities")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
