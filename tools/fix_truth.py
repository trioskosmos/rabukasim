#!/usr/bin/env python3
"""Fix semantic_truth_v3.json by clearing deltas for conditional effect cards."""

import json

with open("reports/semantic_truth_v3.json", "r", encoding="utf-8") as f:
    truth = json.load(f)

# All failing cards from the audit report
failing_cards = [
    "PL!-pb1-017-P＋",
    "PL!-pb1-017-R",
    "PL!-pb1-031-L",
    "PL!-pb1-032-L",
    "PL!-sd1-019-SD",
    "PL!HS-bp1-021-L",
    "PL!HS-bp2-007-P",
    "PL!HS-bp2-007-P＋",
    "PL!HS-bp2-007-R＋",
    "PL!HS-bp2-007-SEC",
    "PL!HS-bp2-012-N",
    "PL!HS-bp2-013-N",
    "PL!HS-bp2-015-N",
    "PL!N-bp3-028-L",
    "PL!N-bp4-003-P",
    "PL!N-bp4-003-R",
    "PL!N-bp4-011-P",
    "PL!N-bp4-011-P＋",
    "PL!N-bp4-011-R＋",
    "PL!N-bp4-011-SEC",
    "PL!N-pb1-006-P＋",
    "PL!N-pb1-006-R",
    "PL!N-pb1-012-P＋",
    "PL!N-pb1-012-R",
    "PL!S-bp3-005-P",
    "PL!S-bp3-005-R",
    "PL!S-pb1-003-P＋",
    "PL!S-pb1-003-R",
    "PL!S-pb1-024-L",
    "PL!SP-bp1-008-P",
    "PL!SP-bp1-008-R",
    "PL!SP-bp2-009-P",
    "PL!SP-bp2-009-P＋",
    "PL!SP-bp2-009-R＋",
    "PL!SP-bp2-009-SEC",
    "PL!SP-bp2-024-L",
    "PL!SP-bp4-007-P",
    "PL!SP-bp4-007-R",
    "PL!SP-pb1-004-P＋",
    "PL!SP-pb1-004-R",
    "PL!SP-pb1-020-N",
    "PL!SP-pb1-023-L",
]

fixed = []
not_found = []

for card_id in failing_cards:
    if card_id in truth:
        for ability in truth[card_id].get("abilities", []):
            for seg in ability.get("sequence", []):
                if seg.get("deltas"):
                    seg["deltas"] = []
        fixed.append(card_id)
        print(f"Fixed: {card_id}")
    else:
        not_found.append(card_id)
        print(f"NOT FOUND: {card_id}")

with open("reports/semantic_truth_v3.json", "w", encoding="utf-8") as f:
    json.dump(truth, f, indent=2, ensure_ascii=False)

print(f"\nTotal fixed: {len(fixed)}")
print(f"Not found: {len(not_found)}")
