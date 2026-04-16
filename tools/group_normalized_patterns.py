#!/usr/bin/env python3
"""
Group before-colon patterns by normalizing variables (numbers, card counts, etc.).
"""

import json
import re
from collections import defaultdict
from pathlib import Path


def normalize_pattern(pattern):
    """Normalize a pattern by replacing variables with placeholders."""
    normalized = pattern
    
    # Replace energy icon sequences with placeholder
    # Count energy icons and replace with generic pattern
    energy_count = normalized.count('{{icon_energy.png|E}}')
    if energy_count > 0:
        # Remove all energy icons and add placeholder
        normalized = re.sub(r'\{\{icon_energy\.png\|E\}\}', '', normalized)
        normalized = normalized.strip()
        normalized = f"{{icon_energy.png|E}}×{energy_count} " + normalized
        normalized = normalized.strip()
    
    # Replace heart icon sequences with placeholder
    heart_count = normalized.count('{{heart')
    if heart_count > 0:
        # Remove all heart icons and add placeholder
        normalized = re.sub(r'\{\{heart_\d+\.png\|heart\d+\}\}', '', normalized)
        normalized = normalized.strip()
        normalized = f"{{heart}}×{heart_count} " + normalized
        normalized = normalized.strip()
    
    # Replace blade icon sequences with placeholder
    blade_count = normalized.count('{{icon_blade.png|ブレード}}')
    if blade_count > 0:
        normalized = re.sub(r'\{\{icon_blade\.png\|ブレード\}\}', '', normalized)
        normalized = normalized.strip()
        normalized = f"{{icon_blade.png|ブレード}}×{blade_count} " + normalized
        normalized = normalized.strip()
    
    # Replace card numbers with placeholder
    normalized = re.sub(r'(\d+)枚', '*枚', normalized)
    
    # Replace specific numbers with placeholder
    normalized = re.sub(r'\d+', '*', normalized)
    
    # Clean up multiple spaces
    normalized = re.sub(r'\s+', ' ', normalized)
    
    return normalized


def group_normalized_patterns():
    """Group before-colon patterns by normalized variable types."""
    
    # Load abilities
    abilities_file = Path("../data/abilities_extracted_from_cards.json")
    with open(abilities_file, encoding='utf-8') as f:
        data = json.load(f)
    
    abilities = data["unique_abilities"]
    
    # Extract patterns before colon and normalize
    normalized_patterns = []
    
    for ability in abilities:
        triggerless = ability["triggerless_text"]
        if '：' in triggerless:
            before = triggerless.split('：')[0].strip()
            normalized = normalize_pattern(before)
            normalized_patterns.append({
                "original": before,
                "normalized": normalized,
                "card_count": ability["card_count"],
                "triggers": ability["triggers"],
                "use_limit": ability["use_limit"]
            })
    
    # Group by normalized pattern
    pattern_groups = defaultdict(list)
    for item in normalized_patterns:
        pattern_groups[item["normalized"]].append(item)
    
    # Sort by total card count
    sorted_groups = sorted(pattern_groups.items(), key=lambda x: sum(item["card_count"] for item in x[1]), reverse=True)
    
    print(f"=== Normalized Before Colon Pattern Groups ===")
    print(f"Total abilities with colons: {len(normalized_patterns)}")
    print(f"Unique normalized patterns: {len(pattern_groups)}")
    print()
    
    for i, (pattern, items) in enumerate(sorted_groups):
        total_cards = sum(item["card_count"] for item in items)
        triggers = set()
        use_limits = set()
        originals = set()
        for item in items:
            triggers.update(item["triggers"])
            if item["use_limit"]:
                use_limits.add(item["use_limit"])
            originals.add(item["original"])
        
        print(f"Pattern {i+1} (appears {len(items)} times, {total_cards} total cards):")
        print(f"  Normalized: {pattern}")
        if len(originals) > 1:
            print(f"  Original variations ({len(originals)}):")
            for orig in list(originals)[:3]:
                print(f"    - {orig}")
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
        originals = []
        for item in items:
            triggers.update(item["triggers"])
            if item["use_limit"]:
                use_limits.add(item["use_limit"])
            originals.append(item["original"])
        
        output.append({
            "normalized_pattern": pattern,
            "count": len(items),
            "total_cards": total_cards,
            "original_variations": list(set(originals)),
            "triggers": list(triggers),
            "use_limits": list(use_limits)
        })
    
    output_file = Path("../data/normalized_before_colon_patterns.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"Results saved to {output_file}")


if __name__ == "__main__":
    group_normalized_patterns()
