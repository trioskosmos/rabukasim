import json
import re

def detect_mismatches():
    # Load Master Data
    with open("data/cards.json", "r", encoding="utf-8") as f:
        cards_data = json.load(f)

    # Load Manual Pseudocode
    with open("data/manual_pseudocode.json", "r", encoding="utf-8") as f:
        pseudo_data = json.load(f)

    # Flatten cards_data if it's a list or dict of lists
    cards_dict = {}
    if isinstance(cards_data, list):
        for card in cards_data:
            cards_dict[card["id"]] = card
    elif isinstance(cards_data, dict):
        for k, v in cards_data.items():
            if isinstance(v, list):
                for card in v:
                    cards_dict[str(card["id"])] = card
            else:
                cards_dict[k] = v

    mismatches = []

    # Keywords mapping
    trigger_keywords = {
        "登場": "ON_PLAY",
        "ライブ開始時": "ON_LIVE_START",
        "ライブ成功時": "ON_LIVE_SUCCESS",
        "常時": "CONSTANT",
        "起動": "ACTIVATED",
        "自動": "AUTOMATIC", # or ON_LEAVES etc
    }

    group_keywords = {
        "μ's": "GROUP_ID=0",
        "Aqours": "GROUP_ID=1",
        "虹ヶ咲": "GROUP_ID=2",
        "Liella!": "GROUP_ID=3",
        "蓮ノ空": "GROUP_ID=4",
        "A-RISE": "ARISE",
        "SaintSnow": "SAINTSNOW",
        "EdelNote": "EDELNOTE",
        "スリーズブーケ": "スリーズブーケ",
        "DOLLCHESTRA": "DOLLCHESTRA",
        "みらくらぱーく！": "みらくらぱーく",
    }

    for card_id, entry in pseudo_data.items():
        # Ensure card_id is string since keys in pseudo_data are strings
        card = cards_dict.get(str(card_id))
        if not card:
            continue

        jp_text = ""
        abilities = card.get("abilities", [])
        if abilities:
            jp_text = " ".join([a.get("text", "") for a in abilities])
        else:
            jp_text = card.get("ability", "") or card.get("ability_text", "") or card.get("original_text", "") or ""

        pseudo = entry.get("pseudocode", "").upper()

        issues = []

        # Check for trigger mismatches
        for jp_keyword, pseudo_trigger in trigger_keywords.items():
            if jp_keyword in jp_text and pseudo_trigger not in pseudo:
                # Special case: ON_PLAY might be missing in pseudo if it's just effects, 
                # but usually it should be there.
                if pseudo_trigger == "ON_PLAY" and ("EFFECT:" in pseudo or "TRIGGER:" in pseudo):
                    if "ON_PLAY" not in pseudo and "TRIGGER:" in pseudo:
                         issues.append(f"Missing trigger '{pseudo_trigger}' for JP keyword '{jp_keyword}'")
                elif pseudo_trigger != "ON_PLAY":
                    issues.append(f"Missing trigger '{pseudo_trigger}' for JP keyword '{jp_keyword}'")

        # Check for group mismatches
        for group_name, group_id_str in group_keywords.items():
            if group_name in jp_text and group_id_str not in pseudo:
                # If it's a very common group like mu's, it might be implicit or in a filter
                if group_name not in pseudo: # Check literal name too
                    issues.append(f"Missing group reference '{group_name}/{group_id_str}'")

        # Check for score boost mismatches
        matches_jp_score = re.search(r"スコアを[＋+][１1]", jp_text)
        if matches_jp_score and "BOOST_SCORE(1)" not in pseudo and "SCORE_DELTA=1" not in pseudo:
             issues.append("Missing score boost (+1)")

        if issues:
            mismatches.append({
                "id": card_id,
                "card_no": card.get("card_no", "N/A"),
                "issues": issues,
                "jp_text": jp_text,
                "pseudo": pseudo
            })

    output_path = "reports/pseudocode_semantic_mismatches.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(mismatches, f, ensure_ascii=False, indent=2)

    print(f"Detected {len(mismatches)} potential mismatches. Saved to {output_path}")

if __name__ == "__main__":
    detect_mismatches()
