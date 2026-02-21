import json

def verify():
    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    c = data["member_db"]["265"]
    print(f"Card: {c['card_no']}")
    for i, a in enumerate(c["abilities"]):
        print(f"Ability {i}:")
        print(f"  Trigger: {a['trigger']}")
        print(f"  Costs: {a['costs']}")
        print(f"  Effects: {a['effects']}")

if __name__ == "__main__":
    verify()
