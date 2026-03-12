import json
import os

PROJECT_ROOT = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy"


def normalize_simple(code):
    if not code:
        return ""
    return code.replace("＋", "+").replace("－", "-").replace("ー", "-").strip()


def normalize_upper(code):
    if not code:
        return ""
    return code.replace("＋", "+").replace("－", "-").replace("ー", "-").strip().upper()


def main():
    cards_path = os.path.join(PROJECT_ROOT, "data", "cards.json")
    if not os.path.exists(cards_path):
        print("cards.json not found")
        return

    with open(cards_path, "r", encoding="utf-8") as f:
        card_db = json.load(f)

    db_nos_simple = set()
    db_nos_upper = set()

    for k, v in card_db.items():
        if isinstance(v, dict) and "card_no" in v:
            c_no = v["card_no"]
            db_nos_simple.add(normalize_simple(c_no))
            db_nos_upper.add(normalize_upper(c_no))

    deck_path = os.path.join(PROJECT_ROOT, "ai", "decks2", "vividworld.txt")
    with open(deck_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    print(f"Total Card Templates in DB: {len(db_nos_simple)}")

    matches_simple = 0
    matches_upper = 0
    total_lines = 0

    missing_simple = []

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if " x " in line:
            code = line.split(" x ")[0].strip()
        else:
            code = line

        total_lines += 1
        n_simple = normalize_simple(code)
        n_upper = normalize_upper(code)

        if n_simple in db_nos_simple:
            matches_simple += 1
        else:
            missing_simple.append(code)

        if n_upper in db_nos_upper:
            matches_upper += 1

    print(f"Matches (Simple): {matches_simple} / {total_lines}")
    print(f"Matches (Upper): {matches_upper} / {total_lines}")

    if missing_simple:
        print(f"Missing in Simple but possibly in Upper: {len(missing_simple)}")
        # Check if they are in Upper
        actually_in_db = 0
        for m in missing_simple:
            if normalize_upper(m) in db_nos_upper:
                actually_in_db += 1
        print(f"  Of which are in DB if using Upper: {actually_in_db}")


if __name__ == "__main__":
    main()
