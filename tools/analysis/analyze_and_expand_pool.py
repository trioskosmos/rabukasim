import json
import os
import re


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_log_verified_cards(log_path):
    verified_ids = set()
    if not os.path.exists(log_path):
        return verified_ids

    with open(log_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Regex to find table rows with Passed or Fixed
    # | Card No. | ... | Status |
    # Matches PL... or LL... patterns
    matches = re.finditer(
        r"\|\s*([A-Za-z0-9!+\-]+)\s*\|\s*.*?\s*\|\s*.*?(Passed|Fixed|Verified)", content, re.IGNORECASE
    )
    for m in matches:
        cid = m.group(1).strip()
        # Filter out header or invalid lines
        if cid.startswith("PL") or cid.startswith("LL"):
            verified_ids.add(cid)

    return verified_ids


def main():
    pool_path = "verified_card_pool.json"
    cards_path = "data/cards_compiled.json"
    log_path = "engine/tests/cards/card_verification_log.md"

    pool_data = load_json(pool_path)
    cards_data = load_json(cards_path)

    current_pool = set(pool_data.get("verified_abilities", []))
    current_vanilla = set(pool_data.get("vanilla_members", []) + pool_data.get("vanilla_lives", []))

    # 1. Check Log consistency
    log_verified = parse_log_verified_cards(log_path)
    missing_from_pool = []
    for cid in log_verified:
        if cid not in current_pool and cid not in current_vanilla:
            missing_from_pool.append(cid)

    print(f"Cards in Log but MISSING from verified_card_pool.json: {len(missing_from_pool)}")
    for cid in missing_from_pool:
        print(f"  - {cid}")

    # 2. Find Simple Cards
    candidates = []

    # Integers based on engine/models/ability.py
    SAFE_EFFECTS = {
        0,  # DRAW
        1,  # ADD_BLADES
        2,  # ADD_HEARTS
        6,  # BOOST_SCORE
        13,  # ENERGY_CHARGE
        8,  # BUFF_POWER
        5,  # RECOVER_LIVE (Maybe simple enough?)
        30,  # ADD_TO_HAND
    }

    SAFE_TRIGGERS = {
        1,  # ON_PLAY
        2,  # ON_LIVE_START
        3,  # ON_LIVE_SUCCESS
    }

    for cid, card in cards_data.get("member_db", {}).items():
        card_no = card.get("card_no")
        if not card_no:
            continue

        if card_no in current_pool or card_no in current_vanilla:
            continue

        abilities = card.get("abilities", [])

        if not abilities:
            continue

        is_simple = True

        # Heuristic: Only 1 Ability to start safe
        if len(abilities) > 1:
            continue

        for abil in abilities:
            # Check Trigger
            if abil.get("trigger", 0) not in SAFE_TRIGGERS:
                is_simple = False
                break

            # Check Conditions - MUST BE EMPTY for "Basic" start
            if abil.get("conditions"):
                is_simple = False
                break

            # Check effects
            effects = abil.get("effects", [])
            if not effects:
                is_simple = False
                break

            for eff in effects:
                etype = eff.get("effect_type")
                if etype not in SAFE_EFFECTS:
                    is_simple = False
                    break

                # Check for complex params?
                params = eff.get("params", {})
                if "condition" in params or "target_filter" in params:
                    is_simple = False
                    break

            if not is_simple:
                break

        if is_simple:
            candidates.append(card_no)

    print(f"\nFound {len(candidates)} candidate cards with simple effects.")

    # Update the pool
    if missing_from_pool or candidates:
        pool_data["verified_abilities"].extend(missing_from_pool)
        pool_data["verified_abilities"].extend(candidates)

        # Deduplicate
        pool_data["verified_abilities"] = list(set(pool_data["verified_abilities"]))

        with open(pool_path, "w", encoding="utf-8") as f:
            json.dump(pool_data, f, indent=2, ensure_ascii=False)

        print(
            f"Updated {pool_path} with {len(missing_from_pool)} missing log cards and {len(candidates)} new candidates."
        )


if __name__ == "__main__":
    main()
