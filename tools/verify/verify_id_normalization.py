import json
import os
from collections import defaultdict

from engine.game.deck_utils import UnifiedDeckParser


def run_audit():
    cards_path = "data/cards.json"
    if not os.path.exists(cards_path):
        print(f"Error: {cards_path} not found.")
        return

    with open(cards_path, "r", encoding="utf-8") as handle:
        cards = json.load(handle)

    print(f"Auditing {len(cards)} card entries...")

    normalized_map = defaultdict(list)
    errors = []

    for card_id, data in cards.items():
        card_no = data.get("card_no", card_id)
        norm_id = UnifiedDeckParser.normalize_code(card_id)
        norm_no = UnifiedDeckParser.normalize_code(card_no)

        normalized_map[norm_id].append(card_id)

        if norm_id != norm_no:
            errors.append(
                f"Mismatch: key '{card_id}' vs card_no '{card_no}' (Normalized into '{norm_id}' and '{norm_no}')"
            )

    collisions = []
    for norm, original_ids in normalized_map.items():
        if len(original_ids) > 1:
            collisions.append({"norm": norm, "originals": original_ids})

    report_path = "reports/id_normalization_audit.md"
    os.makedirs("reports", exist_ok=True)

    with open(report_path, "w", encoding="utf-8") as handle:
        handle.write("# Card ID Normalization Audit Report\n\n")
        handle.write(f"- **Total Cards Audited**: {len(cards)}\n")
        handle.write("- **Normalization Logic**: `NFKC + trim + collapse spaces + normalize plus/minus`\n\n")

        if not collisions and not errors:
            handle.write("> [!NOTE]\n> **ALL CLEAR**: No collisions or inconsistencies found. Normalization is safe.\n")
        else:
            if errors:
                handle.write("## Inconsistencies (Key vs Card No)\n")
                handle.write(
                    "> [!WARNING]\n> These cards have an internal key that doesn't match their `card_no` when normalized.\n\n"
                )
                for error in errors[:50]:
                    handle.write(f"- {error}\n")
                if len(errors) > 50:
                    handle.write(f"\n... and {len(errors) - 50} more.\n")

            if collisions:
                handle.write("\n## Collisions\n")
                handle.write(
                    "> [!CAUTION]\n> Multiple different IDs map to the same normalized string. This will cause matching ambiguity!\n\n"
                )
                handle.write("| Normalized ID | Original IDs |\n")
                handle.write("| :--- | :--- |\n")
                for collision in collisions:
                    handle.write(f"| `{collision['norm']}` | `{', '.join(collision['originals'])}` |\n")

    print(f"Audit complete. Report written to {report_path}")
    if collisions:
        print(f"WARNING: Found {len(collisions)} collisions!")
    if errors:
        print(f"WARNING: Found {len(errors)} inconsistencies!")


if __name__ == "__main__":
    run_audit()
