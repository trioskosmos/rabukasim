"""
Trace opcode 29 (META_RULE) back to original pseudocode patterns.
"""

import json
from collections import Counter

# Load the source pseudocode from cards.json
with open("data/cards.json", "r", encoding="utf-8") as f:
    raw_db = json.load(f)

# Load manual overrides
with open("data/manual_pseudocode.json", "r", encoding="utf-8") as f:
    manual_pc = json.load(f)

# Load compiled data
with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
    compiled_db = json.load(f)

print("=== TRACING OPCODE 29 (META_RULE) TO SOURCE PSEUDOCODE ===")

# Find cards with opcode 29 in bytecode
meta_rule_sources = []

for card_id, card in compiled_db["member_db"].items():
    for ab_idx, ab in enumerate(card.get("abilities", [])):
        bc = ab.get("bytecode", [])
        if 29 in bc:
            card_no = card.get("card_no", card_id)

            # Get original pseudocode
            pseudocode = None
            if card_no in manual_pc:
                pseudocode = manual_pc[card_no].get("pseudocode", "")
                source = "manual"
            elif card_no in raw_db:
                pseudocode = raw_db[card_no].get("pseudocode", "")
                source = "cards.json"
            else:
                source = "unknown"

            meta_rule_sources.append(
                {
                    "card_no": card_no,
                    "ab_idx": ab_idx,
                    "source": source,
                    "pseudocode": pseudocode,
                    "bytecode_snippet": bc[:20],
                }
            )

print(f"\nTotal abilities with META_RULE (opcode 29): {len(meta_rule_sources)}")
print("\nSample of 15 affected abilities:")
for item in meta_rule_sources[:15]:
    print(f"\n[{item['card_no']}] Ability {item['ab_idx']} (Source: {item['source']}):")
    if item["pseudocode"]:
        print(f"  Pseudocode: {item['pseudocode'][:120]}...")
    else:
        print("  Pseudocode: NOT FOUND")
    print(f"  Bytecode: {item['bytecode_snippet']}")

# Count pseudocode patterns that lead to META_RULE
print("\n=== PATTERN ANALYSIS ===")
patterns = Counter()
for item in meta_rule_sources:
    if item["pseudocode"]:
        # Extract effect names from pseudocode
        import re

        effects = re.findall(r"EFFECT:\s*([^;]+)", item["pseudocode"])
        for eff in effects:
            effect_names = re.findall(r"(\w+)\(", eff)
            for name in effect_names:
                patterns[name] += 1

print("\nTop 20 effect names appearing in META_RULE pseudocodes:")
for name, count in patterns.most_common(20):
    print(f"  {name}: {count}")
