import json
from collections import defaultdict

def analyze_atomic_decomposition():
    """Analyze if all abilities are decomposed to atomic level"""
    
    # Load simplified extracted data (has 627 abilities from main script)
    with open('../data/abilities_extracted_simple.json', 'r', encoding='utf-8') as f:
        simple_data = json.load(f)
    
    # Load extracted data (from main script)
    with open('../data/abilities_extracted.json', 'r', encoding='utf-8') as f:
        extracted_data = json.load(f)
    
    print("=" * 80)
    print("ATOMIC DECOMPOSITION ANALYSIS")
    print("=" * 80)
    
    # Simple data analysis (627 abilities)
    print("\n--- Simplified Data Analysis (627 Abilities) ---")
    print(f"Total unique abilities: {simple_data['total_unique_abilities']}")
    
    # Analyze pattern matches in simple data
    abilities_with_patterns = 0
    abilities_without_patterns = 0
    pattern_distribution = defaultdict(int)
    
    for ability in simple_data['abilities']:
        if ability.get('pattern_matches') and len(ability['pattern_matches']) > 0:
            abilities_with_patterns += 1
            for match in ability['pattern_matches']:
                pattern_distribution[match['pattern_name']] += 1
        else:
            abilities_without_patterns += 1
    
    print(f"Abilities with pattern matches: {abilities_with_patterns}")
    print(f"Abilities without pattern matches: {abilities_without_patterns}")
    print(f"Pattern match rate: {abilities_with_patterns / simple_data['total_unique_abilities'] * 100:.1f}%")
    print(f"Unique pattern types: {len(pattern_distribution)}")
    
    # Extracted data analysis
    print("\n--- Extracted Data Analysis (from main script) ---")
    extracted_metadata = extracted_data.get('dsl_pattern_analysis', {})
    print(f"Total abilities: {extracted_metadata.get('total_texts', 'N/A')}")
    print(f"Total coverage: {extracted_metadata.get('total_coverage_percentage', 'N/A')}%")
    print(f"Unique patterns: {extracted_metadata.get('unique_patterns', 'N/A')}")
    
    # Overall atomic decomposition assessment
    print("\n" + "=" * 80)
    print("ATOMIC DECOMPOSITION ASSESSMENT")
    print("=" * 80)
    
    total_abilities = simple_data['total_unique_abilities']
    pattern_match_rate = (abilities_with_patterns / total_abilities) * 100 if total_abilities > 0 else 0
    
    print(f"\nTotal abilities: {total_abilities}")
    print(f"Pattern match rate: {pattern_match_rate:.1f}%")
    print(f"Unique patterns used: {len(pattern_distribution)}")
    print(f"Average patterns per ability: {abilities_with_patterns / total_abilities:.1f}")
    
    if pattern_match_rate >= 95:
        print("\n[EXCELLENT] Nearly all abilities are atomically decomposed")
    elif pattern_match_rate >= 80:
        print("\n[GOOD] Most abilities are atomically decomposed")
    elif pattern_match_rate >= 60:
        print("\n[MODERATE] Significant portion of abilities lack atomic decomposition")
    else:
        print("\n[POOR] Most abilities lack atomic decomposition")
    
    print(f"\nRecommendation: {'Current atomic decomposition is sufficient' if pattern_match_rate >= 80 else 'Need to improve atomic decomposition coverage'}")

if __name__ == "__main__":
    analyze_atomic_decomposition()
