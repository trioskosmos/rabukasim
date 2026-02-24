#!/usr/bin/env python3
"""
Fix semantic_truth_v3.json by removing/correcting cards with unrealistic delta values.

Cards with HAND_DELTA > 10 or DISCARD_DELTA < -10 are likely parsing errors
from dynamic values like DRAW(DYNAMIC:stage_count).
"""

import json
from pathlib import Path


def fix_semantic_truth(input_path: str, output_path: str):
    """Fix unrealistic delta values in semantic truth."""
    
    with open(input_path, 'r', encoding='utf-8') as f:
        truth = json.load(f)
    
    fixed_count = 0
    removed_abilities = 0
    
    for card_id, card_truth in truth.items():
        abilities = card_truth.get('abilities', [])
        
        for ability in abilities:
            sequence = ability.get('sequence', [])
            new_sequence = []
            
            for segment in sequence:
                deltas = segment.get('deltas', [])
                new_deltas = []
                has_unrealistic = False
                
                for delta in deltas:
                    tag = delta.get('tag')
                    value = delta.get('value', 0)
                    
                    # Check for unrealistic values
                    if tag == 'HAND_DELTA' and abs(value) > 10:
                        print(f"  Unrealistic HAND_DELTA({value}) in {card_id}")
                        has_unrealistic = True
                        fixed_count += 1
                        continue
                    
                    if tag == 'DISCARD_DELTA' and (value > 10 or value < -10):
                        print(f"  Unrealistic DISCARD_DELTA({value}) in {card_id}")
                        has_unrealistic = True
                        fixed_count += 1
                        continue
                    
                    if tag == 'DECK_DELTA' and abs(value) > 10:
                        print(f"  Unrealistic DECK_DELTA({value}) in {card_id}")
                        has_unrealistic = True
                        fixed_count += 1
                        continue
                    
                    new_deltas.append(delta)
                
                if not has_unrealistic:
                    segment['deltas'] = new_deltas
                    new_sequence.append(segment)
                else:
                    # Clear the segment if it has unrealistic values
                    segment['deltas'] = []
                    new_sequence.append(segment)
            
            ability['sequence'] = new_sequence
    
    # Write fixed truth
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(truth, f, indent=2, ensure_ascii=False)
    
    print(f"\nFixed {fixed_count} unrealistic values")
    print(f"Output written to: {output_path}")
    
    return fixed_count


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix unrealistic delta values in semantic truth')
    parser.add_argument('--input', '-i', default='reports/semantic_truth_v3.json',
                        help='Input semantic truth file')
    parser.add_argument('--output', '-o', default='reports/semantic_truth_v3_fixed2.json',
                        help='Output fixed semantic truth file')
    
    args = parser.parse_args()
    
    if not Path(args.input).exists():
        print(f"Error: Input file not found: {args.input}")
        return 1
    
    fix_semantic_truth(args.input, args.output)
    return 0


if __name__ == '__main__':
    exit(main())
