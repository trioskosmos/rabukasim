"""Extract abilities from ability_frame_source.json preserving ab# indexing."""
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[2]

def main():
    source_path = ROOT / "data" / "ability_frame_source.json"
    output_path = ROOT / "data" / "abilities_extracted_from_cards_with_ab_index.json"
    
    print(f"Loading from {source_path}...")
    with open(source_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Group by (card_no, ability_index) to preserve ab# indexing
    card_abilities = defaultdict(lambda: {
        "card_no": "",
        "card_name": "",
        "abilities": {}
    })
    
    for ability in data["abilities"]:
        for card_ref in ability.get("card_refs", []):
            card_no = card_ref["card_no"]
            ab_idx = card_ref["ability_index"]
            trigger = card_ref["trigger"]
            name = card_ref["name"]
            
            key = (card_no, ab_idx)
            card_abilities[key]["card_no"] = card_no
            card_abilities[key]["card_name"] = name
            card_abilities[key]["abilities"][ab_idx] = {
                "ability_index": ab_idx,
                "trigger": trigger,
                "trigger_name": ability.get("trigger", ""),
                "primary_text_jp": ability.get("primary_text_jp", ""),
                "primary_text_en": ability.get("primary_text_en", ""),
                "frames": ability.get("frames", []),
            }
    
    # Convert to list
    output_list = []
    for (card_no, ab_idx), card_data in card_abilities.items():
        for idx, ability_data in card_data["abilities"].items():
            output_list.append({
                "card_no": card_no,
                "card_name": card_data["card_name"],
                "ability_index": ability_data["ability_index"],
                "trigger": ability_data["trigger"],
                "trigger_name": ability_data["trigger_name"],
                "primary_text_jp": ability_data["primary_text_jp"],
                "primary_text_en": ability_data["primary_text_en"],
                "frames": ability_data["frames"],
            })
    
    output_data = {
        "schema": "extracted_abilities_with_ab_index.v1",
        "generated_at": datetime.now().isoformat(),
        "generated_by": "tools/ability_extraction/extract_from_frame_source.py",
        "source_file": "data/ability_frame_source.json",
        "statistics": {
            "total_entries": len(output_list),
        },
        "abilities": output_list,
    }
    
    print(f"Writing {len(output_list)} entries to {output_path}...")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print("Done!")

if __name__ == "__main__":
    main()
