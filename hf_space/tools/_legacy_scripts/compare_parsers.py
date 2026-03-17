# -*- coding: utf-8 -*-
"""Compare parser.py (legacy) vs parser_v2 on all cards.

Generates a detailed report of differences to identify gaps.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from compiler.parser import AbilityParser
from compiler.parser_v2 import AbilityParserV2


def load_cards():
    """Load compiled card data and extract ability texts."""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base, "data", "cards_compiled.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    # Extract cards with raw ability text
    cards = {}
    for section in ["member_db", "live_db"]:
        for card_id, card in data.get(section, {}).items():
            if "abilities" in card and card["abilities"]:
                # Get raw_text from first ability
                raw_texts = [a.get("raw_text", "") for a in card["abilities"] if a.get("raw_text")]
                if raw_texts:
                    cards[card.get("card_no", card_id)] = {
                        "ability": "\\n".join(raw_texts),
                        "abilities": card["abilities"],
                        "type": "Live" if section == "live_db" else "Member",
                    }
    return cards


def compare_parsers():
    """Compare legacy vs V2 parser on all cards."""
    cards = load_cards()
    legacy = AbilityParser()
    v2 = AbilityParserV2()

    results = {
        "total": 0,
        "match": 0,
        "v2_better": 0,
        "legacy_better": 0,
        "differences": [],
        "total_member": 0,
        "total_live": 0,
        "match_member": 0,
        "match_live": 0,
        "parsed_member": 0,
        "parsed_live": 0,
    }

    for card_no, card in cards.items():
        ability_text = card.get("ability", "")
        card_type = card.get("type", "Member")
        is_live = card_type == "Live"

        if not ability_text or ability_text.strip() == "":
            continue

        results["total"] += 1
        if is_live:
            results["total_live"] += 1
        else:
            results["total_member"] += 1

        try:
            legacy_result = legacy.parse_ability_text(ability_text)
        except Exception:
            legacy_result = []

        try:
            v2_result = v2.parse(ability_text)
        except Exception:
            print(f"CRASH on card {card_no}: {ability_text}")
            v2_result = []

        if legacy_result is None:
            legacy_result = []
        if v2_result is None:
            v2_result = []

        # Compare results
        legacy_effects = sum(len(a.effects) + len(a.conditions) + len(a.costs) for a in legacy_result)
        legacy_count = len(legacy_result)

        v2_effects = sum(len(a.effects) + len(a.conditions) + len(a.costs) for a in v2_result)
        v2_count = len(v2_result)

        # Simple comparison score
        legacy_score = (
            legacy_effects + sum(len(a.conditions) for a in legacy_result) + sum(len(a.costs) for a in legacy_result)
        )
        v2_score = v2_effects + sum(len(a.conditions) for a in v2_result) + sum(len(a.costs) for a in v2_result)

        if legacy_score == v2_score and legacy_count == v2_count:
            results["match"] += 1
            if is_live:
                results["match_live"] += 1
            else:
                results["match_member"] += 1
        elif v2_score > legacy_score:
            results["v2_better"] += 1
        else:
            results["legacy_better"] += 1
            if len(results["differences"]) < 50:
                results["differences"].append(
                    {
                        "card_no": card_no,
                        "legacy": {"abilities": legacy_count, "effects": legacy_effects},
                        "v2": {"abilities": v2_count, "effects": v2_effects},
                        "text": ability_text[:200],
                    }
                )

        if v2_count > 0:
            if is_live:
                results["parsed_live"] += 1
            else:
                results["parsed_member"] += 1

    return results


def print_report(results):
    """Print comparison report."""
    print("=" * 60)
    print("PARSER COMPARISON REPORT (Member vs Live)")
    print("=" * 60)

    t_mem = results.get("total_member", 0)
    t_liv = results.get("total_live", 0)

    print(f"Total Cards: {results['total']}")
    print(f"  - Members: {t_mem}")
    print(f"  - Lives:   {t_liv}")
    print("-" * 30)
    print("Parsing Coverage (V2 found at least 1 ability):")
    print(
        f"  - Members: {results.get('parsed_member', 0)} / {t_mem} ({100 * results.get('parsed_member', 0) / t_mem if t_mem else 0:.1f}%)"
    )
    print(
        f"  - Lives:   {results.get('parsed_live', 0)} / {t_liv} ({100 * results.get('parsed_live', 0) / t_liv if t_liv else 0:.1f}%)"
    )
    print("-" * 30)
    print("Match Rates (Legacy Parity):")
    print(
        f"  - Members: {results.get('match_member', 0)} / {t_mem} ({100 * results.get('match_member', 0) / t_mem if t_mem else 0:.1f}%)"
    )
    print(
        f"  - Lives:   {results.get('match_live', 0)} / {t_liv} ({100 * results.get('match_live', 0) / t_liv if t_liv else 0:.1f}%)"
    )
    print("-" * 30)
    print(f"Overall Match:       {results['match']} ({100 * results['match'] / results['total']:.1f}%)")
    print(f"V2 Better:           {results['v2_better']} ({100 * results['v2_better'] / results['total']:.1f}%)")
    print()

    if results["differences"]:
        print("=" * 60)
        print("SAMPLE DIFFERENCES (Legacy > V2)")
        print("=" * 60)
        for i, diff in enumerate(results["differences"][:20]):
            print(f"\n--- {i + 1}. {diff['card_no']} ---")
            print(f"Legacy: {diff['legacy']}")
            print(f"V2:     {diff['v2']}")
            print(f"Text:   {diff['text'][:100]}...")


if __name__ == "__main__":
    results = compare_parsers()
    # print_report(results)
    with open("report_utf8.txt", "w", encoding="utf-8") as f:
        # Redirect stdout to file just for the print_report call
        sys.stdout = f
        print_report(results)
        sys.stdout = sys.__stdout__
