import json
from dataclasses import asdict

from compiler.parser import AbilityParser


def check_batch_parsing():
    parser = AbilityParser()

    with open("pending_easy_wins.json", "r", encoding="utf-8") as f:
        easy_wins = json.load(f)

    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        db = json.load(f)

    batch_nos = [card["id"] for card in easy_wins[82:132]]

    # Create No -> CID mapping
    no_to_cid = {}
    for cid, card in db["member_db"].items():
        no_to_cid[card["card_no"]] = cid
    for cid, card in db["live_db"].items():
        no_to_cid[card["card_no"]] = cid

    print(f"Analyzing {len(batch_nos)} cards for Batch 3...")

    results = []
    for cno in batch_nos:
        cid = no_to_cid.get(cno)
        if not cid:
            # Try fuzzy match (ignore spaces and dashes?)
            fuzzy_no = cno.replace("-", "").replace(" ", "").replace("!", "")
            for db_no, db_cid in no_to_cid.items():
                if db_no.replace("-", "").replace(" ", "").replace("!", "") == fuzzy_no:
                    cid = db_cid
                    break

        if not cid:
            print(f"Warning: Card {cno} not found in DB")
            continue

        card = db["member_db"].get(cid) or db["live_db"].get(cid)
        if not card:
            print(f"Warning: Card {cid} not found in DB")
            continue

        # Re-parse to check quality
        text = card.get("ability_text", "")
        abilities = []
        for ab_text in text.split("\n"):
            if not ab_text.strip():
                continue
            try:
                parsed_list = parser.parse(ab_text)
                abilities.append({"text": ab_text, "parsed": [asdict(a) for a in parsed_list] if parsed_list else []})
            except Exception as e:
                print(f"Error parsing text for {cid}: {ab_text}")
                print(f"Exception: {e}")
                abilities.append({"text": ab_text, "error": str(e)})

        results.append({"id": cid, "card_no": card["card_no"], "name": card["name"], "abilities": abilities})

    with open("batch3_parsing_check.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("Results saved to batch3_parsing_check.json")


if __name__ == "__main__":
    check_batch_parsing()
