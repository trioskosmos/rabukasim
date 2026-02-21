"""
Smart scanner to find all cards affected by recent parser fixes.
Groups cards by the type of fix that applies to them.
"""

import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")


def scan():
    with open("c:/Users/trios/.gemini/antigravity/scratch/loveca-copy/data/cards.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    cards = list(data.values()) if isinstance(data, dict) else data

    fixes = {
        "Area-Specific Members": {
            "pattern": r"(右サイドエリア|左サイドエリア|センターエリア)に「.*?」",
            "description": "Cards requiring specific members in specific stage areas",
            "matches": [],
        },
        "Trigger vs Condition (登場している)": {
            "pattern": r"登場している場合",
            "description": "Cards with '登場している場合' that was being mistaken for ON_PLAY trigger",
            "matches": [],
        },
        "Multi-line Modal Branches": {
            "pattern": r"回答が.*?の場合",
            "description": "Cards with modal answer branches (flavor questions)",
            "matches": [],
        },
        "Zone-Restricted Group Checks": {
            "pattern": r"(成功ライブカード置き場|エネルギー置き場|控え室)に『.*?』",
            "description": "Cards checking for groups in specific zones (not just Stage)",
            "matches": [],
        },
        "Negation Conditions": {
            "pattern": r"(以外|でない場合|ではない場合)",
            "description": "Cards with negated conditions (Except X, If NOT X)",
            "matches": [],
        },
        "Optional Effects (てもよい)": {
            "pattern": r"てもよい",
            "description": "Cards with optional effects (may instead of must)",
            "matches": [],
        },
        # NEW PATTERNS BELOW
        "Cost Reduction": {
            "pattern": r"コスト.*(減|－|ー|\-\d)",
            "description": "Cards that reduce play costs",
            "matches": [],
        },
        "Effect Multipliers (枚につき)": {
            "pattern": r"(枚につき|人につき|ごとに)",
            "description": "Cards with per-card/per-member multiplier effects",
            "matches": [],
        },
        "Turn-Based Duration": {
            "pattern": r"(ターン終了時まで|ライブ終了時まで|このターン)",
            "description": "Cards with temporary effects that expire",
            "matches": [],
        },
        "Specific Card Name Condition": {
            "pattern": r"「[^」]+」(が|の)(ある|いる|登場)",
            "description": "Cards checking for specific named members (not groups)",
            "matches": [],
        },
        "Deck Manipulation (Top/Bottom)": {
            "pattern": r"(デッキの上|デッキの下|一番上|一番下)",
            "description": "Cards that interact with specific deck positions",
            "matches": [],
        },
        "Self-Referential (このカード/このメンバー)": {
            "pattern": r"(このカード|このメンバー|このライブカード)",
            "description": "Cards that modify themselves",
            "matches": [],
        },
        "Opponent Targeting": {
            "pattern": r"相手の(メンバー|ステージ|手札|ライブ)",
            "description": "Cards that interact with opponent's board/hand",
            "matches": [],
        },
        "Energy Cost Requirements": {
            "pattern": r"エネルギー.*(消費|払|使)",
            "description": "Cards with energy cost mechanics",
            "matches": [],
        },
        "Attribute/Heart Color Requirements": {
            "pattern": r"heart_\d+\.png",
            "description": "Cards checking for specific heart colors",
            "matches": [],
        },
    }

    for card in cards:
        if not isinstance(card, dict):
            continue
        ability = card.get("ability", "")
        if not ability:
            continue

        for fix_name, fix_info in fixes.items():
            if re.search(fix_info["pattern"], ability):
                fix_info["matches"].append(
                    {"id": card.get("card_no"), "name": card.get("name"), "snippet": ability[:80].replace("\n", " / ")}
                )

    # Report
    with open("fixed_cards_report.txt", "w", encoding="utf-8") as out:
        out.write("=" * 60 + "\n")
        out.write("PARSER FIX IMPACT REPORT\n")
        out.write("=" * 60 + "\n")

        total_fixed = 0
        for fix_name, fix_info in fixes.items():
            count = len(fix_info["matches"])
            total_fixed += count
            out.write(f"\n## {fix_name}: {count} cards\n")
            out.write(f"   {fix_info['description']}\n")
            for m in fix_info["matches"][:5]:  # Show top 5 examples
                out.write(f"   - [{m['id']}] {m['name']}: {m['snippet']}...\n")
            if count > 5:
                out.write(f"   ... and {count - 5} more\n")

        out.write(f"\n{'=' * 60}\n")
        out.write(f"TOTAL CARDS BENEFITING FROM FIXES: {total_fixed}\n")
        out.write("=" * 60 + "\n")

    print(f"Report written to fixed_cards_report.txt ({total_fixed} cards)")


if __name__ == "__main__":
    scan()
