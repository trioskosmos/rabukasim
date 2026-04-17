"""Show a card's ability in all three forms: backup, semantic, converted."""

import json
import sys

def load_backup():
    with open("launcher/static_content/data/ability_frame_source.json.backup", "r", encoding="utf-8") as f:
        return json.load(f)

def load_semantic():
    with open("data/abilities_extracted_from_cards.json", "r", encoding="utf-8") as f:
        return json.load(f)

def load_converted():
    with open("data/ability_frame_source.json", "r", encoding="utf-8") as f:
        return json.load(f)

def find_in_backup(backup_data, search_term):
    """Find ability in backup by card number or text."""
    for ability in backup_data["abilities"]:
        if search_term in ability.get("primary_text_jp", ""):
            return ability
        for card_ref in ability.get("card_refs", []):
            if search_term in card_ref.get("card_no", "") or search_term in card_ref.get("name", ""):
                return ability
    return None

def find_in_semantic(semantic_data, search_term):
    """Find ability in semantic by card number or text."""
    for ability in semantic_data["unique_abilities"]:
        if search_term in ability.get("full_text", ""):
            return ability
        for card in ability.get("cards", []):
            if search_term in card:
                return ability
    return None

def find_in_converted(converted_data, search_term):
    """Find ability in converted by card number or text."""
    for ability in converted_data["abilities"]:
        if search_term in ability.get("primary_text_jp", ""):
            return ability
        for card_ref in ability.get("card_refs", []):
            if search_term in card_ref.get("card_no", "") or search_term in card_ref.get("name", ""):
                return ability
    return None

def show_ability(ability, label):
    """Display ability details."""
    if not ability:
        print(f"\n=== {label}: NOT FOUND ===\n")
        return
    
    print(f"\n=== {label} ===")
    print(f"Text: {ability.get('primary_text_jp', ability.get('full_text', 'N/A'))[:150]}...")
    print(f"Trigger: {ability.get('trigger', 'N/A')}")
    
    frames = ability.get("frames", [])
    print(f"Frames ({len(frames)}):")
    for i, frame in enumerate(frames[:10]):
        print(f"  {i}: {frame.get('op')} value={frame.get('value')} slot={frame.get('slot')}")
    if len(frames) > 10:
        print(f"  ... and {len(frames) - 10} more")
    
    cost = ability.get("cost")
    if cost:
        print(f"Cost: {cost}")
    elif ability.get("costless"):
        print(f"Cost: costless={ability.get('costless')}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python show_card_abilities.py <search_term>")
        print("  search_term: card number (e.g., PL!S-bp2-009-P) or name (e.g., 黒澤ルビィ) or text fragment")
        sys.exit(1)
    
    search_term = sys.argv[1]
    
    print(f"Searching for: {search_term}\n")
    
    backup_data = load_backup()
    semantic_data = load_semantic()
    converted_data = load_converted()
    
    backup_ability = find_in_backup(backup_data, search_term)
    semantic_ability = find_in_semantic(semantic_data, search_term)
    converted_ability = find_in_converted(converted_data, search_term)
    
    show_ability(backup_ability, "BACKUP (ability_frame_source.json.backup)")
    show_ability(semantic_ability, "SEMANTIC (abilities_extracted_from_cards.json)")
    show_ability(converted_ability, "CONVERTED (ability_frame_source.json)")

if __name__ == "__main__":
    main()
