import json

# Load the extracted abilities data
with open('data/abilities_extracted.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Find the longest abilities
abilities_with_length = []
for ability in data['dsl_pattern_analysis']['text_matches']:
    abilities_with_length.append({
        'original': ability['original'],
        'length': len(ability['original']),
        'matches': ability['matches'],
        'coverage': ability['coverage'],
    })

# Sort by length
abilities_with_length.sort(key=lambda x: x['length'], reverse=True)

print("=== LONGEST ABILITIES AND THEIR BREAKDOWN ===\n")

for i, ability in enumerate(abilities_with_length[:10]):
    print(f"--- Ability {i+1} (Length: {ability['length']}, Coverage: {ability['coverage']:.1%}) ---")
    print(f"Original: {ability['original'][:120]}...")
    print(f"\nMatches:")
    for j, match in enumerate(ability['matches']):
        print(f"  {j+1}. Pattern: {match['pattern_name']}")
        print(f"     Matched: {match['matched_text'][:60]}...")
        print(f"     Variables: {match['variables']}")
        
        if 'decomposed_variables' in match and match['decomposed_variables']:
            print(f"     Decomposed variables:")
            for k, var_decomp in enumerate(match['decomposed_variables']):
                var_text = match['variables'][k]
                is_atomic = var_decomp.get('atomic', True)
                print(f"       {k+1}. Length {len(var_text)}, Atomic: {is_atomic}")
                if not is_atomic and var_decomp.get('decomposition'):
                    for sub_decomp in var_decomp['decomposition']:
                        print(f"          -> {sub_decomp['match']['pattern_name']}: {sub_decomp['match']['matched_text'][:40]}...")
                elif len(var_text) > 30:
                    print(f"          WARNING: Long variable marked atomic: {var_text[:40]}...")
    print()
