#!/usr/bin/env python3
"""
find_parsing_issues.py

Scans cards_compiled.json to find cards with potentially missing or malformed
abilities by comparing ability_text keywords to parsed effect types.
"""

import json
import re
from pathlib import Path

# Effect type mapping (from engine/models/ability.py)
EFFECT_TYPES = {
    "DRAW": [0, 11],  # DRAW or SWAP_CARDS
    "ADD_BLADES": 1,
    "ADD_HEARTS": 2,
    "REDUCE_HEART_REQ": 36,
    "BOOST_SCORE": 6,
    "ADD_TO_HAND": 30,
    "BUFF_POWER": 8,
    "RECOVER_LIVE": 5,
    "RECOVER_MEMBER": 7,
    "IMMUNITY": 9,
    "REDUCE_COST": 3,
    "LOOK_DECK": 4,
    "SEARCH_DECK": 12,
    "ENERGY_CHARGE": 13,
    "REVEAL_CARDS": 26,  # 公開
    "LOOK_AND_CHOOSE": 27,  # 見る、その中から
    "CHEER_REVEAL": 28,  # エールにより公開
    "ACTIVATE_MEMBER": 29,
    "MOVE_MEMBER": 10,
    "PLACE_UNDER": 20,
    "TAP_MEMBER": [40, 19],  # TAP_MEMBER or TAP_OPPONENT
    "ORDER_DECK": 15,
}

# Keywords to look for in ability_text
KEYWORD_TO_EFFECT = {
    "スコアを＋": "BOOST_SCORE",
    "スコア＋": "BOOST_SCORE",
    "+1": "BOOST_SCORE",
    "引く": "DRAW",
    "ドロー": "DRAW",
    "ハートを得る": "ADD_HEARTS",
    "ブレードを得る": "ADD_BLADES",
    "ブレード}}を得る": "ADD_BLADES",
    "ブレード＋": "ADD_BLADES",
    "ブレード+": "ADD_BLADES",
    "必要ハートを": "REDUCE_HEART_REQ",
    "必要ハートは": "REDUCE_HEART_REQ",
    "アクティブにする": "ACTIVATE_MEMBER",
    "移動させ": "MOVE_MEMBER",
    "下に置": "PLACE_UNDER",
    "ウェイトにする": "TAP_MEMBER",
    "順番でデッキの上に置く": "ORDER_DECK",
}


def load_cards(data_dir: Path):
    compiled_path = data_dir / "cards_compiled.json"
    with open(compiled_path, "r", encoding="utf-8") as f:
        return json.load(f)


