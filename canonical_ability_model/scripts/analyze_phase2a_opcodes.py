#!/usr/bin/env python3
"""
Generate canonical conversions for Phase 2A by mapping game EFFECT opcodes
to canonical action steps.
"""

import json
from collections import Counter

# Load audit and runtime
with open('canonical_ability_model/reports/legacy_cards_audit.json', encoding='utf-8') as f:
    audit = json.load(f)

with open('canonical_ability_model/reports/fallback_runtime_preview.json', encoding='utf-8-sig') as f:
    runtime = json.load(f)

simple_cards = audit['simple_cards'][:50]

# Analyze what game opcodes/patterns we're actually dealing with
opcode_counter = Counter()
effect_patterns = {}

for card_entry in simple_cards:
    card_id = card_entry['card_id']
    ability_idx = card_entry['ability_idx']
    
    card_data = runtime['member_db'].get(str(card_id))
    if card_data and ability_idx < len(card_data['abilities']):
        ability = card_data['abilities'][ability_idx]
        bytecode = ability.get('bytecode', [])
        text = ability.get('raw_text', '')
        
        # Track first opcode (usually the effect type)
        if bytecode:
            op = bytecode[0]
            opcode_counter[op] += 1
            
            # Store pattern
            pattern_key = f'opcode_{op}'
            if pattern_key not in effect_patterns:
                effect_patterns[pattern_key] = {
                    'example_card': card_id,
                    'example_text': text[:80],
                    'example_bytecode': bytecode,
                    'count': 0,
                }
            effect_patterns[pattern_key]['count'] += 1

# Print analysis
print("PHASE 2A BYTECODE ANALYSIS")
print("=" * 80)
print()
print("Top opcodes in 'simple' cards:")
for opcode, count in opcode_counter.most_common(10):
    print(f"  Opcode {opcode}: {count} cards")
    pattern = effect_patterns[f'opcode_{opcode}']
    print(f"    Example card {pattern['example_card']}: {pattern['example_text']}")
    print(f"    Bytecode: {pattern['example_bytecode'][:10]}")
    print()

# Generate mapping strategy
print("=" * 80)
print("MAPPING STRATEGY FOR PHASE 2A")
print("=" * 80)
print()

opcode_meanings = {
    15: 'RECOVER_LIVE - Add live member to hand',
    16: 'BOOST_SCORE - Increase live score (passive effect)',
    17: 'RECOVER_MEMBER - Add member to hand from reserve',
    43: 'ACTIVATE_MEMBER - Activate specific member ability',
}

for opcode in sorted([o for o, _ in opcode_counter.most_common()]):
    meaning = opcode_meanings.get(opcode, 'Unknown')
    print(f"Opcode {opcode}: {meaning}")

print()
print("Recommendation: Create game-semantics canonicalization")
print("- Each opcode maps to one or more canonical 'action' steps")
print("- RECOVER_LIVE/MEMBER -> 'recover' action")
print("- BOOST_SCORE -> 'passive_boost' or 'score_modifier' action")
print("- ACTIVATE_MEMBER -> 'activate' action")
print()
print("These need semantic review before implementation.")
