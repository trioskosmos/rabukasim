import json


def verify_coverage():
    print("=== Verifying Verified Pool Coverage ===")

    # 1. Load Data
    try:
        with open("data/verified_card_pool.json", "r") as f:
            verified = json.load(f)
        with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
            db_compiled = json.load(f)
        with open("data/cards_numba.json", "r") as f:
            numba_map = json.load(f)
    except FileNotFoundError as e:
        print(f"Error loading data: {e}")
        return

    # 2. Build Maps
    card_no_to_id = {}
    for cid, data in db_compiled.get("member_db", {}).items():
        card_no_to_id[data["card_no"]] = int(cid)
    for cid, data in db_compiled.get("live_db", {}).items():
        card_no_to_id[data["card_no"]] = int(cid)

    # 3. Check Verified List
    missing_id = []
    missing_bytecode = []
    found_count = 0
    used_opcodes = set()

    verified_list = verified.get("verified_abilities", [])
    print(f"Total Verified Cards: {len(verified_list)}")

    for v_no in verified_list:
        if v_no not in card_no_to_id:
            missing_id.append(v_no)
            continue

        cid = card_no_to_id[v_no]
        # Check bytecode map (keys are "cid_abidx")
        # Just check if ANY ability exists for this card
        has_bytecode = False
        for k in numba_map.keys():
            k_cid = int(k.split("_")[0])
            if k_cid == cid:
                has_bytecode = True
                # Collect opcodes
                seq = numba_map[k]
                for i in range(0, len(seq), 4):
                    op = seq[i]
                    if op > 0:  # exclude NOP
                        used_opcodes.add(op)

        if not has_bytecode:
            missing_bytecode.append(f"{v_no} (ID: {cid})")
        else:
            found_count += 1

    print("\nCoverage Results:")
    print(f"Found & Compiled: {found_count}/{len(verified_list)}")

    if missing_id:
        print(f"Missing IDs in DB ({len(missing_id)}): {missing_id}")
    if missing_bytecode:
        print(f"Missing Bytecode ({len(missing_bytecode)}): {missing_bytecode}")

    print(f"\nUsed Opcodes in Verified Pool: {sorted(list(used_opcodes))}")

    # Opcodes Map (Quick Reference)
    # 1: DRAW, 2: CHARGE, 3: BLADES, 4: HEARTS
    # 11: PLAY_MEMBER, 12: ACTIVATE
    # etc.


if __name__ == "__main__":
    verify_coverage()
