#!/usr/bin/env python3
"""
Generate cost_component_composition.json from normalized patterns.
Analyzes cost patterns and groups them by their component composition.

This script generates: ../data/cost_component_composition.json
Source: ../data/normalized_before_colon_patterns.json
"""

import json
from collections import defaultdict
from pathlib import Path


def identify_components(pattern):
    """Identify the components that make up a cost pattern."""
    components = []
    
    # Energy cost
    if '{icon_energy.png|E}' in pattern or 'icon_energy' in pattern:
        components.append('energy_cost')
    
    # Card discard from hand
    if '手札' in pattern and ('控え室に置く' in pattern or '控え室に置いてもよい' in pattern):
        if 'ライブカード' in pattern:
            components.append('discard_live_card_from_hand')
        elif 'メンバーカード' in pattern:
            components.append('discard_member_card_from_hand')
        else:
            components.append('discard_card_from_hand')
    
    # Card discard from deck
    if 'デッキ' in pattern and ('控え室に置く' in pattern or '控え室に置いてもよい' in pattern):
        components.append('discard_from_deck')
    
    # Member to waitroom
    if 'ステージから控え室に置く' in pattern or 'ステージから控え室に置いてもよい' in pattern:
        components.append('member_to_waitroom')
    elif 'ウェイトにする' in pattern or 'ウェイトにしてもよい' in pattern:
        components.append('member_to_wait')
    
    # Card reveal
    if '公開' in pattern:
        components.append('reveal')
    
    # Optional payment
    if 'でもよい' in pattern or '支払ってもよい' in pattern:
        components.append('optional_payment')
    
    return components


def generate_cost_component_composition():
    """Generate cost_component_composition.json from normalized patterns."""
    
    # Load normalized patterns
    input_file = Path("../data/normalized_before_colon_patterns.json")
    with open(input_file, encoding='utf-8') as f:
        patterns = json.load(f)
    
    # Group by component composition
    composition_groups = defaultdict(list)
    
    for item in patterns:
        pattern = item["normalized_pattern"]
        components = identify_components(pattern)
        
        # Use tuple of components as key for grouping
        comp_key = tuple(sorted(components))
        composition_groups[comp_key].append({
            "pattern": pattern,
            "components": components,
            "count": item["count"],
            "total_cards": item["total_cards"],
            "original_variations": item["original_variations"]
        })
    
    # Build output structure
    output = []
    total_pattern_count = 0
    total_card_count = 0
    
    for comp_key, items in composition_groups.items():
        pattern_count = sum(item["count"] for item in items)
        card_count = sum(item["total_cards"] for item in items)
        
        total_pattern_count += pattern_count
        total_card_count += card_count
        
        output.append({
            "component_composition": list(comp_key),
            "pattern_count": pattern_count,
            "total_cards": card_count,
            "patterns": items
        })
    
    # Sort by total_cards descending
    output.sort(key=lambda x: x["total_cards"], reverse=True)
    
    # Save to file
    output_file = Path("../data/cost_component_composition.json")
    output_with_metadata = {
        "generated_by": "generate_cost_component_composition.py",
        "source_file": "../data/normalized_before_colon_patterns.json",
        "generated_at": str(Path.cwd()),
        "data": output
    }
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_with_metadata, f, ensure_ascii=False, indent=2)
    
    print(f"Generated {output_file}")
    print(f"Total component compositions: {len(output)}")
    print(f"Total patterns: {total_pattern_count}")
    print(f"Total cards: {total_card_count}")


if __name__ == "__main__":
    generate_cost_component_composition()
