# IMPORTANT: Generate Useful DSL Output with Card References
# - Shows pattern templates with card references
# - Links patterns to specific cards
# - Shows compression statistics
import json

# Load data
abilities_data = json.load(open('data/abilities_from_cards.json', encoding='utf-8'))
extracted_data = json.load(open('data/abilities_extracted.json', encoding='utf-8'))

abilities = abilities_data['abilities']
dpa = extracted_data['analysis']['dsl_pattern_analysis']
ability_dpa = extracted_data['analysis']['dsl_pattern_analysis']

output = []

# Clause-level patterns
output.append("="*80)
output.append("CLAUSE-LEVEL DSL PATTERNS")
output.append("="*80)
output.append(f"Total clauses: {dpa['total_clauses']}")
output.append(f"Matched: {dpa['matched_clauses']} ({dpa['compression_ratio']:.2%})")
output.append(f"Unique patterns: {dpa['unique_patterns']}")
output.append("")
output.append("Top patterns by usage:")
for pattern, count in sorted(dpa['pattern_counts'].items(), key=lambda x: -x[1])[:10]:
    output.append(f"  {pattern}: {count} clauses")

# Ability-level patterns
output.append("")
output.append("="*80)
output.append("ABILITY-LEVEL DSL PATTERNS")
output.append("="*80)
output.append(f"Total abilities: {ability_dpa['total_abilities']}")
output.append(f"Matched: {ability_dpa['matched_abilities']} ({ability_dpa['ability_compression_ratio']:.2%})")
output.append(f"Unique patterns: {ability_dpa['unique_ability_patterns']}")
output.append("")
output.append("Pattern distribution:")
for pattern, count in sorted(ability_dpa['ability_pattern_counts'].items(), key=lambda x: -x[1]):
    output.append(f"  {pattern}: {count} abilities")

# Show examples with card references
output.append("")
output.append("="*80)
output.append("EXAMPLE ABILITIES WITH CARD REFERENCES")
output.append("="*80)

# Create a mapping from ability text to cards
ability_to_cards = {}
for ability in abilities:
    for source in ability['source_ability_texts']:
        jp_text = source['jp']
        cards = source['cards']
        if jp_text not in ability_to_cards:
            ability_to_cards[jp_text] = []
        ability_to_cards[jp_text].extend(cards)

# Show matched ability samples with card references
for matched in ability_dpa['matched_ability_sample'][:5]:
    output.append("")
    output.append(f"Pattern: {matched['pattern_name']}")
    output.append(f"Structure: {matched['structure']}")
    output.append(f"Template: {matched['template']}")
    output.append(f"Original: {matched['original']}")
    cards = ability_to_cards.get(matched['original'], ['Unknown'])
    output.append(f"Cards: {', '.join(cards)}")

# Show unmatched ability
if ability_dpa['unmatched_ability_sample']:
    output.append("")
    output.append("="*80)
    output.append("UNMATCHED ABILITY")
    output.append("="*80)
    unmatched = ability_dpa['unmatched_ability_sample'][0]
    output.append(f"Text: {unmatched}")
    cards = ability_to_cards.get(unmatched, ['Unknown'])
    output.append(f"Cards: {', '.join(cards)}")

# Write output
with open('docs/dsl_useful_output.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print("Output written to docs/dsl_useful_output.txt")
