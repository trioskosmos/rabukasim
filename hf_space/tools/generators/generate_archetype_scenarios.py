import json
import os

# Paths
CARDS_PATH = "data/cards.json"
CARDS_COMPILED_PATH = "data/cards_compiled.json"
OUTPUT_PATH = "engine_rust_src/data/scenarios.json"

# Trigger Types
T_NONE = 0
T_ON_PLAY = 1
T_ON_LIVE_START = 2
T_ON_LIVE_SUCCESS = 3
T_TURN_START = 4
T_TURN_END = 5
T_CONSTANT = 6
T_ACTIVATED = 7
T_ON_LEAVES = 8
T_ON_REVEAL = 9
T_ON_POSITION_CHANGE = 10

# Condition Types
C_NONE = 0
C_STG = 203  # CountStage (mapped from ConditionType::CountStage if we had enum mapping, but using direct values logic from experience)
# Wait, let's use the values form enums.rs or experience.
# Actually, the python script `generate_archetype_scenarios.py` used 203, 204 etc.
# checking logic.rs or compiler for ConditionType values.
# enums.rs: CountStage = 4, CountHand = 5.
# The values 203, 204 seem to be OpCodes for *checking* them in bytecode, not the ConditionType enum in JSON.
# The JSON `conditions` list uses `type` which matches `ConditionType` enum.
# Let's fix this. Use the ENUM values.
C_HAS_MEMBER = 2
C_HAS_COLOR = 3
C_COUNT_STAGE = 4
C_COUNT_HAND = 5
C_COUNT_DISCARD = 6
C_IS_CENTER = 7
C_LIFE_LEAD = 8
C_COUNT_GROUP = 9
C_GROUP_FILTER = 10
C_OPPONENT_HAS = 11
C_SELF_IS_GROUP = 12
C_MODAL_ANSWER = 13
C_COUNT_ENERGY = 14
C_HAS_LIVE = 15
C_COST_CHECK = 16
C_RARITY_CHECK = 17
C_HAND_HAS_NO_LIVE = 18
C_COUNT_SUCCESS_LIVE = 19
C_OPPONENT_HAND_DIFF = 20
C_SCORE_COMPARE = 21
C_HAS_CHOICE = 22
C_OPPONENT_CHOICE = 23
C_COUNT_HEARTS = 24
C_COUNT_BLADES = 25
C_OPPONENT_ENERGY_DIFF = 26
C_HAS_KEYWORD = 27
C_DECK_REFRESHED = 28
C_HAS_MOVED = 29
C_HAND_INCREASED = 30
C_COUNT_LIVE_ZONE = 31
C_BATON = 32
C_TYPE_CHECK = 33
C_IS_IN_DISCARD = 34
C_AREA_CHECK = 35


