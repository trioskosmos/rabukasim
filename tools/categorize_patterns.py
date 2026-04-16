#!/usr/bin/env python3
"""
Categorize the 56 normalized patterns into broader groups.
"""

import json
from collections import defaultdict
from pathlib import Path


def categorize_pattern(pattern):
    """Categorize a pattern into a broader group."""
    
    # Card discard (手札を控え室に置く)
    if '手札' in pattern and '控え室に置く' in pattern:
        if '支払ってもよい' in pattern or '支払ってもよい' in pattern:
            return 'card_discard_optional'
        else:
            return 'card_discard'
    
    # Energy payment (energy icons + 支払ってもよい)
    if '{icon_energy.png|E}' in pattern and '支払ってもよい' in pattern:
        return 'energy_payment_optional'
    
    # Energy cost (just energy icons, no payment text)
    if '{icon_energy.png|E}' in pattern and '支払ってもよい' not in pattern:
        if '手札' in pattern or 'このメンバー' in pattern or 'このカード' in pattern:
            return 'energy_plus_action'
        else:
            return 'energy_cost'
    
    # Member to waitroom (ステージから控え室に置く)
    if 'ステージから控え室に置く' in pattern:
        if '支払ってもよい' in pattern:
            return 'member_to_waitroom_optional'
        else:
            return 'member_to_waitroom'
    
    # Member to wait (ウェイトにする)
    if 'ウェイトにする' in pattern or 'ウェイトにしてもよい' in pattern:
        if '支払ってもよい' in pattern or 'でもよい' in pattern:
            return 'member_to_wait_optional'
        else:
            return 'member_to_wait'
    
    # Card reveal (公開する)
    if '公開' in pattern:
        if '支払ってもよい' in pattern or 'でもよい' in pattern:
            return 'card_reveal_optional'
        else:
            return 'card_reveal'
    
    # Deck manipulation (デッキの上から, デッキの一番下に置く)
    if 'デッキ' in pattern:
        if '控え室に置く' in pattern:
            return 'deck_to_waitroom'
        elif 'デッキの一番下に置く' in pattern:
            return 'deck_to_bottom'
        else:
            return 'deck_manipulation'
    
    # Energy placement (エネルギー置き場にあるエネルギーを...の下に置く)
    if 'エネルギー置き場' in pattern or 'エネルギーデッキ' in pattern:
        return 'energy_placement'
    
    # Mixed costs (combining different actions)
    if 'か' in pattern and ('手札' in pattern or 'ウェイト' in pattern):
        return 'mixed_choice'
    
    # Default
    return 'other'


def categorize_patterns():
    """Categorize all normalized patterns into broader groups."""
    
    # Load normalized patterns
    patterns_file = Path("data/normalized_before_colon_patterns.json")
    with open(patterns_file, encoding='utf-8') as f:
        patterns = json.load(f)
    
    # Categorize each pattern
    categorized = defaultdict(list)
    for item in patterns:
        category = categorize_pattern(item["normalized_pattern"])
        categorized[category].append(item)
    
    # Sort categories by total card count
    sorted_categories = sorted(categorized.items(), key=lambda x: sum(item["total_cards"] for item in x[1]), reverse=True)
    
    print(f"=== Pattern Categories ===")
    print(f"Total patterns: {len(patterns)}")
    print(f"Total categories: {len(categorized)}")
    print()
    
    for category, items in sorted_categories:
        total_cards = sum(item["total_cards"] for item in items)
        pattern_count = len(items)
        print(f"{category}: {pattern_count} unique patterns, {total_cards} total cards")
        for item in items[:3]:
            print(f"  - {item['normalized_pattern']} ({item['count']} times, {item['total_cards']} cards)")
        print()
    
    # Save to file
    output = []
    for category, items in sorted_categories:
        total_cards = sum(item["total_cards"] for item in items)
        pattern_count = len(items)
        
        category_data = {
            "category": category,
            "pattern_count": pattern_count,
            "total_cards": total_cards,
            "patterns": items
        }
        output.append(category_data)
    
    output_file = Path("data/pattern_categories.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"Results saved to {output_file}")


if __name__ == "__main__":
    categorize_patterns()
