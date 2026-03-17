
import json
from pathlib import Path

def get_all_abilities():
    compiled_path = Path("data/cards_compiled.json")
    with open(compiled_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    all_abilities = []
    for db_name in ["member_db", "live_db", "event_db"]:
        db = data.get(db_name, {})
        for card_id, card in db.items():
            if not isinstance(card, dict): continue
            card_no = card.get("card_no")
            original_text = card.get("original_text", "")
            # Japanese abilities are usually separated by \n
            japanese_lines = original_text.split("\n")
            
            abilities = card.get("abilities", [])
            for idx, ability in enumerate(abilities):
                # Try to get the matching Japanese line
                japanese_text = ""
                if idx < len(japanese_lines):
                    japanese_text = japanese_lines[idx].strip()
                
                all_abilities.append({
                    "card_no": card_no,
                    "ability_idx": idx,
                    "text": ability.get("raw_text", ""),
                    "pseudocode": ability.get("pseudocode", ""),
                    "japanese_text": japanese_text
                })
    
    # Deduplicate by (text, japanese_text)
    seen = set()
    deduped = []
    for a in all_abilities:
        key = (a["text"], a["japanese_text"])
        if key not in seen:
            seen.add(key)
            deduped.append(a)
    return deduped

if __name__ == "__main__":
    abilities = get_all_abilities()
    output_path = Path("canonical_ability_model/all_abilities_list.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(abilities, f, indent=2, ensure_ascii=False)
    print(f"Extracted {len(abilities)} unique abilities to {output_path}")
