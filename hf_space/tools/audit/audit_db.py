import json
import os


def audit_cards(search_patterns, files):
    for f_path in files:
        if not os.path.exists(f_path):
            continue
        print(f"Auditing {f_path}...")
        try:
            with open(f_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            cards = []
            if isinstance(data, list):
                cards = data
            elif isinstance(data, dict):
                # Check for member_db/live_db
                if "member_db" in data:
                    cards.extend(data["member_db"].values())
                if "live_db" in data:
                    cards.extend(data["live_db"].values())
                # If no DB keys, just take values
                if not cards:
                    cards = [v for v in data.values() if isinstance(v, dict)]

            for card in cards:
                cno = str(card.get("card_no", ""))
                name = str(card.get("name", ""))
                for p in search_patterns:
                    if p.lower() in cno.lower() or p.lower() in name.lower():
                        print(f"  Found '{p}' in {f_path}: {cno} ({name})")
        except Exception as e:
            print(f"  Error reading {f_path}: {e}")


if __name__ == "__main__":
    patterns = [
        "PL!S-bp3-029-PE＋",
        "PL!HS-bp1-027-PE＋",
        "PL!HS-bp1-028-PE＋",
        "PL!HS-bp1-029-PE＋",
        "PL!HS-bp1-030-PE＋",
        "PL!HS-bp1-031-PE＋",
        "PL!HS-bp2-030-PE＋",
        "PL!HS-bp2-031-PE＋",
        "PL!HS-bp2-032-PE＋",
        "PL!HS-bp2-033-PE＋",
        "PL!HS-PR-015-PR",
        "PL!SP-pb1-044-SECE",
        "PL!SP-pb1-044-SRE",
        "PL!-bp3-030-PE＋",
        "PL!-sd1-024-P",
        "PL!-sd1-029-P",
        "PL!N-bp1-033-SECE",
        "PL!N-sd1-036-P",
        "PL!S-pb1-028-PE＋",
        "PL!S-pb1-037-SRE",
        "PL!SP-pb1-031-PE＋",
        "PL!SP-pb1-039-SRE",
        "PL!SP-pb1-040-SRE",
        "PL!SP-pb1-041-SRE",
        "PL!SP-pb1-100-LLE",
        "PL!N-bp1-034-PE＋",
    ]
    files = [
        "data/cards_compiled.json",
        "data/temp/simplified_cards.json",
        "data/verified_card_pool.json",
        "engine/data/cards.json",
        "simplified_cards.json",
        "data/cards_numba.json",
    ]
    audit_cards(patterns, files)
