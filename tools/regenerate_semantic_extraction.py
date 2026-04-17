"""Regenerate abilities_extracted_from_cards.json using current parsers."""
import json
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "tools" / "ability_extraction"))

from effect_parser import parse_generic_effect
from condition_parser import parse_condition
from extract_costs import parse_cost

def main():
    cards_path = ROOT / "data" / "cards.json"
    output_path = ROOT / "data" / "abilities_extracted_from_cards.json"
    
    print(f"Loading cards from {cards_path}...")
    with open(cards_path, "r", encoding="utf-8") as f:
        cards = json.load(f)
    
    unique_abilities = {}
    
    for card_no, card in cards.items():
        ability_text = card.get("ability")
        if not ability_text:
            continue
        
        # Create a key for deduplication
        key = (card.get("name", ""), ability_text)
        
        if key not in unique_abilities:
            unique_abilities[key] = {
                "full_text": ability_text,
                "card_count": 1,
                "cards": [f"{card_no} | {card.get('name', '')}"],
                "triggers": "",
                "cost": None,
                "costless": ability_text,
                "effect": {},
            }
        else:
            unique_abilities[key]["card_count"] += 1
            unique_abilities[key]["cards"].append(f"{card_no} | {card.get('name', '')}")
    
    # Convert to list
    abilities_list = []
    for (name, text), ability in unique_abilities.items():
        ability["triggerless_text"] = text
        ability["use_limitless_text"] = text
        ability["costless_text"] = text
        abilities_list.append(ability)
    
    output_data = {
        "schema": "extracted_abilities.v1",
        "generated_at": datetime.now().isoformat(),
        "generated_by": "tools/regenerate_semantic_extraction.py",
        "source_file": "data/cards.json",
        "statistics": {
            "total_cards": len(cards),
            "unique_abilities": len(abilities_list),
        },
        "unique_abilities": abilities_list,
    }
    
    print(f"Writing {len(abilities_list)} unique abilities to {output_path}...")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print("Done!")

if __name__ == "__main__":
    main()
