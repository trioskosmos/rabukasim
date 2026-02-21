"""Compare parser V1 and V2 output."""

import json

# Ensure we can import from local modules
import os
import sys
from typing import List

sys.path.append(os.getcwd())

from compiler.parser import AbilityParser as AbilityParserV1
from compiler.parser_v2 import AbilityParserV2
from engine.models.ability import Ability


def load_cards(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def abilities_to_str(abilities: List[Ability]) -> str:
    """Convert abilities to string for comparison."""
    if not abilities:
        return "None"

    parts = []
    for i, ab in enumerate(abilities):
        eff_strs = [f"{e.effect_type.name}({e.value})" for e in ab.effects]
        cond_strs = [f"{c.type.name}" for c in ab.conditions]
        cost_strs = [f"{c.type.name}" for c in ab.costs]

        parts.append(f"[{i}] T:{ab.trigger.name}")
        if eff_strs:
            parts.append(f"    E:{', '.join(eff_strs)}")
        if cond_strs:
            parts.append(f"    C:{', '.join(cond_strs)}")
        if cost_strs:
            parts.append(f"    K:{', '.join(cost_strs)}")
        if ab.effects and ab.effects[0].is_optional:
            parts.append("    OPT:True")

    return "\n".join(parts)


def compare_parsers():
    print("Loading cards...")
    cards = load_cards("engine/data/cards.json")

    parser_v1 = AbilityParserV1()
    parser_v2 = AbilityParserV2()

    total = 0
    matches = 0
    mismatches = 0
    errors_v2 = 0

    mismatch_samples = []

    print(f"Comparing {len(cards)} cards...")

    for card_id, card_data in cards.items():
        # Skip dummy cards or markers if necessary, but parser usually handles them
        if "ability" not in card_data:
            continue

        text = card_data["ability"]
        if not text:
            # Empty text should produce empty abilities
            res_v1 = []
            res_v2 = []
        else:
            # V1 Parse
            try:
                res_v1 = parser_v1.parse_ability_text(text)
            except Exception:
                res_v1 = []

            # V2 Parse
            try:
                res_v2 = parser_v2.parse(text)
            except Exception:
                errors_v2 += 1
                res_v2 = []

        str_v1 = abilities_to_str(res_v1)
        str_v2 = abilities_to_str(res_v2)

        total += 1
        if str_v1 == str_v2:
            matches += 1
        else:
            mismatches += 1
            if len(mismatch_samples) < 10:
                mismatch_samples.append(
                    {"id": card_id, "name": card_data.get("name", "Unknown"), "text": text, "v1": str_v1, "v2": str_v2}
                )

    with open("parser_comparison_report.txt", "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write("COMPARISON RESULTS\n")
        f.write("=" * 60 + "\n")
        f.write(f"Total Cards Checked: {total}\n")
        f.write(f"Matches:             {matches} ({matches / total * 100:.1f}%)\n")
        f.write(f"Mismatches:          {mismatches}\n")
        f.write(f"V2 Errors:           {errors_v2}\n\n")

        print(f"Total Cards Checked: {total}")
        print(f"Matches:             {matches} ({matches / total * 100:.1f}%)")
        print(f"Mismatches:          {mismatches}")
        print(f"V2 Errors:           {errors_v2}")

        f.write("=" * 60 + "\n")
        f.write("SAMPLE MISMATCHES\n")
        f.write("=" * 60 + "\n")

        for sample in mismatch_samples:
            f.write(f"\nCard: {sample['name']} ({sample['id']})\n")
            f.write(f"Text: {sample['text']}\n")
            f.write("-" * 30 + "\n")
            f.write("Legacy (V1):\n")
            f.write(f"{sample['v1']}\n")
            f.write("-" * 30 + "\n")
            f.write("New (V2):\n")
            f.write(f"{sample['v2']}\n")
            f.write("=" * 60 + "\n")

    print("Report written to parser_comparison_report.txt")


if __name__ == "__main__":
    compare_parsers()
