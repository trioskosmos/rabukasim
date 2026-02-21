import json
import os
import re


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    print("Reading vanilla_deck.md...")
    with open("ai/vanilla_deck.md", "r", encoding="utf-8") as f:
        content = f.read()

    # Extract card codes like [PL!-sd1-010-SD]
    card_codes = re.findall(r"\[(PL!-[^\]]+)\]", content)
    unique_codes = sorted(list(set(card_codes)))
    print(f"Found {len(unique_codes)} unique cards in vanilla_deck.md")

    print("Loading cards_compiled.json...")
    compiled_data = load_json("data/cards_compiled.json")

    member_db = compiled_data.get("member_db", {})
    live_db = compiled_data.get("live_db", {})

    found_members = []
    found_lives = []
    missing = []

    # Structure for verified pool
    new_verified_pool = {"verified_abilities": [], "vanilla_lives": []}

    for code in unique_codes:
        # Check Member DB
        found = False
        for cid, data in member_db.items():
            if data["card_no"] == code:
                found_members.append(code)
                # Check abilities
                abilities = data.get("abilities", [])
                print(f"Member {code}: {len(abilities)} abilities")
                # If it has abilities, add to verified_abilities
                # Even vanilla cards might need to be in the list if the env logic requires it?
                # The prompt says "make sure all cards are properly verified".
                # Usually verifying implies "this card is safe to use".
                new_verified_pool["verified_abilities"].append(code)
                found = True
                break

        if not found:
            # Check Live DB
            for cid, data in live_db.items():
                if data["card_no"] == code:
                    found_lives.append(code)
                    print(f"Live {code}: Score {data.get('score', '?')}")
                    if data.get("abilities"):
                        with open("debug_lives.txt", "a", encoding="utf-8") as debug_f:
                            debug_f.write(f"Live {code} has {len(data['abilities'])} abilities:\\n")
                            for ab in data["abilities"]:
                                debug_f.write(f"    - {ab.get('raw_text', 'No Text')}\\n")
                                debug_f.write(
                                    f"      Trigger: {ab.get('trigger')}, Effects: {len(ab.get('effects', []))}\\n"
                                )
                        new_verified_pool["verified_abilities"].append(code)
                    else:
                        print("  No abilities (Vanilla Live)")
                        new_verified_pool["vanilla_lives"].append(code)

                    found = True
                    break

        if not found:
            missing.append(code)

    print("-" * 20)
    print(f"Found Members: {len(found_members)}")
    print(f"Found Lives: {len(found_lives)}")
    print(f"Missing: {len(missing)}")
    if missing:
        print("Missing Codes:", missing)

    # Backup current verified pool
    if os.path.exists("data/verified_card_pool.json"):
        if not os.path.exists("data/verified_card_pool.json.bak"):
            print("Backing up verified_card_pool.json...")
            with open("data/verified_card_pool.json", "r", encoding="utf-8") as f:
                old_pool = f.read()
            with open("data/verified_card_pool.json.bak", "w", encoding="utf-8") as f:
                f.write(old_pool)

    # Save new pool
    print("Writing new verified_card_pool.json...")
    with open("data/verified_card_pool.json", "w", encoding="utf-8") as f:
        json.dump(new_verified_pool, f, indent=2)

    print("Done.")


if __name__ == "__main__":
    main()
