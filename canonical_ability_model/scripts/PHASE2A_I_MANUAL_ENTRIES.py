#!/usr/bin/env python3
"""
Phase 2A-i: Manually create canonical entries for immediate cards.
This is the actual WRITING: converting legacy to canonical pseudocode.
"""

import json

# Cards I'm writing manually based on analysis
PHASE_2A_I_ENTRIES = [
    {
        "card_no": "377",
        "ability_idx": 0,
        "ability_text": "TRIGGER: ON_PLAY\nEFFECT: DRAW(1)",
        "description": "When played, draw 1 card. Opcode 10.",
        "canonical_plan": [
            {
                "step": 1,
                "action": "draw",
                "count": 1,
                "source": "player"
            }
        ]
    },
]

# Load the existing draft to see structure
with open('canonical_ability_model/drafts/canonical_full_draft.json', encoding='utf-8') as f:
    existing = json.load(f)

print(f"Phase 2A-i Entries to Add: {len(PHASE_2A_I_ENTRIES)}")
print("=" * 80)

for entry in PHASE_2A_I_ENTRIES:
    print(f"\nCard {entry['card_no']} (ability {entry['ability_idx']})")
    print(f"  Text: {entry['ability_text']}")
    print(f"  Canonical plan: {entry['canonical_plan']}")

print("\n" + "=" * 80)
print("✅ Ready to integrate into canonical_full_draft.json")
print("   These entries convert legacy bytecode to canonical pseudocode.")
print("   Next: Validate + regenerate runtime + test")
