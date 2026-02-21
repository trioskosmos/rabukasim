import json

DATA_FILE = "data/cards_compiled.json"


def scan_for_effect_27():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    with open("scan_output.txt", "w", encoding="utf-8") as out:
        out.write(f"Scanning {len(data.get('member_db', {}))} cards for Effect 27 (LOOK_AND_CHOOSE)...\n")

        found = []

        for cid, card in data.get("member_db", {}).items():
            abilities = card.get("abilities", [])
            for ab in abilities:
                for eff in ab.get("effects", []):
                    if eff.get("effect_type") == 27:
                        found.append(
                            {
                                "id": cid,
                                "no": card.get("card_no"),
                                "text": ab.get("raw_text"),
                                "params": eff.get("params"),
                            }
                        )

        out.write(f"Found {len(found)} cards with Effect 27.\n")
        for c in found:
            out.write(f"\n[{c['no']}] Need: {c['text'][:100]}...\n")
            out.write(f"   Params: {c['params']}\n")

    print("Outpt written to scan_output.txt")


if __name__ == "__main__":
    scan_for_effect_27()
