import json
import sys


def inspect_card(card_no):
    # Load Master Data
    try:
        with open("data/cards.json", "r", encoding="utf-8") as f:
            cards = json.load(f)
    except FileNotFoundError:
        print("Error: data/cards.json not found.")
        return

    target_card = None
    # cards.json is a dict keyed by card_no
    for card in cards.values():
        if card.get("card_no") == card_no:
            target_card = card
            break

    if not target_card:
        print(f"Card {card_no} not found in cards.json")
        return

    print(f"=== Card Details: {card_no} ===")
    print(f"Keys: {list(target_card.keys())}")
    # Try to find an integer ID
    target_id = target_card.get("id")
    if target_id is None:
        target_id = target_card.get("card_id")
    print(f"ID: {target_id}")
    print(f"Name: {target_card.get('name')}")
    print(f"Rarity: {target_card.get('rarity')}")

    abilities = target_card.get("abilities", [])
    print(f"\nAbilities ({len(abilities)}):")
    for i, ab in enumerate(abilities):
        print(f"  [{i}] {ab}")

    # Load Compiled Data
    try:
        with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
            compiled_data = json.load(f)
    except FileNotFoundError:
        print("\nError: data/cards_compiled.json not found.")
        return

    compiled_card = None
    member_db = compiled_data.get("member_db", {})

    # Search by card_no in compiled data
    for cid, data in member_db.items():
        if data.get("card_no") == card_no:
            compiled_card = data
            print(f"Found compiled data for ID {cid}")
            print(f"Ability Text: {data.get('ability_text')}")
            break

    if not compiled_card:
        print(f"\nCard {card_no} not found in cards_compiled.json")
        return

    print(f"\n=== Compiled Bytecode for {card_no} ===")
    compiled_abilities = compiled_card.get("abilities", [])
    for i, ab in enumerate(compiled_abilities):
        trigger = ab.get("trigger")
        bytecode = ab.get("bytecode")
        print(f"Bytecode_Dump_{i}: {bytecode}")

    print("\n=== Analysis ===")
    # Basic opcode check (simplified)
    # O_ACTIVATE_MEMBER = 43
    # TriggerType::Activated = 6 (approx, depending on enum)

    for i, ab in enumerate(compiled_abilities):
        bc = ab.get("bytecode", [])
        trigger = ab.get("trigger")

        # Check for Activated Trigger (usually 6 in Python enum, check parser_v2 or logic.rs)
        # Actually logic.rs TriggerType::Activated is what matters.
        # But we can check if it has bytecode.

        if not bc:
            print(f"  Ability {i}: Empty Bytecode (Likely Not Implemented or Meta Rule)")
        else:
            print(f"  Ability {i}: Has Bytecode (Potentially Active)")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        inspect_card(sys.argv[1])
    else:
        inspect_card("PL!N-bp4-008-R")
