import json
import re


def parse_deck_debug(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    print(f"Content length: {len(content)}")
    print(f"Content sample: {repr(content[:100])}")

    matches = re.findall(r"([A-Za-z0-9!+\-＋]+)\s*[xX]\s*(\d+)", content)
    print(f"Found {len(matches)} matches")
    for i, m in enumerate(matches):
        print(f"Match {i}: {m}")


def test():
    cards_path = "data/cards_compiled.json"
    with open(cards_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    card_map = {}
    for cid, cdata in data["member_db"].items():
        card_map[cdata["card_no"]] = int(cid)
    for cid, cdata in data["live_db"].items():
        card_map[cdata["card_no"]] = int(cid)

    for k in list(card_map.keys()):
        if "+" in k:
            card_map[k.replace("+", "＋")] = card_map[k]
        if "＋" in k:
            card_map[k.replace("＋", "+")] = card_map[k]

    deck_path = "ai/decks/aqours_cup.txt"
    parse_deck_debug(deck_path)

    # Check Energy identification
    test_no = "PL!S-bp3-029-PE＋"
    cid = card_map.get(test_no)
    print(f"Test card: {test_no} -> CID: {cid}")
    if cid is not None:
        cdata = data["live_db"].get(str(cid)) or data["member_db"].get(str(cid))
        print(f"CData rare: {cdata.get('rare')}")
        print(f"CData name: {repr(cdata.get('name'))}")


test()
