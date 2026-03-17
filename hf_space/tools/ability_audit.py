"""
Quick ability audit script that finds weak links in the ability system.
Examines bytecode patterns, parsing success rates, and identifies problematic cards.
"""

import json
import sys
from collections import Counter

sys.path.insert(0, ".")


def main():
    # Load compiled data
    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        db = json.load(f)

    member_db = db["member_db"]
    live_db = db["live_db"]

    print("=" * 60)
    print("ABILITY SYSTEM AUDIT")
    print("=" * 60)

    # Stats counters
    total_members = len(member_db)
    total_lives = len(live_db)
    members_with_abilities = 0
    lives_with_abilities = 0
    empty_bytecode = []
    meta_rule_abilities = []
    nop_only = []
    missing_trigger = []

    # Analyze members
    for card_id, card in member_db.items():
        abilities = card.get("abilities", [])
        if abilities:
            members_with_abilities += 1
            for i, ab in enumerate(abilities):
                bc = ab.get("bytecode", [])
                trigger = ab.get("trigger")

                # Check for empty or near-empty bytecode
                if not bc or len(bc) < 4:
                    empty_bytecode.append((card.get("card_no", card_id), i, "empty"))
                elif bc == [1, 0, 0, 0]:  # Just RETURN
                    nop_only.append((card.get("card_no", card_id), i, "RETURN only"))

                # Check for META_RULE opcodes (29)
                if 29 in bc:
                    meta_rule_abilities.append((card.get("card_no", card_id), i, ab.get("text", "")[:50]))

                # Check for missing trigger types
                if trigger is None or trigger == 0:
                    missing_trigger.append((card.get("card_no", card_id), i, ab.get("text", "")[:50]))

    # Analyze lives
    for card_id, card in live_db.items():
        abilities = card.get("abilities", [])
        if abilities:
            lives_with_abilities += 1
            for i, ab in enumerate(abilities):
                bc = ab.get("bytecode", [])
                if not bc or len(bc) < 4:
                    empty_bytecode.append((card.get("card_no", card_id), i, "empty (LIVE)"))

    print(f"\nTotal Members: {total_members}")
    print(f"Members with abilities: {members_with_abilities}")
    print(f"Total Lives: {total_lives}")
    print(f"Lives with abilities: {lives_with_abilities}")

    print("\n--- POTENTIAL ISSUES ---")
    print(f"Empty/Short Bytecode: {len(empty_bytecode)}")
    print(f"NOP-Only (RETURN only): {len(nop_only)}")
    print(f"META_RULE Opcodes: {len(meta_rule_abilities)}")
    print(f"Missing Trigger Type: {len(missing_trigger)}")

    # Show samples
    if empty_bytecode:
        print("\n[EMPTY BYTECODE] Top 10:")
        for item in empty_bytecode[:10]:
            print(f"  {item[0]} (Ability {item[1]}): {item[2]}")

    if nop_only:
        print("\n[NOP-ONLY] Top 10:")
        for item in nop_only[:10]:
            print(f"  {item[0]} (Ability {item[1]}): {item[2]}")

    if meta_rule_abilities:
        print("\n[META_RULE] Top 10:")
        for item in meta_rule_abilities[:10]:
            print(f"  {item[0]} (Ability {item[1]}): {item[2]}")

    if missing_trigger:
        print("\n[MISSING TRIGGER] Top 10:")
        for item in missing_trigger[:10]:
            print(f"  {item[0]} (Ability {item[1]}): {item[2]}")

    # Opcode distribution
    print("\n--- OPCODE DISTRIBUTION ---")
    opcode_counts = Counter()
    for card_id, card in member_db.items():
        for ab in card.get("abilities", []):
            bc = ab.get("bytecode", [])
            for i in range(0, len(bc), 4):
                if i < len(bc):
                    opcode_counts[bc[i]] += 1

    print("Top 20 Opcodes:")
    for op, count in opcode_counts.most_common(20):
        print(f"  Opcode {op}: {count}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
