import json
import re
from pathlib import Path


def audit_numbers():
    cards_path = Path("data/cards.json")
    manual_path = Path("data/manual_pseudocode.json")

    if not cards_path.exists() or not manual_path.exists():
        print("Missing data files.")
        return

    with open(cards_path, "r", encoding="utf-8") as f:
        cards_data = json.load(f)

    with open(manual_path, "r", encoding="utf-8") as f:
        manual_pseudocode = json.load(f)

    # Map cards by card_no for fast lookup
    card_map = {}
    for card_id, card in cards_data.items():
        if isinstance(card, dict) and "card_no" in card:
            card_map[card.get("card_no")] = card

    mismatches = []

    for card_no, entry in manual_pseudocode.items():
        pseudocode = entry.get("pseudocode", "")
        card = card_map.get(card_no)

        if not card:
            continue

        original_text = card.get("original_text") or card.get("ability", "")

        # 1. Audit LOOK_AND_CHOOSE(X)
        pc_look = re.search(r"LOOK_AND_CHOOSE\((\d+)\)", pseudocode)
        if pc_look:
            pc_val = int(pc_look.group(1))
            # Text: (\d+)枚見る or (\d+)枚公開 or (\d+)枚を?見て
            text_look = re.search(r"(\d+)枚.*? (見る|見て|公開)", original_text)
            if not text_look:
                # Try without space
                text_look = re.search(r"(\d+)枚(見る|見て|公開)", original_text)

            if text_look:
                text_val = int(text_look.group(1))
                if pc_val != text_val:
                    mismatches.append(
                        {
                            "card_no": card_no,
                            "type": "LOOK_AND_CHOOSE",
                            "pseudocode": pc_val,
                            "original": text_val,
                            "text": original_text,
                            "pc": pseudocode,
                        }
                    )

        # 2. Audit DRAW(X)
        pc_draw = re.search(r"DRAW\((\d+)\)", pseudocode)
        if pc_draw:
            pc_val = int(pc_draw.group(1))
            text_draw = re.search(r"(\d+)枚引", original_text)
            if text_draw:
                text_val = int(text_draw.group(1))
                if pc_val != text_val:
                    mismatches.append(
                        {
                            "card_no": card_no,
                            "type": "DRAW",
                            "pseudocode": pc_val,
                            "original": text_val,
                            "text": original_text,
                            "pc": pseudocode,
                        }
                    )

        # 3. Audit DISCARD(X) / MOVE_TO_DISCARD(X)
        pc_disc = re.search(r"(?:DISCARD_HAND|MOVE_TO_DISCARD)\((\d+)\)", pseudocode)
        if pc_disc:
            pc_val = int(pc_disc.group(1))
            # Text: (\d+)枚.*?控え室
            text_disc = re.search(r"(\d+)枚.*?控え室", original_text)
            if text_disc:
                text_val = int(text_disc.group(1))
                if pc_val != text_val:
                    mismatches.append(
                        {
                            "card_no": card_no,
                            "type": "DISCARD",
                            "pseudocode": pc_val,
                            "original": text_val,
                            "text": original_text,
                            "pc": pseudocode,
                        }
                    )

        # 4. Audit ADD_BLADES(X) / ADD_HEARTS(X)
        pc_add = re.search(r"(?:ADD_BLADES|ADD_HEARTS)\((\d+)\)", pseudocode)
        if pc_add:
            pc_val = int(pc_add.group(1))
            # Text: (\d+)[個つ]
            text_add = re.search(r"(\d+)[個つ]", original_text)
            if text_add:
                text_val = int(text_add.group(1))
                if pc_val != text_val:
                    mismatches.append(
                        {
                            "card_no": card_no,
                            "type": "ADD_RESOURCE",
                            "pseudocode": pc_val,
                            "original": text_val,
                            "text": original_text,
                            "pc": pseudocode,
                        }
                    )

    # Output results
    if mismatches:
        print(f"Found {len(mismatches)} potential numerical discrepancies.")
        with open("audit_results.json", "w", encoding="utf-8") as f:
            json.dump(mismatches, f, ensure_ascii=False, indent=2)
        print("Results saved to audit_results.json")
    else:
        print("No obvious numerical discrepancies found in manual pseudocode.")


if __name__ == "__main__":
    audit_numbers()
