# IMPORTANT: DSL Pattern Matching Analysis Script
# - Checks compression ratio and pattern coverage for ability clauses
# - Run this after updating extract_abilities_to_template.py to verify improvements
# - Output shows matched/unmatched counts and pattern usage statistics
import json

data = json.load(open('data/abilities_extracted.json', encoding='utf-8'))
dpa = data['analysis']['dsl_pattern_analysis']

print("DSL Pattern Matching Analysis")
print("="*80)
print(f"Total clauses: {dpa['total_clauses']}")
print(f"Matched clauses: {dpa['matched_clauses']}")
print(f"Unmatched clauses: {dpa['unmatched_clauses']}")
print(f"Unique patterns: {dpa['unique_patterns']}")
print(f"Compression ratio: {dpa['compression_ratio']:.2%}")
print()

print("Pattern counts by language structure:")
print("-"*80)
for pattern, count in sorted(dpa['pattern_counts'].items(), key=lambda x: -x[1]):
    print(f"  {pattern:25s}: {count:3d} clauses")
print()

print("Sample matches with structure types:")
print("-"*80)
for match in dpa['matched_sample'][:10]:
    print(f"Pattern: {match['pattern_name']}")
    print(f"Structure: {match['structure']}")
    print(f"Template: {match['template'].replace('⟦X⟧', '[X]').replace('⟦Y⟧', '[Y]').replace('⟦', '[').replace('⟧', ']')}")
    print(f"Variables: {match['variables']}")
    print()
