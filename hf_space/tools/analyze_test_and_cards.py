import json


def main():
    try:
        with open("reports/test_output_v4.txt", "r", encoding="utf-8") as f:
            lines = f.readlines()
            print("--- Test Panic Output ---")
            for line in lines[-50:]:
                print(line.rstrip())
    except FileNotFoundError:
        print("No test output found.")

    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        cards = json.load(f)

    print("\n--- Looking for cost <= 2 with ON_PLAY ... ---")
    for cid, c in cards.items():
        if c.get("cost", 99) <= 2:
            for ab in c.get("abilities", []):
                if "ON_PLAY" in ab.get("raw_text", ""):
                    print(f"ID: {cid}, Name: {c['name']}, No: {c['card_no']}")
                    break


if __name__ == "__main__":
    main()
