# -*- coding: utf-8 -*-
"""Audit script to find parser issues."""

import json
from pathlib import Path


def main():
    data_path = Path("data/cards_compiled.json")
    data = json.loads(data_path.read_text(encoding="utf-8"))

    members = data.get("member_db", {})
    print(f"Total members: {len(members)}")

    # Find cards with abilities but no effects
    no_effects = []
    for k, v in members.items():
        abilities = v.get("abilities", [])
        for i, a in enumerate(abilities):
            if not a.get("effects"):
                no_effects.append((k, v.get("card_no"), i, a.get("raw_text", "")))

    print(f"\n=== Cards with abilities but no effects: {len(no_effects)} ===")
    for card_id, card_no, ability_idx, raw in no_effects[:15]:
        print(f"  [{card_id}] {card_no} - ability {ability_idx}: {raw[:60]}...")

    # Find cards with UNKNOWN effect type
    unknown_effects = []
    for k, v in members.items():
        abilities = v.get("abilities", [])
        for i, a in enumerate(abilities):
            for j, e in enumerate(a.get("effects", [])):
                if e.get("type") == 999:
                    unknown_effects.append((k, v.get("card_no"), i, j, a.get("raw_text", "")))

    print(f"\n=== Cards with UNKNOWN effect (type=999): {len(unknown_effects)} ===")
    for card_id, card_no, ability_idx, effect_idx, raw in unknown_effects[:15]:
        print(f"  [{card_id}] {card_no} - ability {ability_idx}, effect {effect_idx}: {raw[:60]}...")

    # Find triggers that may have been missed
    no_trigger = []
    for k, v in members.items():
        abilities = v.get("abilities", [])
        for i, a in enumerate(abilities):
            if a.get("trigger") is None or a.get("trigger") == 0:
                raw = a.get("raw_text", "")
                # Check if text has typical trigger keywords
                if any(kw in raw for kw in ["ライブ参加した時", "登場した時", "ライブ成功した時"]):
                    no_trigger.append((k, v.get("card_no"), i, raw))

    print(f"\n=== Cards with likely missed triggers: {len(no_trigger)} ===")
    for card_id, card_no, ability_idx, raw in no_trigger[:10]:
        print(f"  [{card_id}] {card_no} - ability {ability_idx}: {raw[:60]}...")


if __name__ == "__main__":
    main()
