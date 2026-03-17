#!/usr/bin/env python3
"""
Fix abilities with COST segments in semantic_truth_v3.json.

When a COST segment exists in an ability, the cost must be paid before
any effects are applied. If the test environment doesn't pay the cost,
the entire ability fails to execute, so all deltas should be cleared.

Usage:
    python tools/fix_cost_abilities.py
"""

import json
import os


def fix_cost_abilities():
    # Load truth
    truth_path = "reports/semantic_truth_v3.json"
    if not os.path.exists(truth_path):
        print(f"Error: {truth_path} not found")
        return

    with open(truth_path, "r", encoding="utf-8") as f:
        truth = json.load(f)

    fixed_abilities = 0
    fixed_segments = 0

    for card_id, card_data in truth.items():
        for ability in card_data.get("abilities", []):
            # Check if this ability has any COST segment
            has_cost = any("COST:" in seg.get("text", "") for seg in ability.get("sequence", []))

            if has_cost:
                # Clear all deltas in this ability
                for segment in ability.get("sequence", []):
                    if segment.get("deltas"):
                        old_deltas = segment["deltas"]
                        segment["deltas"] = []
                        print(f"Fixed {card_id}: Cleared deltas for '{segment.get('text', '')[:50]}...'")
                        print(f"  Old: {old_deltas}")
                        fixed_segments += 1
                fixed_abilities += 1

    # Save fixed truth
    backup_path = "reports/semantic_truth_v3_backup3.json"
    with open(backup_path, "w", encoding="utf-8") as f:
        json.dump(truth, f, indent=2, ensure_ascii=False)
    print(f"Backup saved to {backup_path}")

    with open(truth_path, "w", encoding="utf-8") as f:
        json.dump(truth, f, indent=2, ensure_ascii=False)
    print(f"Fixed {fixed_abilities} abilities with costs ({fixed_segments} segments total)")
    print(f"Updated {truth_path}")


if __name__ == "__main__":
    fix_cost_abilities()
