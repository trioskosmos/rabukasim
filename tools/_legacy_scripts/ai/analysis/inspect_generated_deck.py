import json
import random


def main():
    # 1. Load Verified Pool
    try:
        with open("data/verified_card_pool.json", "r", encoding="utf-8") as f:
            verified_data = json.load(f)
    except FileNotFoundError:
        print("Error: data/verified_card_pool.json not found.")
        return

    # 2. Load Card DB
    try:
        with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
            db_data = json.load(f)
    except FileNotFoundError:
        print("Error: data/cards_compiled.json not found.")
        return

    # Map CardNo -> ID and Data
    member_no_map = {}
    member_data_map = {}
    for cid, cdata in db_data.get("member_db", {}).items():
        member_no_map[cdata["card_no"]] = int(cid)
        member_data_map[int(cid)] = cdata

    live_no_map = {}
    live_data_map = {}
    for cid, cdata in db_data.get("live_db", {}).items():
        live_no_map[cdata["card_no"]] = int(cid)
        live_data_map[int(cid)] = cdata

    # 3. Build Pools
    ability_member_ids = []
    ability_live_ids = []

    # Support verified_abilities (legacy) + members (new)
    source_members = verified_data.get("verified_abilities", []) + verified_data.get("members", [])
    for v_no in source_members:
        if v_no in member_no_map:
            ability_member_ids.append(member_no_map[v_no])

    source_lives = verified_data.get("verified_lives", []) + verified_data.get("lives", [])
    for v_no in source_lives:
        if v_no in live_no_map:
            ability_live_ids.append(live_no_map[v_no])

    print("\nPool Stats:")
    print(f"  Members Available: {len(ability_member_ids)}")
    print(f"  Lives Available:   {len(ability_live_ids)}")

    NUM_DECKS = 5
    print(f"\n=== GENERATING {NUM_DECKS} TEST DECKS ===")

    for d_i in range(NUM_DECKS):
        # 4. Generate Deck
        deck_members = []
        if len(ability_member_ids) == 48:
            deck_members = ability_member_ids[:]  # Exact Copy
        else:
            for _ in range(48):
                if ability_member_ids:
                    idx = random.randint(0, len(ability_member_ids) - 1)
                    deck_members.append(ability_member_ids[idx])

        deck_lives = []
        if len(ability_live_ids) == 12:
            deck_lives = ability_live_ids[:]  # Exact Copy
        else:
            for _ in range(12):
                if ability_live_ids:
                    idx = random.randint(0, len(ability_live_ids) - 1)
                    deck_lives.append(ability_live_ids[idx])
                else:
                    deck_lives.append(999)

        # 5. Validate
        member_counts = {}
        for mid in deck_members:
            member_counts[mid] = member_counts.get(mid, 0) + 1

        live_counts = {}
        for lid in deck_lives:
            live_counts[lid] = live_counts.get(lid, 0) + 1

        # Check constraints
        violations = []
        if len(deck_members) != 48:
            violations.append(f"Member Count {len(deck_members)} != 48")
        if len(deck_lives) != 12:
            violations.append(f"Live Count {len(deck_lives)} != 12")

        for mid, count in member_counts.items():
            if count > 4:
                # data = member_data_map.get(mid, {})
                # name = data.get("card_no", str(mid))
                violations.append(f"Member {mid} count {count} > 4")

        for lid, count in live_counts.items():
            if count > 4:
                violations.append(f"Live {lid} count {count} > 4")

        status = "PASS" if not violations else "FAIL"
        print(f"\nDeck {d_i + 1}: {status}")
        if violations:
            print(f"  Violations ({len(violations)}):")
            for v in violations[:3]:
                print(f"    - {v}")
            if len(violations) > 3:
                print(f"    - ... and {len(violations) - 3} more")

        # Show detail for first deck only or if requested
        if d_i == 0:
            print("\n  -- Sample Content (Top 3 Members) --")
            sorted_mids = sorted(member_counts.keys())
            for i, mid in enumerate(sorted_mids):
                if i >= 3:
                    break
                count = member_counts[mid]
                data = member_data_map.get(mid, {})
                card_no = data.get("card_no", "Unknown")
                print(f"    ID {mid:<4} | Qty {count} | {card_no}")

            print("  -- Sample Content (Top 3 Lives) --")
            sorted_lids = sorted(live_counts.keys())
            for i, lid in enumerate(sorted_lids):
                if i >= 3:
                    break
                count = live_counts[lid]
                data = live_data_map.get(lid, {})
                card_no = data.get("card_no", "Unknown")
                print(f"    ID {lid:<4} | Qty {count} | {card_no}")

    print("\nEND OF REPORT")


if __name__ == "__main__":
    main()
