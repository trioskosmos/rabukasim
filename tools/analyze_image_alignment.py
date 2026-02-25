import json
import os
import re

def analyze_discrepancies():
    json_path = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\data\cards_compiled.json"
    img_root = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\frontend\img"
    cards_webp_dir = os.path.join(img_root, "cards_webp")
    
    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found.")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    all_cards = {**data.get("member_db", {}), **data.get("live_db", {})}
    existing_files = set(os.listdir(cards_webp_dir))
    
    missing_but_exists_alternative = [] # img_path is wrong but file exists based on card_no
    truly_missing = [] # file doesn't exist at all
    metadata_mismatch = [] # img_path exists but doesn't match expected pattern (optional check)

    def normalize_no(card_no):
        # Normalize card no for filename matching
        # Examples: LL-bp1-001-R＋ -> LL-bp1-001-R2.webp (sometimes)
        # We need to see common patterns.
        return card_no.replace("＋", "2").replace("+", "2")

    for card_id, card_data in all_cards.items():
        card_no = card_data.get("card_no", "Unknown")
        img_path_val = card_data.get("img_path", "")
        img_filename = os.path.basename(img_path_val)
        
        full_img_path = os.path.join(img_root, img_path_val.replace("/", "\\"))
        
        if not os.path.exists(full_img_path):
            # Try to find it by card_no
            potential_name = normalize_no(card_no) + ".webp"
            if potential_name in existing_files:
                missing_but_exists_alternative.append({
                    "id": card_id,
                    "no": card_no,
                    "current_meta": img_path_val,
                    "found_file": f"cards_webp/{potential_name}"
                })
            else:
                # Try simple variants
                found = False
                for f in existing_files:
                    if card_no in f or normalize_no(card_no) in f:
                        missing_but_exists_alternative.append({
                            "id": card_id,
                            "no": card_no,
                            "current_meta": img_path_val,
                            "found_file": f"cards_webp/{f}"
                        })
                        found = True
                        break
                
                if not found:
                    truly_missing.append({
                        "id": card_id,
                        "no": card_no,
                        "meta": img_path_val
                    })

    print(f"Total cards analyzed: {len(all_cards)}")
    print(f"Existing files in cards_webp: {len(existing_files)}")
    
    print("\n--- METADATA ALIGNMENT (Wrong path in JSON, but file exists) ---")
    for item in missing_but_exists_alternative:
        print(f"ID: {item['id']} ({item['no']}) -> Expected '{item['current_meta']}', but suggests '{item['found_file']}'")

    print("\n--- TRULY MISSING (Need to be downloaded) ---")
    for item in truly_missing:
        print(f"ID: {item['id']} ({item['no']}) -> No file matching name found. (Meta: {item['meta']})")

if __name__ == "__main__":
    analyze_discrepancies()
