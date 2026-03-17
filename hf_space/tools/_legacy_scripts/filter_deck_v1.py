import json
import os
import re


def load_verified_cards(log_path):
    verified_cards = set()
    if not os.path.exists(log_path):
        print(f"Warning: {log_path} not found.")
        return verified_cards

    with open(log_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Look for card IDs and their status in MD tables
    # | PL!-sd1-001-SD | Honoka Kosaka | SD01 | **Passed** | ...
    # | PL!-sd1-003-SD | Status | Issue Found | Fix Applied | Impact |
    matches = re.findall(
        r"\|\s*(PL[!-][\w-]+)\s*\|[^|]*\|\s*[^|]*\s*\|\s*\*\*?(Passed|Fixed|Verified|Inherited Fixed|VERIFIED|FIXED)\*\*?\s*\|",
        content,
    )
    for card_no, status in matches:
        verified_cards.add(card_no)

    # Also look for the newer batch format
    # - **PL!N-sd1-027-SD (Just Believe!!!)**: [VERIFIED]
    matches_v2 = re.findall(r"-\s*\*\*?(PL[!-][\w-]+)\s*\(.*?\)\*\*?:\s*\[(VERIFIED|FIXED)\]", content)
    for card_no, status in matches_v2:
        verified_cards.add(card_no)

    print(f"Found {len(verified_cards)} verified cards in log.")
    return verified_cards


def load_vanilla_cards(cards_path):
    vanilla_members = set()
    vanilla_lives = set()
    if not os.path.exists(cards_path):
        print(f"Warning: {cards_path} not found.")
        return vanilla_members, vanilla_lives

    with open(cards_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for card_no, details in data.items():
        ability = details.get("ability", "").strip()
        if not ability:
            if details.get("type") == "ライブ":
                vanilla_lives.add(card_no)
            else:
                vanilla_members.add(card_no)

    print(f"Found {len(vanilla_members)} vanilla members and {len(vanilla_lives)} vanilla lives in cards.json.")
    return vanilla_members, vanilla_lives


def main():
    root = r"C:\Users\trios\.gemini\antigravity\vscode\loveca-copy"
    log_path = os.path.join(root, "engine", "tests", "cards", "card_verification_log.md")
    cards_path = os.path.join(root, "engine", "data", "cards.json")
    deck_path = os.path.join(root, "training_deck_v1.json")

    verified = load_verified_cards(log_path)
    vanilla_members, vanilla_lives = load_vanilla_cards(cards_path)

    # We should also know which verified cards are members vs lives
    # For now, we'll verify them against the full cards.json
    with open(cards_path, "r", encoding="utf-8") as f:
        master_data = json.load(f)

    allowed_members = vanilla_members.copy()
    allowed_lives = vanilla_lives.copy()

    for v_no in verified:
        details = master_data.get(v_no, {})
        if details.get("type") == "ライブ":
            allowed_lives.add(v_no)
        else:
            allowed_members.add(v_no)

    print(f"Total allowed: {len(allowed_members)} members, {len(allowed_lives)} lives")

    # Prioritize Verified Cards: 4 copies each
    new_members = []
    new_lives = []

    # 1. Add Verified Members
    verified_members = [c for c in verified if c in master_data and master_data[c].get("type") != "ライブ"]
    for v_no in verified_members:
        if len(new_members) < 48:
            copies = min(4, 48 - len(new_members))
            new_members.extend([v_no] * copies)

    # 2. Add Verified Lives
    verified_lives = [c for c in verified if c in master_data and master_data[c].get("type") == "ライブ"]
    for v_no in verified_lives:
        if len(new_lives) < 12:
            copies = min(3, 12 - len(new_lives))  # Max 3 for lives usually, but let's stick to 3 or 4 if requested
            new_lives.extend([v_no] * copies)

    # 3. Fill remaining with Vanilla Members
    vanilla_member_list = list(vanilla_members)
    import random

    random.shuffle(vanilla_member_list)

    while len(new_members) < 48 and vanilla_member_list:
        v_no = vanilla_member_list.pop(0)
        copies = min(4, 48 - len(new_members))
        new_members.extend([v_no] * copies)

    # 4. Fill remaining with Vanilla Lives
    vanilla_live_list = list(vanilla_lives)
    random.shuffle(vanilla_live_list)
    while len(new_lives) < 12 and vanilla_live_list:
        v_no = vanilla_live_list.pop(0)
        copies = min(3, 12 - len(new_lives))
        new_lives.extend([v_no] * copies)

    print(f"Final deck composition: {len(new_members)} members, {len(new_lives)} lives")
    print(f"Unique verified members included: {len(set(new_members) & set(verified))}")

    deck = {"members": new_members[:48], "lives": new_lives[:12]}

    with open(deck_path, "w", encoding="utf-8") as f:
        json.dump(deck, f, indent=2, ensure_ascii=False)

    print("Updated training_deck_v1.json with 4x verified cards successfully.")

    # Also save verified_card_pool.json for random_verified mode
    pool_path = os.path.join(root, "verified_card_pool.json")
    pool = {
        "verified_abilities": list(verified),
        "vanilla_members": list(vanilla_members),
        "vanilla_lives": list(vanilla_lives),
    }
    with open(pool_path, "w", encoding="utf-8") as f:
        json.dump(pool, f, indent=2, ensure_ascii=False)
    print(f"Updated {pool_path} successfully.")


if __name__ == "__main__":
    main()
