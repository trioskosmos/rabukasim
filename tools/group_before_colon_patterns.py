#!/usr/bin/env python3
"""
Group all unique triggerless text patterns before the colon.
"""

import json
from collections import Counter, defaultdict
from pathlib import Path


def group_before_colon_patterns():
    """Group all unique patterns before the colon in triggerless_text."""
    
    # Load abilities
    abilities_file = Path("../data/abilities_extracted_from_cards.json")
    with open(abilities_file, encoding='utf-8') as f:
        data = json.load(f)
    
    abilities = data["unique_abilities"]
    
    # Extract patterns before colon
    before_colon_patterns = []
    
    for ability in abilities:
        triggerless = ability["triggerless_text"]
        if '：' in triggerless:
            before = triggerless.split('：')[0].strip()
            before_colon_patterns.append({
                "pattern": before,
                "card_count": ability["card_count"],
                "triggers": ability["triggers"],
                "use_limit": ability["use_limit"]
            })
    
    # Group by pattern
    pattern_groups = defaultdict(list)
    for item in before_colon_patterns:
        pattern_groups[item["pattern"]].append(item)
    
    # Sort by total card count
    sorted_groups = sorted(pattern_groups.items(), key=lambda x: sum(item["card_count"] for item in x[1]), reverse=True)
    
    print(f"=== Before Colon Pattern Groups ===")
    print(f"Total abilities with colons: {len(before_colon_patterns)}")
    print(f"Unique patterns: {len(pattern_groups)}")
    print()
    
    for i, (pattern, items) in enumerate(sorted_groups):
        total_cards = sum(item["card_count"] for item in items)
        triggers = set()
        use_limits = set()
        for item in items:
            triggers.update(item["triggers"])
            if item["use_limit"]:
                use_limits.add(item["use_limit"])
        
        print(f"Pattern {i+1} (appears {len(items)} times, {total_cards} total cards):")
        print(f"  {pattern}")
        if triggers:
            print(f"  Triggers: {list(triggers)}")
        if use_limits:
            print(f"  Use limits: {list(use_limits)}")
        print()
    
    # Save to file
    output = []
    for pattern, items in sorted_groups:
        total_cards = sum(item["card_count"] for item in items)
        triggers = set()
        use_limits = set()
        for item in items:
            triggers.update(item["triggers"])
            if item["use_limit"]:
                use_limits.add(item["use_limit"])
        
        output.append({
            "pattern": pattern,
            "count": len(items),
            "total_cards": total_cards,
            "triggers": list(triggers),
            "use_limits": list(use_limits)
        })
    
    output_file = Path("data/before_colon_pattern_groups.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"Results saved to {output_file}")


if __name__ == "__main__":
    group_before_colon_patterns()