def generate_scenarios():
    if not os.path.exists(CARDS_COMPILED_PATH):
        print(f"Error: {CARDS_COMPILED_PATH} not found.")
        return
    if not os.path.exists(CARDS_PATH):
        print(f"Error: {CARDS_PATH} not found.")
        return

    with open(CARDS_COMPILED_PATH, "r", encoding="utf-8") as f:
        db_compiled = json.load(f)

    with open(CARDS_PATH, "r", encoding="utf-8") as f:
        db_raw = json.load(f)

    # raw_lookup = db_raw # Correct lookup? db_raw is a dict of card_no -> data?
    # Usually cards.json is a list. Let's assume list and make a dict.
    if isinstance(db_raw, list):
        raw_lookup = {c["card_no"]: c for c in db_raw}
    else:
        raw_lookup = db_raw  # Maybe it's already a dict

    members = db_compiled.get("member_db", {})
    member_ids = [int(cid) for cid in members.keys()]
    lives = db_compiled.get("live_db", {})
    live_ids = [int(cid) for cid in lives.keys()]

    scenarios = []

    def get_setup(conditions, is_pass, target_card_id, trigger_type):
        # Default state
        setup = {
            "hand": [member_ids[0]] if target_card_id != member_ids[0] else [member_ids[1]],
            "deck": member_ids[5:15],
            "live": [live_ids[0], live_ids[1]],
            "discard": [member_ids[2], member_ids[3]],
            "stage": [-1, -1, -1],
            "energy_count": 10,
        }

        # Trigger-specific placement
        if trigger_type == T_ON_PLAY:
            setup["hand"].insert(0, target_card_id)
        elif trigger_type in [
            T_ON_LIVE_START,
            T_ON_LIVE_SUCCESS,
            T_TURN_START,
            T_TURN_END,
            T_ACTIVATED,
            T_ON_LEAVES,
            T_ON_POSITION_CHANGE,
            T_CONSTANT,
        ]:
            setup["stage"] = [target_card_id, -1, -1]
        elif trigger_type == T_ON_REVEAL:
            setup["deck"].insert(0, target_card_id)  # Should be on top of deck or handled specifically

        # Condition handling
        for cond in conditions:
            c_type = cond.get("type")
            val = cond.get("value", 1)  # Default value
            if isinstance(val, str):
                val = 1  # Handle string values if any

            if c_type == C_COUNT_HAND:
                count = val if is_pass else max(0, val - 1)
                setup["hand"] = member_ids[:count]
                if trigger_type == T_ON_PLAY and target_card_id not in setup["hand"]:
                    setup["hand"].append(target_card_id)

            elif c_type == C_COUNT_STAGE:
                count = val if is_pass else max(0, val - 1)
                # Ensure target is on stage if required
                current_stage = [target_card_id] if trigger_type != T_ON_PLAY else []
                remaining = max(0, count - len(current_stage))

                # Fill with other members
                others = [mid for mid in member_ids if mid != target_card_id][:remaining]
                setup["stage"] = (current_stage + others + [-1] * 3)[:3]

            elif c_type == C_COUNT_DISCARD:
                count = val if is_pass else max(0, val - 1)
                setup["discard"] = member_ids[10 : 10 + count]

            elif c_type == C_COUNT_ENERGY:
                setup["energy_count"] = val if is_pass else max(0, val - 1)

            elif c_type == C_HAS_LIVE:
                if not is_pass:
                    setup["live"] = []

        return setup

    print("Generating scenarios...")
    seen_scenarios = set()

    for card_id, card in members.items():
        card_no = card.get("card_no", "")
        raw_card = raw_lookup.get(card_no, {})
        jp_full_text = raw_card.get("ability", "N/A")

        for ab_idx, ability in enumerate(card.get("abilities", [])):
            bytecode = ability.get("bytecode", [])
            # if not bytecode: continue # Some abilities might be purely passive without bytecode? checking..

            sig = tuple(bytecode)
            trigger_type = ability.get("trigger", 0)

            unique_key = (sig, card_no, ab_idx, trigger_type)
            if unique_key in seen_scenarios:
                continue
            seen_scenarios.add(unique_key)

            conditions = ability.get("conditions", [])

            # Determine target slot based on conditions
            target_slot_idx = 0
            is_center_req = False
            for cond in conditions:
                raw_cond = cond.get("params", {}).get("raw_cond")
                if cond.get("type") == 206 or raw_cond == "IS_CENTER":  # C_IS_CENTER
                    is_center_req = True
                    target_slot_idx = 1
                    break

            # Action Mapping
            action = {
                "type": "FORCE_TRIGGER",
                "trigger_type": trigger_type,
                "slot_idx": target_slot_idx,
                "ab_idx": ab_idx,
            }

            if trigger_type == T_ON_PLAY:
                action = {"type": "PLAY_MEMBER", "hand_idx": 0, "slot_idx": target_slot_idx}
            elif trigger_type == T_ACTIVATED:
                action = {"type": "MANUAL_ABILITY", "slot_idx": target_slot_idx, "ab_idx": ab_idx}
            elif trigger_type == T_CONSTANT:
                # Constants don't "trigger" via action usually, but FORCE_TRIGGER works for testing effects
                # checks usually happen on state update.
                # For verification, we might need a specific action to "check" valid state?
                # But existing FORCE_TRIGGER logic handles it.
                pass

            # Setup Helper Update
            def get_setup_v2(conds, pass_mode, t_card_id, t_type, t_slot):
                # Default
                s_setup = {
                    "hand": [],
                    "deck": member_ids[5:15],
                    "live": [live_ids[0], live_ids[1]],
                    "discard": [member_ids[2], member_ids[3]],
                    "stage": [-1, -1, -1],
                    "energy_count": 10,
                    "completed_live_count": 0,
                }

                # Default Placement
                if t_type == T_ON_PLAY:
                    s_setup["hand"] = [t_card_id]
                elif t_type in [
                    T_ON_LIVE_START,
                    T_ON_LIVE_SUCCESS,
                    T_TURN_START,
                    T_TURN_END,
                    T_ACTIVATED,
                    T_ON_LEAVES,
                    T_ON_POSITION_CHANGE,
                    T_CONSTANT,
                ]:
                    s_setup["stage"][t_slot] = t_card_id
                    s_setup["hand"] = [member_ids[0]]  # Dummy hand

                # Condition Applying
                for c in conds:
                    ct = c.get("type")
                    val = c.get("value", 1)
                    if isinstance(val, str):
                        val = 1

                    if ct == C_COUNT_HAND:
                        # Ensure we have enough cards in hand
                        needed = val if pass_mode else max(0, val - 1)
                        # If ON_PLAY, we already have target in hand (or should).
                        # If t_card_id in hand, it counts.
                        current_hand = s_setup["hand"][:]
                        if len(current_hand) < needed:
                            diff = needed - len(current_hand)
                            # Add dummies
                            for i in range(diff):
                                s_setup["hand"].append(member_ids[(i + 10) % len(member_ids)])

                        if not pass_mode and len(s_setup["hand"]) >= val:
                            # Must reduce to fail
                            s_setup["hand"] = s_setup["hand"][: val - 1]

                    elif ct == C_COUNT_STAGE:
                        needed = val if pass_mode else max(0, val - 1)
                        # We have target at t_slot (if not ON_PLAY).
                        # Fill other slots
                        count = 0
                        for x in s_setup["stage"]:
                            if x != -1:
                                count += 1

                        if count < needed:
                            diff = needed - count
                            placed = 0
                            for i in range(3):
                                if s_setup["stage"][i] == -1 and placed < diff:
                                    s_setup["stage"][i] = member_ids[(i + 5) % len(member_ids)]  # Dummy
                                    placed += 1

                        if not pass_mode and count >= val:
                            # Remove dummies to fail?
                            # Hard to remove specific ones without removing target.
                            # Just ensure we DON'T add more.
                            # If we naturally have >= val (e.g. target + others), we might need to remove target? But that invalidates test.
                            # For FAIL case of C_COUNT_STAGE, we assume "Pass" means >= X. Fail means < X.
                            # So we just ensure count < val.
                            # If target is on stage, count is at least 1.
                            # If val is 1, we can't fail unless we remove target (which might stop trigger).
                            # So C_COUNT_STAGE 1 FAIL is impossible for ON_STAGE triggers.
                            pass

                    elif ct == 206 or c.get("params", {}).get("raw_cond") == "IS_CENTER":  # C_IS_CENTER
                        # Handled by t_slot, but for FAIL case:
                        if not pass_mode:
                            # Move to side if possible
                            if t_slot == 1:
                                # We forced it to 1. Check if we can move to 0 or 2.
                                # But setup logic above used t_slot.
                                # So we should have passed t_slot=0 for FAIL case of Center?
                                pass

                    elif ct == C_COUNT_ENERGY:
                        s_setup["energy_count"] = val if pass_mode else max(0, val - 1)

                    elif ct == 218:  # C_SCS_LIV (Success Live Count)
                        s_setup["completed_live_count"] = val if pass_mode else max(0, val - 1)

                return s_setup

            # Determine slot for PASS/FAIL
            # Pass Case: Use target_slot_idx (which respects Center)
            pass_slot = target_slot_idx

            # Fail Case: If Center is required, put in Side (0)
            fail_slot = target_slot_idx
            if is_center_req:
                fail_slot = 0 if target_slot_idx == 1 else 1  # Move away from required slot

            # Pass Case
            scenarios.append(
                {
                    "id": f"{card_no}_ab{ab_idx}_PASS",
                    "signature": bytecode,
                    "scenario_name": f"Pass Case: {card_no} Ab {ab_idx} T{trigger_type}",
                    "original_text_jp": jp_full_text,
                    "real_card_id": int(card_id),
                    "setup": get_setup_v2(conditions, True, int(card_id), trigger_type, pass_slot),
                    "action": {**action, "slot_idx": pass_slot}
                    if action["type"] != "PLAY_MEMBER"
                    else {**action, "slot_idx": pass_slot},
                    "choices": [0] * 10,
                    "expect": {"is_pass": True},
                }
            )

            # Fail Case (only if conditions exist)
            if conditions:
                # Update action slot for fail case
                fail_action = action.copy()
                if fail_action["type"] != "PLAY_MEMBER":
                    fail_action["slot_idx"] = fail_slot
                else:
                    fail_action["slot_idx"] = fail_slot

                scenarios.append(
                    {
                        "id": f"{card_no}_ab{ab_idx}_FAIL",
                        "signature": bytecode,
                        "scenario_name": f"Fail Case: {card_no} Ab {ab_idx} T{trigger_type}",
                        "original_text_jp": jp_full_text,
                        "real_card_id": int(card_id),
                        "setup": get_setup_v2(conditions, False, int(card_id), trigger_type, fail_slot),
                        "action": fail_action,
                        "choices": None,
                        "expect": {"is_pass": False},
                    }
                )

    output_data = {"scenarios": scenarios}
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)

    print(f"Generated {len(scenarios)} scenarios in {OUTPUT_PATH}")


if __name__ == "__main__":
    generate_scenarios()
