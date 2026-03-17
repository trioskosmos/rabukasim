import json


def inspect_card(target_no):
    try:
        with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
            full_db = json.load(f)

        member_db = full_db.get("member_db", {})
        found = False

        for cid, card in member_db.items():
            if card.get("card_no") == target_no:
                with open("inspect_output.txt", "w", encoding="utf-8") as f_out:
                    json.dump(card, f_out, indent=2, ensure_ascii=False)
                print("Dumped to inspect_output.txt")
                found = True
                break

        if not found:
            print(f"Card {target_no} not found in member_db.")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    inspect_card("PL!S-pb1-013-N")
