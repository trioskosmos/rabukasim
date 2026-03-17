import json


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    cards = load_json("data/cards_compiled.json")
    pool = load_json("verified_card_pool.json")

    # 1. Total Playable Cards
    # Filter out invalid or non-member cards if necessary, but 'member_db' usually implies members.
    # We might want to count Lives too if they are in the pool.

    total_members = len(cards.get("member_db", {}))
    total_lives = len(cards.get("live_db", {}))
    total_cards = total_members + total_lives

    # 2. Verified Cards
    # Pool can be a list (new format) or dict (old format)
    if isinstance(pool, list):
        v_abilities = set(pool)
        v_vanilla_m = set()
        v_vanilla_l = set()
    else:
        v_abilities = set(pool.get("verified_abilities", []))
        v_vanilla_m = set(pool.get("vanilla_members", []))
        v_vanilla_l = set(pool.get("vanilla_lives", []))

    # Ensure no overlap (though they should be distinct lists, good to check)
    all_verified = v_abilities | v_vanilla_m | v_vanilla_l

    print("--- Verification Coverage Stats ---")
    print(f"Total Cards in Database: {total_cards}")
    print(f"  - Members: {total_members}")
    print(f"  - Lives:   {total_lives}")
    print(f"Verified Pool Total:     {len(all_verified)}")
    print(f"  - Strictly Verified:   {len(v_abilities)}")
    print(f"  - Vanilla Members:     {len(v_vanilla_m)}")
    print(f"  - Vanilla Lives:       {len(v_vanilla_l)}")

    # 3. Ability Coverage (Requested Metric)
    # Identify actual ability cards from the source DB
    ability_card_ids = set()
    vanilla_card_ids = set()

    for db in [cards.get("member_db", {}), cards.get("live_db", {})]:
        for cno, card in db.items():
            # Check if card has meaningful abilities
            abilities = card.get("abilities", [])
            has_ability = False
            if abilities:
                # Ensure it's not just empty parsing
                if any(ab.get("raw_text") or ab.get("trigger") for ab in abilities):
                    has_ability = True

            # Use actual card_no, not the dict key (which is an int ID)
            real_cno = card.get("card_no")
            if not real_cno:
                continue

            if has_ability:
                ability_card_ids.add(real_cno)
            else:
                vanilla_card_ids.add(real_cno)

    total_ability_cards = len(ability_card_ids)

    # Intersection: verified_abilities that are actually in the ability_card_ids set
    # (Just to be safe against data drift)
    verified_ability_hits = v_abilities.intersection(ability_card_ids)

    print("-" * 30)
    print("Ability-Only Coverage Stats")
    print(f"Total Cards with Abilities: {total_ability_cards}")
    print(f"Verified Ability Cards:     {len(verified_ability_hits)}")

    ability_coverage = (len(verified_ability_hits) / total_ability_cards) * 100 if total_ability_cards > 0 else 0
    print(f"Ability Coverage:           {ability_coverage:.2f}%")


if __name__ == "__main__":
    main()
