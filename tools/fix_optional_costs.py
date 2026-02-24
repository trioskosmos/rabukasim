#!/usr/bin/env python3
"""
Fix optional costs in semantic_truth_v3.json.

Optional costs (abilities with optional: true) should have expected delta of 0
for COST segments since the test environment may not pay them.

Usage:
    python tools/fix_optional_costs.py
"""

import json
import re
import os

def fix_optional_costs():
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
            # Check if this ability is optional
            is_optional = ability.get("optional", False)
            
            for segment in ability.get("sequence", []):
                text = segment.get("text", "")
                
                # Check if this is a cost segment
                is_cost = "COST:" in text
                
                # For optional abilities, cost segments should have empty deltas
                if is_optional and is_cost:
                    if segment.get("deltas"):
                        old_deltas = segment["deltas"]
                        segment["deltas"] = []
                        print(f"Fixed {card_id}: Cleared deltas for optional cost '{text[:50]}...'")
                        print(f"  Old: {old_deltas}")
                        fixed_count += 1
    
    # Save fixed truth
    backup_path = "reports/semantic_truth_v3_backup.json"
    with open(backup_path, "w", encoding="utf-8") as f:
        json.dump(truth, f, indent=2, ensure_ascii=False)
    print(f"Backup saved to {backup_path}")
    
    with open(truth_path, "w", encoding="utf-8") as f:
        json.dump(truth, f, indent=2, ensure_ascii=False)
    print(f"Fixed {fixed_count} optional cost segments")
    print(f"Updated {truth_path}")

if __name__ == "__main__":
    fix_optional_costs()
