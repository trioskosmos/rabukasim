import json


def test_card_map():
    cards_path = "data/cards_compiled.json"
    with open(cards_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    card_map = {}
    for cid, cdata in data["member_db"].items():
        card_map[cdata["card_no"]] = int(cid)
    for cid, cdata in data["live_db"].items():
        card_map[cdata["card_no"]] = int(cid)

    # Check for PL!S-bp3-029-PE variants
    search = "PL!S-bp3-029-PE"
    found = [k for k in card_map.keys() if k.startswith(search)]
    print(f"Variants found for {search}: {found}")

    # Check for specific wide plus variant
    wide_plus = search + "＋"
    print(f"Mapping for {repr(wide_plus)}: {card_map.get(wide_plus)}")

    # Check for normal plus variant
    normal_plus = search + "+"
    print(f"Mapping for {repr(normal_plus)}: {card_map.get(normal_plus)}")


test_card_map()
