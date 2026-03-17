import json
import os
import sys

sys.path.append(os.getcwd())
# Re-use logic from auto_verify_semantic to find candidates
from tools.auto_verify_semantic import SAFE_TRIGGERS, SEMANTIC_HANDLERS


def inspect():
    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        full_db = json.load(f)

    candidates = []

    print(f"\nScanning {len(full_db)} cards for semantic candidates...")
    print(f"Allowed Effects: {[h['name'] for h in SEMANTIC_HANDLERS.values()]}")

    # keys are "member_db", "live_db"
    member_db = full_db.get("member_db", {})

    for cid, card in member_db.items():
        if card.get("type") != "member":
            continue

        abilities = card.get("abilities", [])
        if len(abilities) != 1:
            continue

        ab = abilities[0]

        # Check Trigger
        if ab.get("trigger") not in SAFE_TRIGGERS:
            continue

        # Check Conditions (Must be empty or simple)
        conditions = ab.get("conditions", [])
        if len(conditions) > 0:
            continue  # Strictly no conditions for now

        # Check Effects (Single effect, supported handler)
        effects = ab.get("effects", [])
        if len(effects) != 1:
            continue

        eff = effects[0]
        etype = eff.get("effect_type")

        if etype in SEMANTIC_HANDLERS:
            # Check Params safety (exclude complex nested logic for now)
            params = eff.get("params", {})
            # We skip if params has 'condition' or 'target_filter' that looks complex
            # But earlier we relaxed this. Let's just include them for inspection.
            candidates.append((card["card_no"], card.get("name", "Unknown"), ab.get("text", "No Text")))

    print(f"\nFound {len(candidates)} Candidates:\n")
    print(f"{'Card No':<15} | {'Name':<20} | {'Ability Text'}")
    print("-" * 100)
    for cno, name, text in candidates:
        print(f"{cno:<15} | {name[:20]:<20} | {text}")


if __name__ == "__main__":
    inspect()
