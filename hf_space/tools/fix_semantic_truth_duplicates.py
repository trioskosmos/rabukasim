#!/usr/bin/env python3
"""
Fix semantic_truth_v3.json by removing duplicate DISCARD_DELTA entries.

When HAND_DISCARD is present, it already implies:
- HAND_DELTA(-N)
- DISCARD_DELTA(+N)

If the semantic truth also has explicit DISCARD_DELTA(+N), it's a duplicate.
This script removes such duplicates.
"""

import json
from pathlib import Path


def fix_semantic_truth(input_path: str, output_path: str):
    """Fix duplicate DISCARD_DELTA entries in semantic truth."""

    with open(input_path, "r", encoding="utf-8") as f:
        truth = json.load(f)

    fixed_count = 0

    for card_id, card_truth in truth.items():
        for ability in card_truth.get("abilities", []):
            sequence = ability.get("sequence", [])

            # Collect all HAND_DISCARD values in this ability
            hand_discard_values = []
            for segment in sequence:
                for delta in segment.get("deltas", []):
                    if delta.get("tag") == "HAND_DISCARD":
                        hand_discard_values.append(delta.get("value", 0))

            if not hand_discard_values:
                continue

            total_hand_discard = sum(hand_discard_values)

            # Now check for duplicate DISCARD_DELTA
            for segment in sequence:
                deltas = segment.get("deltas", [])
                new_deltas = []

                for delta in deltas:
                    tag = delta.get("tag")
                    value = delta.get("value", 0)

                    # If this is DISCARD_DELTA with value matching total_hand_discard, skip it
                    if tag == "DISCARD_DELTA" and value == total_hand_discard:
                        # This is likely a duplicate, skip it
                        fixed_count += 1
                        print(f"  Removing duplicate DISCARD_DELTA({value}) from {card_id}")
                        continue

                    # If this is DISCARD_DELTA with value matching any hand_discard value, also skip
                    if tag == "DISCARD_DELTA" and value in hand_discard_values:
                        fixed_count += 1
                        print(f"  Removing duplicate DISCARD_DELTA({value}) from {card_id}")
                        continue

                    new_deltas.append(delta)

                segment["deltas"] = new_deltas

    # Write fixed truth
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(truth, f, indent=2, ensure_ascii=False)

    print(f"\nFixed {fixed_count} duplicate entries")
    print(f"Output written to: {output_path}")

    return fixed_count


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Fix duplicate DISCARD_DELTA in semantic truth")
    parser.add_argument("--input", "-i", default="reports/semantic_truth_v3.json", help="Input semantic truth file")
    parser.add_argument(
        "--output", "-o", default="reports/semantic_truth_v3_fixed.json", help="Output fixed semantic truth file"
    )

    args = parser.parse_args()

    if not Path(args.input).exists():
        print(f"Error: Input file not found: {args.input}")
        return 1

    fix_semantic_truth(args.input, args.output)
    return 0


if __name__ == "__main__":
    exit(main())
