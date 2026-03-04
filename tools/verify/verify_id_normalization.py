import json
import os
from collections import defaultdict

def normalize_code(code: str) -> str:
    if not code:
        return ""
    # Exact match of Rust/JS normalization logic
    return code.strip().replace('＋', "+").replace('－', "-").replace('ー', "-").upper()

def run_audit():
    cards_path = "data/cards.json"
    if not os.path.exists(cards_path):
        print(f"Error: {cards_path} not found.")
        return

    with open(cards_path, "r", encoding="utf-8") as f:
        cards = json.load(f)

    print(f"Auditing {len(cards)} card entries...")

    normalized_map = defaultdict(list)
    errors = []
    
    # 1. Check for basic normalization coverage
    for card_id, data in cards.items():
        card_no = data.get("card_no", card_id)
        norm_id = normalize_code(card_id)
        norm_no = normalize_code(card_no)
        
        normalized_map[norm_id].append(card_id)
        
        if norm_id != norm_no:
            errors.append(f"Mismatch: key '{card_id}' vs card_no '{card_no}' (Normalized into '{norm_id}' and '{norm_no}')")

    # 2. Check for collisions (different IDs mapping to same norm)
    collisions = []
    for norm, original_ids in normalized_map.items():
        if len(original_ids) > 1:
            # We filter out suspected identical entries if we find any
            collisions.append({
                "norm": norm,
                "originals": original_ids
            })

    # 3. Generate Report
    report_path = "reports/id_normalization_audit.md"
    os.makedirs("reports", exist_ok=True)
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Card ID Normalization Audit Report\n\n")
        f.write(f"- **Total Cards Audited**: {len(cards)}\n")
        f.write(f"- **Normalization Logic**: `Uppercase + Trim + [＋, －, ー] to [+, -, -]`\n\n")
        
        if not collisions and not errors:
            f.write("> [!NOTE]\n> **ALL CLEAR**: No collisions or inconsistencies found. Normalization is safe.\n")
        else:
            if errors:
                f.write("## Inconsistencies (Key vs Card No)\n")
                f.write("> [!WARNING]\n> These cards have a internal key that doesn't match their `card_no` when normalized.\n\n")
                for e in errors[:50]:
                    f.write(f"- {e}\n")
                if len(errors) > 50:
                    f.write(f"\n... and {len(errors)-50} more.\n")
            
            if collisions:
                f.write("\n## Collisions\n")
                f.write("> [!CAUTION]\n> Multiple different IDs map to the same normalized string. This will cause matching ambiguity!\n\n")
                f.write("| Normalized ID | Original IDs |\n")
                f.write("| :--- | :--- |\n")
                for c in collisions:
                    f.write(f"| `{c['norm']}` | `{', '.join(c['originals'])}` |\n")

    print(f"Audit complete. Report written to {report_path}")
    if collisions:
        print(f"WARNING: Found {len(collisions)} collisions!")
    if errors:
        print(f"WARNING: Found {len(errors)} inconsistencies!")

if __name__ == "__main__":
    run_audit()