def check_card(card: dict) -> list[str]:
    """Returns a list of issues found for this card."""
    issues = []
    ability_text = card.get("ability_text", "")
    abilities = card.get("abilities", [])

    # Skip cards with no ability text
    if not ability_text.strip():
        return issues

    # Issue 1: Non-empty ability_text but empty abilities list
    if not abilities:
        # Check if it's a rule reminder (parenthetical text only)
        if re.match(r"^\s*\(.*\)\s*$", ability_text, re.DOTALL):
            # Parenthetical text should still generate effects for icon-based rules
            if "icon_score" in ability_text.lower() or "icon_draw" in ability_text.lower():
                issues.append("Parenthetical rule text not parsed (has icons)")
        else:
            issues.append("Empty abilities with non-empty text")
        return issues

    # Issue 2: Text-vs-Effect Mismatch
    parsed_effect_types = set()
    parsed_cost_types = set()

    def collect_effects(eff_list):
        for eff in eff_list:
            parsed_effect_types.add(eff.get("effect_type"))
            if "modal_options" in eff:
                for opt in eff["modal_options"]:
                    collect_effects(opt)

    for ab in abilities:
        collect_effects(ab.get("effects", []))
        for opt in ab.get("modal_options", []):
            collect_effects(opt)
        for cost in ab.get("costs", []):
            parsed_cost_types.add(cost.get("type"))

    for keyword, expected_effect in KEYWORD_TO_EFFECT.items():
        if keyword in ability_text:
            expected_types = EFFECT_TYPES.get(expected_effect)
            if isinstance(expected_types, int):
                expected_types = [expected_types]

            # Special handling for TAP_MEMBER: "ウェイトにする" can be Effect(TAP_MEMBER) or Cost(TAP_SELF)
            if expected_effect == "TAP_MEMBER":
                # Check for Cost(TAP_SELF=2) or Cost(TAP_MEMBER=20)
                if 2 in parsed_cost_types or 20 in parsed_cost_types:
                    continue

            # Special handling for PLACE_UNDER: "下に置" can be MOVE_TO_DECK(18), ORDER_DECK(15), or Cost(SACRIFICE_UNDER=7?)
            # or generic cost (e.g. Place under deck as cost)
            if expected_effect == "PLACE_UNDER":
                # If "Deck" or "Stack" is involved, generic Place Under is not expected
                if "デッキ" in ability_text or "山札" in ability_text:
                    # Accept MOVE_TO_DECK(18) or ORDER_DECK(15) or RETURN_DECK(various)
                    # Also accept Cost types related to Deck Return: 29, 30, 45, 53, 60, 63, 102, 106
                    deck_ops = {18, 15, 29, 30, 45, 53, 60, 63, 102, 106}
                    if any(t in parsed_effect_types for t in deck_ops) or any(t in parsed_cost_types for t in deck_ops):
                        continue
                # Also check if it's a cost like "Place under deck" (unlikely specific cost type unless logic handles it)
                # But if we see "：", it might be cost.
                # Relax checks if we detected valid effects that match "Place" semantics in context

            # Check if any expected effect type is present
            if not any(et in parsed_effect_types for et in expected_types):
                # Final fallback for misclassified triggers or complex costs
                if expected_effect == "PLACE_UNDER" and "コスト" in ability_text:
                    # If "Cost" is mentioned, maybe it's a cost we missed or handled as generic
                    pass
                else:
                    issues.append(f"Missing {expected_effect} (keyword: '{keyword}')")

    # Issue 3: Trigger Mismatch
    # Use negative lookahead to ignore "常時" abilities that mention other triggers as conditions
    # e.g. "能力も【...】能力も持たない" or "能力を持たない"
    if "ライブ成功時" in ability_text or "【ライブ成功時】" in ability_text:
        if re.search(r"能力も.*?持たない", ability_text) or "能力を持たない" in ability_text:
            pass  # False positive
        else:
            # TriggerType.ON_LIVE_SUCCESS = 3
            has_success_trigger = any(ab.get("trigger") == 3 for ab in abilities)
            if not has_success_trigger:
                issues.append("Trigger mismatch: ライブ成功時 in text but not parsed as ON_LIVE_SUCCESS (3)")

    return issues


def main():
    # Determine paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    data_dir = project_root / "engine" / "data"

    print(f"Loading cards from: {data_dir / 'cards_compiled.json'}")
    data = load_cards(data_dir)

    # Correct keys based on file inspection
    members = data.get("member_db", {})
    lives = data.get("live_db", {})

    print(f"Scanning {len(members)} members and {len(lives)} lives...\n")

    issues_found = []

    for cid, card in members.items():
        card_issues = check_card(card)
        if card_issues:
            issues_found.append(
                {
                    "card_no": card.get("card_no", cid),
                    "name": card.get("name", "Unknown"),
                    "type": "member",
                    "issues": card_issues,
                }
            )

    for cid, card in lives.items():
        card_issues = check_card(card)
        if card_issues:
            issues_found.append(
                {
                    "card_no": card.get("card_no", cid),
                    "name": card.get("name", "Unknown"),
                    "type": "live",
                    "issues": card_issues,
                }
            )

    # Output results
    report_path = project_root / "docs" / "parsing_issues_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Parsing Issues Report\n\n")
        f.write(f"Found {len(issues_found)} cards with potential issues:\n\n")
        f.write("| Card No. | Name | Type | Issues |\n")
        f.write("| :--- | :--- | :--- | :--- |\n")
        for item in issues_found:
            issues_str = "; ".join(item["issues"])
            f.write(f"| {item['card_no']} | {item['name']} | {item['type']} | {issues_str} |\n")

    print(f"Report saved to {report_path}")
    return issues_found


if __name__ == "__main__":
    main()
