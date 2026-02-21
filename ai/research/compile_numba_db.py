import json
import os
import sys

# Ensure project root is in path
sys.path.append(os.getcwd())

from engine.models.ability import (
    Ability,
    AbilityCostType,
    Condition,
    ConditionType,
    Cost,
    Effect,
    EffectType,
    TargetType,
    TriggerType,
)


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def reconstruct_ability(data):
    """Reconstruct Ability object from JSON dict."""
    effects = []
    for eff_data in data.get("effects", []):
        effects.append(
            Effect(
                effect_type=EffectType(eff_data["effect_type"]),
                value=eff_data.get("value", 0),
                target=TargetType(eff_data.get("target", 0)),
                params=eff_data.get("params", {}),
                is_optional=eff_data.get("is_optional", False),
            )
        )

    conditions = []
    for cond_data in data.get("conditions", []):
        conditions.append(
            Condition(
                type=ConditionType(cond_data["type"]),
                params=cond_data.get("params", {}),
                is_negated=cond_data.get("is_negated", False),
            )
        )

    costs = []
    for cost_data in data.get("costs", []):
        costs.append(
            Cost(
                type=AbilityCostType(cost_data["type"]),
                value=cost_data.get("value", 0),
                params=cost_data.get("params", {}),
                is_optional=cost_data.get("is_optional", False),
            )
        )

    return Ability(
        raw_text=data.get("raw_text", ""),
        trigger=TriggerType(data.get("trigger", 0)),
        effects=effects,
        conditions=conditions,
        costs=costs,
        is_once_per_turn=data.get("is_once_per_turn", False),
    )


def main():
    print("--- Compiling Cards to Numba Bytecode ---")

    # Load Data
    compiled_data = load_json("data/cards_compiled.json")
    verified_pool = load_json("data/verified_card_pool.json")

    # Target Lists
    target_ids = []

    # Handle list-format or dict-format verified_card_pool.json
    if isinstance(verified_pool, dict):
        verified_abilities = verified_pool.get("verified_abilities", [])
    else:
        verified_abilities = verified_pool

    # Pre-search map
    cid_map = {}
    for cid, card in compiled_data.get("member_db", {}).items():
        cid_map[card["card_no"]] = cid
    for cid, card in compiled_data.get("live_db", {}).items():
        cid_map[card["card_no"]] = cid

    for card_no in verified_abilities:
        # Find ID by card_no
        if card_no in cid_map:
            target_ids.append(int(cid_map[card_no]))
        else:
            print(f"Warning: Verified card {card_no} not found in DB.")

    bytecode_map = {}
    stats = {"compiled": 0, "failed": 0, "skipped": 0}

    # Iterate all cards (or just verified?)
    # Let's do ALL cards types found in DB to be safe, but focus reporting on verified.
    # Iterate all cards from both DBs
    all_cards = {}
    all_cards.update(compiled_data.get("member_db", {}))
    all_cards.update(compiled_data.get("live_db", {}))

    for cid, card_data in all_cards.items():
        cid = int(cid)
        # Assuming only 1 main ability for now or handling the first checking trigger?
        # The VM typically applies an action by ID.
        # We need a schema: ActionID -> Bytecode.
        # For now, let's map: CardID_AbilityIndex -> Bytecode

        abilities = card_data.get("abilities", [])
        for i, ab_data in enumerate(abilities):
            try:
                # Reconstruct and Compile
                ability = reconstruct_ability(ab_data)
                bc = ability.compile()

                # Check if non-trivial
                if len(bc) > 4:  # generic empty return is length 4
                    key = f"{cid}_{i}"
                    bytecode_map[key] = bc
                    stats["compiled"] += 1
                else:
                    stats["skipped"] += 1
            except Exception:
                # print(f"Failed to compile card {cid} ability {i}: {e}")
                stats["failed"] += 1

    print("Compilation Complete.")
    print(f"Compiled: {stats['compiled']}")
    print(f"Skipped (Empty/NoOp): {stats['skipped']}")
    print(f"Failed: {stats['failed']}")

    # Save
    out_path = "data/cards_numba.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(bytecode_map, f, indent=0)
    print(f"Saved to {out_path}")


if __name__ == "__main__":
    main()
