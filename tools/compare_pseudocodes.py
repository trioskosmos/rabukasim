#!/usr/bin/env python3
"""Compare fresh pseudocodes with original manual_pseudocode.json."""

import json
from pathlib import Path

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def compare_pseudocodes():
    original = load_json('data/manual_pseudocode.json')
    fresh = load_json('data/fresh_pseudocodes.json')
    
    # Remove metadata keys from fresh
    fresh_data = {k: v for k, v in fresh.items() if not k.startswith('_')}
    
    # Find common cards
    common_cards = set(original.keys()) & set(fresh_data.keys())
    only_original = set(original.keys()) - set(fresh_data.keys())
    only_fresh = set(fresh_data.keys()) - set(original.keys())
    
    print(f"=== Pseudocode Comparison Report ===\n")
    print(f"Original pseudocodes: {len(original)}")
    print(f"Fresh pseudocodes: {len(fresh_data)}")
    print(f"Common cards: {len(common_cards)}")
    print(f"Only in original: {len(only_original)}")
    print(f"Only in fresh: {len(only_fresh)}")
    
    # Compare common cards
    differences = []
    for card_no in sorted(common_cards):
        orig_pc = original[card_no].get('pseudocode', '')
        fresh_pc = fresh_data[card_no].get('pseudocode', '')
        
        if orig_pc != fresh_pc:
            differences.append({
                'card_no': card_no,
                'original': orig_pc,
                'fresh': fresh_pc
            })
    
    print(f"\n=== Differences in {len(differences)} common cards ===\n")
    
    # Write detailed comparison to file
    with open('reports/pseudocode_comparison.md', 'w', encoding='utf-8') as f:
        f.write("# Pseudocode Comparison Report\n\n")
        f.write(f"- Original pseudocodes: {len(original)}\n")
        f.write(f"- Fresh pseudocodes: {len(fresh_data)}\n")
        f.write(f"- Common cards: {len(common_cards)}\n")
        f.write(f"- Only in original: {len(only_original)}\n")
        f.write(f"- Only in fresh: {len(only_fresh)}\n")
        f.write(f"- Differences found: {len(differences)}\n\n")
        
        f.write("## Cards with Different Pseudocodes\n\n")
        
        for diff in differences[:50]:  # Limit to first 50 for readability
            f.write(f"### {diff['card_no']}\n\n")
            f.write("**Original:**\n```\n")
            f.write(diff['original'])
            f.write("\n```\n\n")
            f.write("**Fresh:**\n```\n")
            f.write(diff['fresh'])
            f.write("\n```\n\n")
            f.write("---\n\n")
        
        if len(differences) > 50:
            f.write(f"\n*... and {len(differences) - 50} more differences*\n")
        
        # Add cards only in original
        f.write("\n## Cards Only in Original\n\n")
        for card_no in sorted(only_original)[:20]:
            f.write(f"- {card_no}\n")
        if len(only_original) > 20:
            f.write(f"\n*... and {len(only_original) - 20} more*\n")
        
        # Add cards only in fresh
        f.write("\n## Cards Only in Fresh\n\n")
        for card_no in sorted(only_fresh):
            f.write(f"- {card_no}\n")
    
    print(f"Detailed comparison written to reports/pseudocode_comparison.md")
    
    return differences

if __name__ == '__main__':
    compare_pseudocodes()
