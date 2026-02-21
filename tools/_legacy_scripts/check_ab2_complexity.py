import json


def check_ab2():
    with open("data/cards_compiled.json", encoding="utf-8") as f:
        db = json.load(f)

    all_cards = list(db.get("member_db", {}).values()) + list(db.get("live_db", {}).values())

    cond_on_ab2 = 0
    choice_on_ab2 = 0

    print("Checking for Complexity in Ability 2+...")
    for c in all_cards:
        abs_list = c.get("abilities", [])
        if len(abs_list) > 1:
            for i in range(1, len(abs_list)):
                if abs_list[i].get("conditions"):
                    cond_on_ab2 += 1
                    print(f"Condition on Ab{i + 1}: {c['card_no']} {c.get('name')}")

                for e in abs_list[i].get("effects", []):
                    if e.get("modal_options"):
                        choice_on_ab2 += 1
                        print(f"Choice on Ab{i + 1}: {c['card_no']} {c.get('name')}")

    print(f"\nTotal Cards with Conditions on Ability 2+: {cond_on_ab2}")
    print(f"Total Cards with Choices on Ability 2+: {choice_on_ab2}")


if __name__ == "__main__":
    check_ab2()
