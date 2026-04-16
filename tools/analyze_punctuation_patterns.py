#!/usr/bin/env python3
"""
Analyze punctuation patterns in abilities to understand actual structure.
"""
import json
from collections import defaultdict

# Read the abilities file
with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Categorize by punctuation structure
patterns = defaultdict(list)
pattern_counts = defaultdict(int)

for ability in data['unique_abilities']:
    costless_text = ability['costless_text']
    
    # Count punctuation
    comma_count = costless_text.count('、')
    period_count = costless_text.count('。')
    
    # Create pattern key
    pattern_key = f"{period_count}P_{comma_count}C"
    patterns[pattern_key].append(costless_text)
    pattern_counts[pattern_key] += 1

# Sort patterns by frequency
sorted_patterns = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)

# Write analysis report
with open('data/punctuation_pattern_analysis.txt', 'w', encoding='utf-8') as f:
    f.write("=" * 80 + "\n")
    f.write("PUNCTUATION PATTERN ANALYSIS\n")
    f.write("=" * 80 + "\n\n")
    
    f.write(f"Total unique abilities: {len(data['unique_abilities'])}\n")
    f.write(f"Total pattern types: {len(sorted_patterns)}\n\n")
    
    f.write("=" * 80 + "\n")
    f.write("PATTERN FREQUENCY\n")
    f.write("=" * 80 + "\n\n")
    
    for pattern, count in sorted_patterns:
        f.write(f"{pattern}: {count} abilities\n")
    
    f.write("\n" + "=" * 80 + "\n")
    f.write("DETAILED PATTERN BREAKDOWN\n")
    f.write("=" * 80 + "\n\n")
    
    for pattern, count in sorted_patterns[:20]:  # Show top 20 patterns
        f.write(f"\n{'=' * 80}\n")
        f.write(f"Pattern: {pattern} ({count} abilities)\n")
        f.write("=" * 80 + "\n\n")
        
        # Show first 5 examples for each pattern
        for i, text in enumerate(patterns[pattern][:5], 1):
            f.write(f"[{i}] {text}\n")
        
        if len(patterns[pattern]) > 5:
            f.write(f"... and {len(patterns[pattern]) - 5} more\n")

print("Analysis complete. See data/punctuation_pattern_analysis.txt")
