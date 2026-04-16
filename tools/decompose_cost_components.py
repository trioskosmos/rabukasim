#!/usr/bin/env python3
"""
Decompose cost patterns into individual components and group by component composition.
"""

import json
import re
from collections import defaultdict
from pathlib import Path


def identify_base_cost_type(cost_text):
    """Identify the base cost type (fundamental action)."""
    # Energy payment (check first as it's most common)
    if '{icon_energy.png|E}' in cost_text or 'icon_energy' in cost_text:
        return "energy_payment"
    
    # Member movement
    if 'ステージから控え室に置く' in cost_text or 'ステージから控え室に置いてもよい' in cost_text:
        return "member_to_waitroom"
    elif 'ウェイトにする' in cost_text or 'ウェイトにしてもよい' in cost_text:
        return "member_to_wait"
    
    # Card discard (handle both 置く and 置いてもよい)
    if '控え室に置く' in cost_text or '控え室に置いてもよい' in cost_text:
        if '手札' in cost_text:
            return "discard_from_hand"
        elif 'デッキ' in cost_text:
            return "discard_from_deck"
        else:
            return "discard"
    
    # Card reveal
    if '公開' in cost_text:
        return "reveal"
    
    # Deck manipulation
    if 'デッキ' in cost_text:
        return "deck_manipulation"
    
    # Energy placement
    if 'エネルギー置き場' in cost_text or 'エネルギーデッキ' in cost_text:
        return "energy_placement"
    
    return "unknown"


def analyze_cost_composition():
    """Analyze cost patterns by base cost type and variants."""
    
    # Load normalized patterns
    patterns_file = Path("data/normalized_before_colon_patterns.json")
    with open(patterns_file, encoding='utf-8') as f:
        patterns = json.load(f)
    
    # Group by base cost type
    base_type_groups = defaultdict(list)
    
    for item in patterns:
        cost_text = item["normalized_pattern"]
        base_type = identify_base_cost_type(cost_text)
        
        base_type_groups[base_type].append({
            "pattern": cost_text,
            "count": item["count"],
            "total_cards": item["total_cards"],
            "original_variations": item["original_variations"]
        })
    
    # Sort by total card count
    sorted_groups = sorted(base_type_groups.items(), key=lambda x: sum(item["total_cards"] for item in x[1]), reverse=True)
    
    print(f"=== Base Cost Types and Variants ===")
    print(f"Total patterns: {len(patterns)}")
    print(f"Unique base cost types: {len(base_type_groups)}")
    print()
    
    for i, (base_type, items) in enumerate(sorted_groups):
        total_cards = sum(item["total_cards"] for item in items)
        total_count = sum(item["count"] for item in items)
        
        print(f"Base Type {i+1}: {base_type}")
        print(f"  {total_count} variants, {total_cards} total cards")
        for item in items[:5]:
            print(f"  - {item['pattern']} ({item['count']} times, {item['total_cards']} cards)")
        print()
    
    # Save to file
    output = []
    for base_type, items in sorted_groups:
        total_cards = sum(item["total_cards"] for item in items)
        total_count = sum(item["count"] for item in items)
        
        group_data = {
            "base_cost_type": base_type,
            "variant_count": total_count,
            "total_cards": total_cards,
            "variants": items
        }
        output.append(group_data)
    
    output_file = Path("data/base_cost_types.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"Results saved to {output_file}")


if __name__ == "__main__":
    analyze_cost_composition()
