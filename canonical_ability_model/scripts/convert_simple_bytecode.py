#!/usr/bin/env python3
"""
Convert simple legacy bytecode patterns to canonical plans for Phase 2A.
Handles the most common, straightforward bytecode->canonical mappings.
"""

import json

# Opcode mappings
OPCODE_MAP = {
    1: 'draw',
    2: 'damage_opponent',
    3: 'damage_self',
    4: 'cost_reduce',
    5: 'activate',
    6: 'heal_self',
    15: 'recover_live',
    16: 'boost_score',
    17: 'recover_member',
    43: 'activate_member',
}

def parse_simple_bytecode(bytecode, card_id, ability_idx):
    """Try to parse simple bytecode patterns into canonical steps."""
    if not bytecode or len(bytecode) < 2:
        return None
    
    steps = []
    i = 0
    
    while i < len(bytecode):
        op = bytecode[i]
        
        # Simple single-arg opcodes
        if op in [1, 2, 3, 4, 6]:
            count = bytecode[i + 1] if i + 1 < len(bytecode) else 1
            
            action_map = {
                1: ('draw', {'count': count, 'source': 'player'}),
                2: ('damage', {'target': 'opponent', 'amount': count}),
                3: ('damage', {'target': 'self', 'amount': count}),
                4: ('cost_reduce', {'amount': count, 'target': 'self'}),
                6: ('heal', {'target': 'self', 'amount': count}),
            }
            
            if op in action_map:
                action, args = action_map[op]
                step = {'step': len(steps) + 1, 'action': action}
                step.update(args)
                steps.append(step)
                i += 2
            else:
                break
        else:
            # Unknown opcode, stop trying
            break
    
    if not steps:
        return None
    
    return steps

def convert_legacy_batch(audit_json_path, runtime_json_path, output_path):
    """Convert simple legacy cards to canonical draft."""
    
    # Load audit and runtime
    with open(audit_json_path, encoding='utf-8') as f:
        audit = json.load(f)
    
    with open(runtime_json_path, encoding='utf-8-sig') as f:
        runtime = json.load(f)
    
    # Start with simple cards
    converted = []
    skipped = []
    
    for card_entry in audit['simple_cards'][:50]:
        card_id = card_entry['card_id']
        ability_idx = card_entry['ability_idx']
        bytecode = card_entry['bytecode']
        
        # Try to convert
        steps = parse_simple_bytecode(bytecode, card_id, ability_idx)
        
        if steps:
            # Get ability text for reference
            card_data = runtime['member_db'].get(str(card_id))
            if card_data and ability_idx < len(card_data['abilities']):
                ability = card_data['abilities'][ability_idx]
                text = ability.get('raw_text', f'Card {card_id} Ability {ability_idx}')
                
                entry = {
                    'card_no': str(card_id),
                    'ability_idx': ability_idx,
                    'ability_text': text[:100],
                    'canonical_plan': steps,
                    'source': 'PHASE2A_AUTO_GENERATED',
                }
                converted.append(entry)
        else:
            skipped.append({
                'card_id': card_id,
                'ability_idx': ability_idx,
                'bytecode': bytecode,
                'reason': 'Complex or unrecognized bytecode pattern',
            })
    
    # Output report
    report = {
        'timestamp': '2026-03-18',
        'phase': 'PHASE_2A_AUTO_GENERATION',
        'converted': len(converted),
        'skipped': len(skipped),
        'entries': converted,
        'skipped_details': skipped[:10],  # Just first 10 skipped
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Converted: {len(converted)} simple cards")
    print(f"⚠️  Skipped: {len(skipped)} complex cards")
    print(f"📝 Output: {output_path}")
    print()
    
    if converted:
        print("Sample conversions:")
        for entry in converted[:3]:
            print(f"  - Card {entry['card_no']}: {entry['ability_text'][:50]}")
            print(f"    Steps: {entry['canonical_plan']}")
    
    return converted, skipped

if __name__ == '__main__':
    converted, skipped = convert_legacy_batch(
        'canonical_ability_model/reports/legacy_cards_audit.json',
        'canonical_ability_model/reports/fallback_runtime_preview.json',
        'canonical_ability_model/reports/PHASE2A_AUTO_CONVERSIONS.json'
    )
