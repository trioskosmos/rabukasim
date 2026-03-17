import json
import re


def audit_pseudocode():
    # Group Mapping from engine/models/enums.py
    GROUP_MAP = {"μ's": 0, "Aqours": 1, "虹ヶ咲": 2, "スーパースター": 3, "Liella": 3, "蓮ノ空": 4, "Hasunosora": 4}

    with open("data/cards.json", "r", encoding="utf-8") as f:
        cards_data = json.load(f)

    with open("data/manual_pseudocode.json", "r", encoding="utf-8") as f:
        pseudo_data = json.load(f)

    # Pre-process cards_data for easy lookup
    # Note: cards_data is a dict key: card_no
    card_info = {}
    for card_no, data in cards_data.items():
        # Determine group ID
        group_id = 99  # Default OTHER
        ability_text = data.get("ability", "")

        # Check series/group hints
        if "ラブライブ！" == data.get("series") or "μ's" in ability_text:
            group_id = 0
        elif "サンシャイン" in ability_text or "Aqours" in ability_text:
            group_id = 1
        elif "虹ヶ咲" in ability_text:
            group_id = 2
        elif "スーパースター" in ability_text or "Liella" in ability_text:
            group_id = 3
        elif "蓮ノ空" in ability_text:
            group_id = 4

        # Fallback to card_no prefix if ability doesn't mention it
        if group_id == 99:
            if card_no.startswith("PL!-"):
                group_id = 0
            elif card_no.startswith("PL!S-"):
                group_id = 1
            elif card_no.startswith("PL!N-"):
                group_id = 2  # N is usually Nijigasaki
            elif card_no.startswith("PL!SP-"):
                group_id = 3  # SP is Liella
            elif card_no.startswith("PL!HS-"):
                group_id = 4  # HS is Hasuno

        card_info[card_no] = {"group_id": group_id, "ability": ability_text, "name": data.get("name", "")}

    errors = []

    for card_no, p_entry in pseudo_data.items():
        if card_no not in card_info:
            continue

        info = card_info[card_no]
        pseudocode = p_entry.get("pseudocode", "")

        # 1. Check Group ID mismatches
        # Find all GROUP_ID=X in pseudocode
        matches = re.findall(r"GROUP_ID=(\d+)", pseudocode)
        for m in matches:
            found_id = int(m)
            # Some cards might check for OTHER groups, so this isn't 100% an error,
            # but if it's a self-group check or a recovery check, it usually matches.
            # We specifically look for N cards using 3 or 4.
            if card_no.startswith("PL!N-") and found_id in (3, 4):
                errors.append(
                    f"[GROUP_MISMATCH] {card_no}: Pseudocode has GROUP_ID={found_id}, but card is likely Nijigasaki (ID 2)."
                )
            elif card_no.startswith("PL!SP-") and found_id != 3:
                errors.append(
                    f"[GROUP_MISMATCH] {card_no}: Pseudocode has GROUP_ID={found_id}, but card is Liella (ID 3)."
                )

        # 2. Check 004 Collision
        if "004" in card_no:
            # If it's Sumire (SP) but has Umi logic (TAP_OPPONENT)
            if "すみれ" in info["name"] and "TAP_OPPONENT" in pseudocode:
                errors.append(f"[LOGIC_COLLISION] {card_no}: Sumire has Umi logic (TAP_OPPONENT).")
            elif "海未" in info["name"] and "ON_REVEAL" in pseudocode and "YELL" in pseudocode:
                # Umi logic is usually Activated
                pass

    # Save report
    with open("reports/pseudocode_audit.txt", "w", encoding="utf-8") as f:
        for err in errors:
            f.write(err + "\n")

    print(f"Audit complete. Found {len(errors)} potential issues.")


if __name__ == "__main__":
    audit_pseudocode()
