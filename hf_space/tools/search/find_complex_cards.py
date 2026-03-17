import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def find_complex_cards():
    with open("engine/data/cards.json", encoding="utf-8") as f:
        data = json.load(f)

    complex_types = [34, 35]  # REPLACE_EFFECT, TRIGGER_REMOTE
    buff_type = 8  # BUFF_POWER
    complex_conds = [9, 26]  # COUNT_GROUP, OPPONENT_ENERGY_DIFF

    found = {"replace": [], "remote": [], "buff": [], "cond": []}

    print(f"Scanning {len(data)} cards...")

    for cid, c in data.items():
        if not c.get("ability"):
            continue

        # We need to look at parsed abilities if available, or just check 'ability' text if we can't easily parse here.
        # Ideally we use the json structure if 'abilities_parsed' is stored there.
        # The engine usually parses on load. Let's look at the raw json structure.
        # If 'abilities_parsed' isn't in JSON, we might need to rely on parsed model.
        # But wait, the previous command showed we can just load the json.
        # Let's assume the JSON *doesn't* have 'abilities_parsed' populated yet if it's raw.
        # Actually, let's use the DataLoader from engine to be safe and get parsed objects.
        pass

    # Better approach: Use DataLoader to get parsed objects
    from engine.game.data_loader import CardDataLoader
    from engine.models.ability import ConditionType, EffectType

    loader = CardDataLoader("engine/data/cards.json")
    members, lives, energy = loader.load()

    for cid, card in members.items():
        for ab in card.abilities:
            # Scan effects
            for eff in ab.effects:
                if eff.effect_type == EffectType.REPLACE_EFFECT:
                    found["replace"].append(f"{card.card_no} ({card.name})")
                elif eff.effect_type == EffectType.TRIGGER_REMOTE:
                    found["remote"].append(f"{card.card_no} ({card.name})")
                elif eff.effect_type == EffectType.BUFF_POWER:
                    found["buff"].append(f"{card.card_no} ({card.name}) - Val: {eff.value} Params: {eff.params}")

            # Scan conditions
            for cond in ab.conditions:
                if cond.type in [ConditionType.COUNT_GROUP, ConditionType.OPPONENT_ENERGY_DIFF]:
                    found["cond"].append(f"{card.card_no} ({card.name}) - {cond.type.name}")

    print(f"\nREPLACE_EFFECT cards ({len(found['replace'])}):")
    for c in found["replace"][:5]:
        print(f"  - {c}")

    print(f"\nTRIGGER_REMOTE cards ({len(found['remote'])}):")
    for c in found["remote"][:5]:
        print(f"  - {c}")

    print(f"\nBUFF_POWER cards ({len(found['buff'])}):")
    for c in found["buff"][:5]:
        print(f"  - {c}")

    print(f"\nCOMPLEX_COND cards ({len(found['cond'])}):")
    for c in found["cond"][:5]:
        print(f"  - {c}")


if __name__ == "__main__":
    find_complex_cards()
