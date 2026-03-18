#!/usr/bin/env python3
"""
Find legacy cards and rate their conversion difficulty.
Outputs: canonical_ability_model/reports/legacy_cards_audit.json
"""

import json
import sys
from pathlib import Path

def estimate_complexity(ability):
    """Rate ability complexity: simple/medium/complex"""
    text = (ability.get('text', '') or '').lower()
    bytecode = ability.get('bytecode', []) or []
    
    # Complex indicators
    complex_patterns = [
        'if',
        'when',
        'depending',
        'choose',
        'random',
        'sequence',
        'after',
        'before',
        'then',
        'active effect',
        'passive effect',
        'trigger',
        'condition',
    ]
    
    # Check complexity indicators
    for pattern in complex_patterns:
        if pattern in text:
            # Some patterns are still okay
            if pattern in ['after', 'then'] and len(text) < 100:
                continue  # Still might be simple
            return 'complex'
    
    # Rate by bytecode length and content
    if len(bytecode) > 30:
        return 'complex'
    elif len(bytecode) > 15:
        return 'medium'
    
    # Rate by text length
    if len(text) > 150:
        return 'medium'
    
    return 'simple'


def count_bytecode_ops(bytecode):
    """Count the number of operations in bytecode"""
    if not bytecode:
        return 0
    return len(bytecode) // 2 + len(bytecode) % 2


def get_dominant_ops(bytecode):
    """Extract dominant opcode patterns"""
    op_map = {
        1: 'draw',
        2: 'damage',
        4: 'cost_reduce',
        6: 'heal',
        5: 'activate',
        3: 'cost_increase',
    }
    
    ops = []
    for i in range(0, len(bytecode or []), 2):
        op = bytecode[i]
        if op in op_map:
            ops.append(op_map[op])
    
    return ops


def main():
    # Load fallback runtime
    json_path = Path('canonical_ability_model/reports/fallback_runtime_preview.json')
    
    if not json_path.exists():
        print(f"ERROR: {json_path} not found")
        sys.exit(1)
    
    with open(json_path, encoding='utf-8-sig') as f:
        data = json.load(f)
    
    legacy_cards = []
    simple_count = 0
    medium_count = 0
    complex_count = 0
    
    # Find all legacy abilities
    for card_id, card in data.get('member_db', {}).items():
        for ability_idx, ability in enumerate(card.get('abilities', [])):
            source = ability.get('source', 'legacy')  # Default to legacy if not marked
            
            if source != 'canonical':  # This is a legacy ability
                complexity = estimate_complexity(ability)
                
                if complexity == 'simple':
                    simple_count += 1
                elif complexity == 'medium':
                    medium_count += 1
                else:
                    complex_count += 1
                
                legacy_cards.append({
                    'card_id': card_id,
                    'ability_idx': ability_idx,
                    'ability_text': ability.get('text', ''),
                    'bytecode': ability.get('bytecode', []),
                    'bytecode_length': len(ability.get('bytecode', []) or []),
                    'bytecode_ops': get_dominant_ops(ability.get('bytecode', [])),
                    'complexity': complexity,
                })
    
    # Sort by complexity (simple first)
    legacy_cards.sort(key=lambda x: (x['complexity'] == 'complex', x['complexity'] == 'medium', x['bytecode_length']))
    
    # Output audit report
    audit = {
        'summary': {
            'total_legacy_abilities': len(legacy_cards),
            'simple': simple_count,
            'medium': medium_count,
            'complex': complex_count,
            'phase2_quick_wins': min(50, simple_count),
            'phase2_medium_cards': min(77, medium_count),
            'phase3_complex_cards': complex_count,
        },
        'simple_cards': legacy_cards[:50],  # Quick wins for Phase 2A
        'medium_cards': legacy_cards[50:50+77],  # Phase 2B
        'complex_cards': legacy_cards[50+77:],  # Phase 3
    }
    
    output_path = Path('canonical_ability_model/reports/legacy_cards_audit.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(audit, f, indent=2, ensure_ascii=False)
    
    print("Legacy Cards Audit Report")
    print("=" * 50)
    print(f"Total legacy abilities: {len(legacy_cards)}")
    print(f"  Simple (quick wins):  {simple_count}")
    print(f"  Medium (Phase 2B):    {medium_count}")
    print(f"  Complex (Phase 3):    {complex_count}")
    print()
    print(f"Phase 2 can convert: {min(50, simple_count)} + {min(77, medium_count)} = {min(50, simple_count) + min(77, medium_count)} cards")
    print(f"  Goal: 50 + 77 = 127 new canonical (from 470 → 597)")
    print()
    print(f"Output: {output_path}")


if __name__ == '__main__':
    main()
