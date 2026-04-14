import json

# Load the extracted abilities data
with open('data/abilities_extracted.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

def print_decomposition_tree(decomp, indent=0):
    """Recursively print decomposition tree."""
    prefix = "  " * indent
    if decomp.get('atomic'):
        print(f"{prefix}ATOMIC: {decomp['text'][:50]}...")
    else:
        print(f"{prefix}DECOMPOSED: {decomp['text'][:50]}...")
        if decomp.get('decomposition'):
            for sub_decomp in decomp['decomposition']:
                match = sub_decomp['match']
                print(f"{prefix}  Pattern: {match['pattern_name']}")
                print(f"{prefix}  Matched: {match['matched_text'][:40]}...")
                print(f"{prefix}  Variables: {match['variables']}")
                for var_decomp in sub_decomp['decomposed_variables']:
                    print_decomposition_tree(var_decomp, indent + 2)

# Find abilities with decomposed variables
print("=== ABILITIES WITH DECOMPOSED VARIABLES ===\n")

count_with_decomp = 0
count_without_decomp = 0
total_decomposed_vars = 0
total_atomic_vars = 0

for ability in data['dsl_pattern_analysis']['text_matches']:
    has_decomp = False
    for match in ability['matches']:
        if 'decomposed_variables' in match and match['decomposed_variables']:
            has_decomp = True
            for var_decomp in match['decomposed_variables']:
                if not var_decomp.get('atomic'):
                    total_decomposed_vars += 1
                else:
                    total_atomic_vars += 1
            break
    
    if has_decomp:
        count_with_decomp += 1
        # Show first 5 examples with decomposition
        if count_with_decomp <= 5:
            print(f"\n--- Example {count_with_decomp} ---")
            print(f"Original: {ability['original'][:80]}...")
            for match in ability['matches']:
                if 'decomposed_variables' in match and match['decomposed_variables']:
                    print(f"\nPattern: {match['pattern_name']}")
                    print(f"Variables: {match['variables']}")
                    print(f"\nDecomposition:")
                    for i, var_decomp in enumerate(match['decomposed_variables']):
                        print(f"  Variable {i}:")
                        print_decomposition_tree(var_decomp, indent=2)
                    break
    else:
        count_without_decomp += 1

print(f"\n=== SUMMARY ===")
print(f"Total abilities: {len(data['dsl_pattern_analysis']['text_matches'])}")
print(f"Abilities with decomposition: {count_with_decomp}")
print(f"Abilities without decomposition: {count_without_decomp}")
print(f"Total decomposed variables (non-atomic): {total_decomposed_vars}")
print(f"Total atomic variables: {total_atomic_vars}")

# Analyze which patterns are being used in decomposition
print(f"\n=== PATTERNS USED IN DECOMPOSITION ===")
decomp_patterns = {}
for ability in data['dsl_pattern_analysis']['text_matches']:
    for match in ability['matches']:
        if 'decomposed_variables' in match and match['decomposed_variables']:
            for var_decomp in match['decomposed_variables']:
                if not var_decomp.get('atomic') and var_decomp.get('decomposition'):
                    for sub_decomp in var_decomp['decomposition']:
                        pattern_name = sub_decomp['match']['pattern_name']
                        decomp_patterns[pattern_name] = decomp_patterns.get(pattern_name, 0) + 1

for pattern, count in sorted(decomp_patterns.items(), key=lambda x: x[1], reverse=True):
    print(f"  {pattern}: {count} times")
