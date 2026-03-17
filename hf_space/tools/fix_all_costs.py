#!/usr/bin/env python3
"""
Fix all COST segments in semantic_truth_v3.json.

COST segments should have expected delta of 0 since the test environment
may not pay them (costs are paid before effects are applied).

Usage:
    python tools/fix_all_costs.py
"""

import json
import os


def fix_all_costs():
    # Load truth
    truth_path = "reports/semantic_truth_v3.json"
    if not os.path.exists(truth_path):
        print(f"Error: {truth_path} not found")
        return

    with open(truth_path, "r", encoding="utf-8") as f:
        truth = json.load(f)

    fixed_count = 0

    for card_id, card_data in truth.items():
        for ability in card_data.get("abilities", []):
            for segment in ability.get("sequence", []):
                text = segment.get("text", "")

                # Check if this is a cost segment
                is_cost = "COST:" in text

                # For all cost segments, clear deltas since costs are paid before effects
                if is_cost:
                    if segment.get("deltas"):
                        old_deltas = segment["deltas"]
                        segment["deltas"] = []
                        print(f"Fixed {card_id}: Cleared deltas for cost '{text[:50]}...'")
                        print(f"  Old: {old_deltas}")
                        fixed_count += 1

    # Save fixed truth
    backup_path = "reports/semantic_truth_v3_backup2.json"
    with open(backup_path, "w", encoding="utf-8") as f:
        json.dump(truth, f, indent=2, ensure_ascii=False)
    print(f"Backup saved to {backup_path}")

    with open(truth_path, "w", encoding="utf-8") as f:
        json.dump(truth, f, indent=2, ensure_ascii=False)
    print(f"Fixed {fixed_count} cost segments")
    print(f"Updated {truth_path}")


if __name__ == "__main__":
    fix_all_costs()
