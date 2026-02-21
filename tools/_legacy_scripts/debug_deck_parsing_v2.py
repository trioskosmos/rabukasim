import re


def parse_deck_debug(path):
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    print(f"Total lines: {len(lines)}")

    pattern = re.compile(r"([A-Za-z0-9!+\-＋]+)\s*[xX]\s*(\d+)")
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        match = pattern.search(line)
        if match:
            print(f"Line {i + 1} MATCH: {match.groups()} | Original: {repr(line)}")
        else:
            print(f"Line {i + 1} FAIL: {repr(line)}")


def test():
    deck_path = "ai/decks/aqours_cup.txt"
    parse_deck_debug(deck_path)


test()
