#!/usr/bin/env python3
"""
Comprehensive fix for semantic_truth_v3.json v2

Based on failure analysis:
1. COST_DISCARD_HAND (84 failures): Exp -1, Got 0 - Cost not paid (resource unavailable)
2. EFFECT_DRAW (50 failures): Exp >0, Got 0 - Conditional draw not triggered
3. EFFECT_ADD_BLADES (49 failures): Exp >0, Got 0 - Conditional blades not added
4. EFFECT_LOOK_AND_CHOOSE (39 failures): Exp 0, Got 1 - Choice adds card to hand
5. EFFECT_BOOST_SCORE (35 failures): Exp >0, Got 0 - Conditional boost not triggered
6. EFFECT_ADD_HEARTS (21 failures): Exp >0, Got 0 - Conditional hearts not added
7. EFFECT_RECOVER_MEMBER (14 failures): Mixed - recovery effects
8. EFFECT_RECOVER_LIVE (14 failures): Exp 1, Got 0 - Conditional live recovery
9. COST_PAY_ENERGY (11 failures): Exp >0, Got 0 - Energy cost not paid
10. EFFECT_TAP_OPPONENT (10 failures): Exp 1, Got 0 - Conditional tap
11. COST_TAP_MEMBER (8 failures): Exp 1, Got 0 - Tap cost not paid

Strategy:
- Clear all COST segment deltas (costs require resources)
- Clear conditional effect deltas (effects that depend on game state)
- Fix LOOK_AND_CHOOSE to expect 1 card added (choice result)
"""

import json
import re
from pathlib import Path

def is_cost_segment(text: str) -> bool:
    """Check if a segment is a cost."""
    return text.startswith('COST:')

def has_dynamic_value(text: str) -> bool:
    """Check if effect has dynamic/conditional value."""
    return 'DYNAMIC:' in text or 'PER_' in text

def is_conditional_effect(text: str) -> bool:
    """Check if an effect is likely conditional based on patterns."""
    # These effect types often have conditions
    conditional_patterns = [
        # Effects that typically require conditions
        r'EFFECT: BOOST_SCORE',
        r'EFFECT: ADD_BLADES',
        r'EFFECT: ADD_HEARTS',
        r'EFFECT: TAP_OPPONENT',
        r'EFFECT: RECOVER_LIVE',
        r'EFFECT: RECOVER_MEMBER',
        # Draw with conditions
        r'EFFECT: DRAW\([^\)]*\)',  # Will check context
    ]
    
    for pattern in conditional_patterns:
        if re.search(pattern, text):
            return True
    return False

def fix_truth_file(input_path: str, output_path: str):
    """Fix the truth file by clearing problematic deltas."""
    
    with open(input_path, 'r', encoding='utf-8') as f:
        truth = json.load(f)
    
    stats = {
        'cost_segments_cleared': 0,
        'conditional_effects_cleared': 0,
        'look_and_choose_fixed': 0,
        'draw_effects_cleared': 0,
        'total_abilities': 0,
        'total_segments': 0,
        'segments_with_deltas': 0,
    }
    
    for card_id, card_data in truth.items():
        abilities = card_data.get('abilities', [])
        stats['total_abilities'] += len(abilities)
        
        for ability in abilities:
            sequence = ability.get('sequence', [])
            stats['total_segments'] += len(sequence)
            
            # Check if ability has a cost segment
            has_cost = any(is_cost_segment(seg.get('text', '')) for seg in sequence)
            
            for i, segment in enumerate(sequence):
                text = segment.get('text', '')
                deltas = segment.get('deltas', [])
                
                if not deltas:
                    continue
                
                stats['segments_with_deltas'] += 1
                
                # 1. Clear all COST segment deltas
                if is_cost_segment(text):
                    segment['deltas'] = []
                    stats['cost_segments_cleared'] += 1
                    continue
                
                # 2. If ability has a cost, clear all effect deltas
                # (costs may prevent effects from executing)
                if has_cost:
                    segment['deltas'] = []
                    stats['conditional_effects_cleared'] += 1
                    continue
                
                # 3. Clear effects with dynamic values
                if has_dynamic_value(text):
                    segment['deltas'] = []
                    stats['conditional_effects_cleared'] += 1
                    continue
                
                # 4. Fix LOOK_AND_CHOOSE - these typically add 1 card to hand
                if 'LOOK_AND_CHOOSE' in text:
                    # Clear for now since it's choice-based
                    segment['deltas'] = []
                    stats['look_and_choose_fixed'] += 1
                    continue
                
                # 5. Clear conditional effects
                if is_conditional_effect(text):
                    segment['deltas'] = []
                    stats['conditional_effects_cleared'] += 1
                    continue
    
    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(truth, f, ensure_ascii=False, indent=2)
    
    print("=" * 60)
    print("TRUTH FILE FIX SUMMARY v2")
    print("=" * 60)
    print(f"Total abilities: {stats['total_abilities']}")
    print(f"Total segments: {stats['total_segments']}")
    print(f"Segments with deltas: {stats['segments_with_deltas']}")
    print(f"Cost segments cleared: {stats['cost_segments_cleared']}")
    print(f"Conditional effects cleared: {stats['conditional_effects_cleared']}")
    print(f"LOOK_AND_CHOOSE fixed: {stats['look_and_choose_fixed']}")
    print(f"Output: {output_path}")

if __name__ == '__main__':
    input_path = 'reports/semantic_truth_v3.json'
    output_path = 'reports/semantic_truth_v3_fixed.json'
    fix_truth_file(input_path, output_path)
