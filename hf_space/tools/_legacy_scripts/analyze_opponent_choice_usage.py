import json


def analyze_opponent_choice():
    with open("docs/full_ability_coverage.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    count = 0
    for card in data.get("with_ability", []):
        parsed = card.get("parsed")
        if not parsed:
            continue

        # Check conditions
        if "OPPONENT_CHOICE" in parsed.get("conditions", []):
            print(f"Card {card['id']} condition: OPPONENT_CHOICE")
            # We want to see the Condition object params.
            # But coverage.json only stores lists of strings?
            # Wait, the structure in previous turns showed:
            # "conditions": ["GROUP_FILTER", "COST_CHECK"]
            # It seems it converts to string names.
            # I need the raw parsing or need to re-parse to see params.
            # But let's check parsing errors or if ability text gives clues.
            print(f"  Text: {card['ability_text']}")
            count += 1

    print(f"Total OPPONENT_CHOICE usages: {count}")


if __name__ == "__main__":
    analyze_opponent_choice()
