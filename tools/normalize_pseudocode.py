import json
import re

def normalize_pseudocode():
    with open('data/manual_pseudocode.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    with open('data/metadata.json', 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    # Naming normalization map
    norm_map = {
        "YELL_COUNT": "REDUCE_YELL_COUNT",
        "ACTION_YELL_MULLIGAN": "MULLIGAN",
        "ALL_MEMBER": "ALL_MEMBERS", # Common typo
        "SUCCESS": "ON_LIVE_SUCCESS",
        "CHARGE_ENERGY": "ENERGY_CHARGE",
        "DISCARD_STAGE": "DISCARD_STAGE_ENERGY",
        "MOVE_TO_HAND": "ADD_TO_HAND",
        "COUNT_SUCCESS_LIVES": "COUNT_SUCCESS_LIVE",
        "COUNT_LIVE": "COUNT_LIVE_ZONE",
    }

    # Common Japanese terms found in pseudocode that should be symbolic if possible
    # or just cleaned up
    repl_map = {
        "1枚": "1",
        "2枚以上": "2",
        "ドロー": "DRAW",
        "ブレード追加": "ADD_BLADES",
        "スコア増加": "BOOST_SCORE",
        "ディスカード": "DISCARD_HAND",
        "エネルギー": "ENERGY",
        "メンバー": "MEMBER",
        "デッキ": "DECK",
    }

    modified_count = 0
    for card_no, entry in data.items():
        pseudo = entry.get('pseudocode', '')
        old_pseudo = pseudo
        
        # Apply word-for-word normalization for tokens
        for old, new in norm_map.items():
            pseudo = re.sub(rf'\b{old}\b', new, pseudo)
            
        # Apply regex replacements for Japanese literals
        for old, new in repl_map.items():
            pseudo = pseudo.replace(old, new)
            
        # Strip redundant CHECK_ prefix (translator handles both as seen in plan, but normalization is better)
        pseudo = pseudo.replace("CONDITION: CHECK_", "CONDITION: ")

        if pseudo != old_pseudo:
            entry['pseudocode'] = pseudo
            modified_count += 1

    with open('data/manual_pseudocode.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Normalized {modified_count} pseudocode entries.")

if __name__ == "__main__":
    normalize_pseudocode()
