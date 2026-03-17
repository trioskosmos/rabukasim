# -*- coding: utf-8 -*-
"""Debug script to check unmatched abilities."""

import json
from pathlib import Path


def main():
    data_path = Path("data/cards_compiled.json")
    data = json.loads(data_path.read_text(encoding="utf-8"))

    members = data.get("member_db", {})

    # Check specific cards that failed
    failed_ids = ["29", "49", "72", "84", "104", "155"]

    for card_id in failed_ids:
        card = members.get(card_id)
        if not card:
            continue
        print(f"=== Card {card_id}: {card.get('card_no')} ===")
        for i, a in enumerate(card.get("abilities", [])):
            raw = a.get("raw_text", "")
            effects = a.get("effects", [])
            if not effects:
                print(f"  Ability {i} (NO EFFECTS):")
                print(f"    Raw: {raw[:200]}")
            else:
                print(f"  Ability {i}: {len(effects)} effects")
        print()


if __name__ == "__main__":
    main()
