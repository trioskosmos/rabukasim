import json
from collections import Counter
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('data/abilities_extracted.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Get pattern variables
pattern_variables = data['analysis']['dsl_pattern_analysis']['pattern_variables']

# Zone names to match
zones = ['控え室', '手札', 'ステージ', 'デッキ', 'エネルギー置き場', 'ライブカード置き場', '成功ライブカード置き場']

# Character/group names to match
groups = ["μ's", 'Aqours', 'Liella!', '虹ヶ咲', '蓮ノ空', 'SaintSnow', 'lilywhite', 'BiBi', 'Printemps', 'Guilty Kiss', 'CYaRon!']

# Resource types
resources = ['ブレード', 'ハート', 'エネルギー', 'blade', 'heart', 'energy']

print("SEMANTIC GRANULARIZATION ANALYSIS")
print("=" * 80)

# Analyze high-priority patterns for zone/group/resource matches
high_priority = ['add_from_discard', 'place_to_zone', 'duration_gain', 'icon_embedded_action', 'basic_action_discard']

for pattern in high_priority:
    if pattern not in pattern_variables:
        continue
    
    variables_list = pattern_variables[pattern]
    
    print(f"\n{pattern} ({len(variables_list)} total matches)")
    print("-" * 80)
    
    # Count zone occurrences
    zone_counts = Counter()
    group_counts = Counter()
    resource_counts = Counter()
    
    for vars in variables_list:
        for var in vars:
            for zone in zones:
                if zone in var:
                    zone_counts[zone] += 1
            for group in groups:
                if group in var:
                    zone_counts[group] += 1
            for resource in resources:
                if resource in var:
                    resource_counts[resource] += 1
    
    print("Top zones found:")
    for zone, count in zone_counts.most_common(10):
        print(f"  {zone}: {count}")
    
    print("\nTop groups found:")
    for group, count in group_counts.most_common(10):
        print(f"  {group}: {count}")
    
    print("\nTop resources found:")
    for resource, count in resource_counts.most_common(10):
        print(f"  {resource}: {count}")

print("\n" + "=" * 80)
print("RECOMMENDATION:")
print("=" * 80)
print("Focus on patterns with high zone/group/resource frequency.")
print("Create specific patterns for:")
print("1. Zone-specific actions (e.g., place_to_discard, place_to_hand)")
print("2. Group-specific filters (e.g., add_μs_from_discard)")
print("3. Resource-specific gains (e.g., gain_blades, gain_hearts)")
