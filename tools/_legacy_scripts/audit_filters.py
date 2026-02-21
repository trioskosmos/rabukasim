import json
import re
import os


def audit_filters():
    cards_path = "data/cards.json"
    if not os.path.exists(cards_path):
        print(f"Error: {cards_path} not found")
        return

    with open(cards_path, "r", encoding="utf-8") as f:
        cards = json.load(f)

    # Patterns for Japanese filter keywords
    # コストN以上 (Cost N or more) -> GE
    # コストN以下 (Cost N or less) -> LE
    # 必要ハートの合計がN以上 (Sum of required hearts is N or more) -> GE
    re_ge = re.compile(r"コスト(\d+)以上")
    re_le = re.compile(r"コスト(\d+)以下")
    re_heart_ge = re.compile(r"必要ハートの合計が(\d+)以上")

    results = []

    for card_id, card in cards.items():
        ability = card.get("ability", "")
        pseudocode = card.get("pseudocode", "")

        # We are specifically looking for LOOK_AND_CHOOSE effects that MIGHT be missing filters
        has_lac = "LOOK_AND_CHOOSE" in pseudocode

        # Check if the pseudocode already has a FILTER for cost
        has_cost_filter = "COST_GE" in pseudocode or "COST_LE" in pseudocode or "COST_LE_REVEALED" in pseudocode

        # Look for matches in Japanese text
        match_ge = re_ge.search(ability)
        match_le = re_le.search(ability)
        match_heart_ge = re_heart_ge.search(ability)

        suspicious = False
        reason = ""

        if (match_ge or match_le or match_heart_ge) and has_lac and not has_cost_filter:
            suspicious = True
            if match_ge:
                reason += f"Found 'コスト{match_ge.group(1)}以上' but no COST_GE in pseudocode. "
            if match_le:
                reason += f"Found 'コスト{match_le.group(1)}以下' but no COST_LE in pseudocode. "
            if match_heart_ge:
                reason += f"Found 'ハート{match_heart_ge.group(1)}以上' but no COST_GE in pseudocode. "

        if suspicious:
            results.append(
                {
                    "id": card_id,
                    "name": card.get("name"),
                    "reason": reason,
                    "ability": ability,
                    "pseudocode": pseudocode,
                }
            )

    print(f"Found {len(results)} suspicious cards.")

    # Sort results by ID for readability
    results.sort(key=lambda x: x["id"])

    with open("reports/filters_audit_report.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Print a summary to console
    for r in results[:10]:
        print(f"[{r['id']}] {r['name']}: {r['reason']}")
    if len(results) > 10:
        print("...")


if __name__ == "__main__":
    audit_filters()
