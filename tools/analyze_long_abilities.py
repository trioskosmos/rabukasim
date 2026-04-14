import json

# Load the extracted abilities data
with open('data/abilities_extracted_simple.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Find the longest abilities
abilities_by_length = sorted(data['abilities'], key=lambda x: len(x['jp']), reverse=True)

print("=== LONGEST ABILITIES ANALYSIS ===")
print(f"\nTotal abilities: {len(data['abilities'])}")

# Analyze the top 20 longest abilities
for i, ability in enumerate(abilities_by_length[:20]):
    print(f"\n--- Ability {i+1} (Length: {len(ability['jp'])} chars) ---")
    print(f"Original: {ability['jp']}")
    print(f"Coverage: {ability['coverage']:.1%}")
    print(f"Patterns matched: {len(ability['pattern_matches'])}")
    
    # Show each pattern match with extracted variables
    for match in ability['pattern_matches']:
        print(f"\n  Pattern: {match['pattern_name']}")
        print(f"  Structure: {match['structure']}")
        print(f"  Matched text: {match['matched_text'][:100]}..." if len(match['matched_text']) > 100 else f"  Matched text: {match['matched_text']}")
        if match.get('extracted_variables'):
            print(f"  Extracted variables: {match['extracted_variables']}")
    
    # Check for overlap between patterns
    if len(ability['pattern_matches']) > 1:
        print(f"\n  Pattern overlap analysis:")
        for j, match1 in enumerate(ability['pattern_matches']):
            for match2 in ability['pattern_matches'][j+1:]:
                # Check if matched texts overlap
                text1 = match1['matched_text']
                text2 = match2['matched_text']
                if text1 in text2 or text2 in text1:
                    print(f"    {match1['pattern_name']} is SUBSET of {match2['pattern_name']}")
                elif text1 == text2:
                    print(f"    {match1['pattern_name']} DUPLICATES {match2['pattern_name']}")

# Save detailed analysis to file
with open('tools/long_abilities_analysis.txt', 'w', encoding='utf-8') as f:
    f.write("=== LONGEST ABILITIES ANALYSIS ===\n\n")
    for i, ability in enumerate(abilities_by_length[:30]):
        f.write(f"--- Ability {i+1} (Length: {len(ability['jp'])} chars) ---\n")
        f.write(f"Original: {ability['jp']}\n")
        f.write(f"Coverage: {ability['coverage']:.1%}\n")
        f.write(f"Patterns matched: {len(ability['pattern_matches'])}\n\n")
        
        for match in ability['pattern_matches']:
            f.write(f"  Pattern: {match['pattern_name']}\n")
            f.write(f"  Structure: {match['structure']}\n")
            f.write(f"  Matched text: {match['matched_text']}\n")
            if match.get('extracted_variables'):
                f.write(f"  Extracted variables: {match['extracted_variables']}\n")
            f.write("\n")
        f.write("=" * 80 + "\n\n")

print("\nDetailed analysis saved to tools/long_abilities_analysis.txt")
