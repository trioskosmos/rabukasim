"""Extract card abilities from cards.json and generate abilities_extracted_from_cards.json."""
import json
import re
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / "tools" / "ability_extraction"))

# Import parser modules
from effect_parser import parse_effect
from condition_parser import parse_condition
from extract_costs import extract_cost

TRIGGER_PATTERN = re.compile(r'\{\{([^|]+)\|([^}]+)\}\}')
SLASH_TRIGGER_PATTERN = re.compile(r'/\{\{([^|]+)\|([^}]+)\}\}')

def extract_trigger(text: str) -> tuple[list, str, str]:
    """Extract triggers and use limits from ability text."""
    triggers = []
    use_limit = None
    effect = text
    
    # Remove / prefix trigger patterns
    slash_matches = SLASH_TRIGGER_PATTERN.findall(text)
    for match in slash_matches:
        icon_file = match[0]
        icon_text = match[1]
        slash_pattern = f"/{{{{{icon_file}|{icon_text}}}}}"
        effect = effect.replace(slash_pattern, '', 1)
        triggers.append(icon_text)
    
    # Find all trigger patterns
    trigger_matches = TRIGGER_PATTERN.findall(text)
    
    # Only consider triggers at the very start
    pos = 0
    for match in trigger_matches:
        icon_file = match[0]
        icon_text = match[1]
        match_start = text.find(f"{{{{{icon_file}|{icon_text}}}}}", pos)
        
        # Check if there's any non-trigger text before this match
        before = text[pos:match_start].strip()
        if before:
            break  # Stop if we hit non-trigger text
        
        triggers.append(icon_text)
        effect = effect.replace(f"{{{{{icon_file}|{icon_text}}}}}", '', 1).strip()
        pos = match_start + len(f"{{{{{icon_file}|{icon_text}}}}}")
    
    # Extract use limit (turn restrictions)
    if "ターン1回" in text or "turn1" in text:
        use_limit = "ターン1回"
    
    return triggers, use_limit, effect

def split_by_colon(text: str) -> tuple:
    """Split text into cost and effect parts."""
    if '：' in text:
        parts = text.split('：', 1)
        return parts[0].strip(), parts[1].strip()
    elif ':' in text:
        parts = text.split(':', 1)
        return parts[0].strip(), parts[1].strip()
    else:
        return None, text

def main():
    cards_path = ROOT / "data" / "cards.json"
    output_path = ROOT / "data" / "abilities_extracted_from_cards.json"
    
    print(f"Loading cards from {cards_path}...")
    with open(cards_path, "r", encoding="utf-8") as f:
        cards = json.load(f)
    
    unique_abilities = {}
    
    for card_no, card in cards.items():
        abilities = card.get("abilities", [])
        for idx, ability_text in enumerate(abilities):
            if not ability_text:
                continue
            
            # Create a key for deduplication
            key = (card.get("name", ""), ability_text)
            
            if key not in unique_abilities:
                # Extract triggers
                triggers, use_limit, effect_text = extract_trigger(ability_text)
                
                # Split cost and effect
                cost_text, effect_text = split_by_colon(effect_text)
                
                # Parse cost
                cost = None
                if cost_text:
                    try:
                        cost = extract_cost(cost_text)
                    except:
                        cost = None
                
                # Parse effect
                effect = {}
                try:
                    effect = parse_effect(effect_text)
                except:
                    effect = {"text": effect_text, "actions": []}
                
                unique_abilities[key] = {
                    "full_text": ability_text,
                    "card_count": 1,
                    "cards": [f"{card_no} | {card.get('name', '')} (ab#{idx})"],
                    "triggers": triggers,
                    "use_limit": use_limit,
                    "cost": cost,
                    "costless_text": cost_text if cost_text else ability_text,
                    "effect": effect,
                }
            else:
                unique_abilities[key]["card_count"] += 1
                unique_abilities[key]["cards"].append(f"{card_no} | {card.get('name', '')} (ab#{idx})")
    
    # Convert to list
    abilities_list = []
    for (name, text), ability in unique_abilities.items():
        ability["triggerless_text"] = text
        ability["use_limitless_text"] = text
        abilities_list.append(ability)
    
    output_data = {
        "schema": "extracted_abilities.v1",
        "generated_at": datetime.now().isoformat(),
        "generated_by": "tools/ability_extraction/extract_card_abilities.py",
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
