with open("engine/data/cards.json", "r", encoding="utf-8") as f:
    lines = f.readlines()

target = '"card_no": "PL!S-PR-027-PR"'
for i, line in enumerate(lines):
    if target in line:
        # Check if it's a key definition (approximate check by looking at indentation or previous line)
        # Actually just print all matches with context
        print(f"Line {i + 1}: {line.strip()}")
        if i > 0:
            print(f"  Prev: {lines[i - 1].strip()}")
