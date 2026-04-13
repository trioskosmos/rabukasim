import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('data/abilities_extracted.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Get pattern counts
pattern_counts = data['analysis']['dsl_pattern_analysis']['pattern_counts']

# Check if new specific patterns are matching
new_patterns = [
    'add_live_card_from_discard',
    'add_member_card_from_discard',
    'place_to_discard',
    'place_to_hand',
    'place_to_stage',
    'place_to_deck',
    'duration_gain_blade',
    'duration_gain_heart',
    'icon_embedded_blade',
    'icon_embedded_heart',
]

print("GRANULARIZATION RESULTS")
print("=" * 80)

for pattern in new_patterns:
    count = pattern_counts.get(pattern, 0)
    print(f"{pattern}: {count} matches")

print()

# Check if generic patterns still have matches
generic_patterns = [
    ('add_from_discard', 'add_live_card_from_discard', 'add_member_card_from_discard'),
    ('place_to_zone', 'place_to_discard', 'place_to_hand', 'place_to_stage', 'place_to_deck'),
    ('duration_gain', 'duration_gain_blade', 'duration_gain_heart'),
    ('icon_embedded_action', 'icon_embedded_blade', 'icon_embedded_heart'),
]

print("GENERIC PATTERN REDUCTION")
print("=" * 80)

for generic, *specifics in generic_patterns:
    generic_count = pattern_counts.get(generic, 0)
    specific_total = sum(pattern_counts.get(s, 0) for s in specifics)
    total = generic_count + specific_total
    reduction = (specific_total / total * 100) if total > 0 else 0
    print(f"{generic}: {generic_count} (specifics: {specific_total}, {reduction:.1f}% diverted)")

print()
print(f"Total patterns: {len(pattern_counts)}")
print(f"Total clauses: {data['analysis']['dsl_pattern_analysis']['total_clauses']}")
