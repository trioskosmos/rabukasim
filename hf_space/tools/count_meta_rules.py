import json


def count_meta_rules():
    compiled_path = "data/cards_compiled.json"
    with open(compiled_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    meta_effect_type = 16
    meta_opcode = 29

    effect_count = 0
    opcode_count = 0
    unique_cards = set()

    # Iterate over members and lives
    for db_name in ["member_db", "live_db"]:
        db = data.get(db_name, {})
        for card_no, card in db.items():
            card_has_meta = False
            for ab in card.get("abilities", []):
                # Count in effects
                for effect in ab.get("effects", []):
                    if effect.get("effect_type") == meta_effect_type:
                        effect_count += 1
                        card_has_meta = True

                # Count in bytecode (every 4th element is opcode)
                bytecode = ab.get("bytecode", [])
                for i in range(0, len(bytecode), 4):
                    if bytecode[i] == meta_opcode:
                        opcode_count += 1
                        card_has_meta = True

            if card_has_meta:
                unique_cards.add(card.get("card_no", card_no))

    with open("tools/meta_summary.txt", "w", encoding="utf-8") as f:
        f.write(f"Effects: {effect_count}\n")
        f.write(f"Opcodes: {opcode_count}\n")
        f.write(f"UniqueCardsCount: {len(unique_cards)}\n")
        f.write("CardIDs:\n")
        for cid in sorted(unique_cards):
            f.write(f"{cid}\n")
    print("Done")


if __name__ == "__main__":
    count_meta_rules()
