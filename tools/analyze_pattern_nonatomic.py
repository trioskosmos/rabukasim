import json

def analyze_pattern_nonatomic():
    """Analyze which DSL patterns contain non-atomic variables and see if they can be enhanced"""
    
    # Load non-atomic variables
    with open('../data/nonatomic_variables_list.json', 'r', encoding='utf-8') as f:
        nonatomic_data = json.load(f)
    
    # Load abilities data
    with open('../data/abilities_extracted_simple.json', 'r', encoding='utf-8') as f:
        abilities_data = json.load(f)
    
    # Load DSL patterns
    with open('extract_abilities_to_template.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract DSL patterns from the file
    import re
    pattern_match = re.search(r'DSL_PATTERNS = \[(.*?)\]', content, re.DOTALL)
    if pattern_match:
        dsl_patterns_str = pattern_match.group(1)
        # This is a simplified approach - in reality we'd need proper parsing
        print("DSL patterns loaded from file")
    
    print("=" * 80)
    print("PATTERN NON-ATOMIC VARIABLE ANALYSIS")
    print("=" * 80)
    
    # Get non-atomic variables
    nonatomic_vars = [item['value'] for item in nonatomic_data['nonatomic_variables']]
    
    # Build mapping of non-atomic variables to patterns
    pattern_nonatomic_mapping = {}
    
    for ability in abilities_data['abilities']:
        if 'pattern_matches' in ability:
            for match in ability['pattern_matches']:
                pattern_name = match['pattern_name']
                if 'extracted_variables' in match:
                    for var in match['extracted_variables']:
                        if var in nonatomic_vars:
                            if pattern_name not in pattern_nonatomic_mapping:
                                pattern_nonatomic_mapping[pattern_name] = []
                            pattern_nonatomic_mapping[pattern_name].append({
                                'variable': var,
                                'ability': ability['jp'][:50] + '...',
                                'all_vars': match['extracted_variables']
                            })
    
    print(f"\nPatterns with non-atomic variables: {len(pattern_nonatomic_mapping)}")
    
    # Sort by number of non-atomic variables
    sorted_patterns = sorted(pattern_nonatomic_mapping.items(), key=lambda x: len(x[1]), reverse=True)
    
    print(f"\n--- Top 10 Patterns with Most Non-Atomic Variables ---")
    for i, (pattern_name, occurrences) in enumerate(sorted_patterns[:10]):
        print(f"\n{i+1}. {pattern_name} ({len(occurrences)} occurrences)")
        
        # Show unique non-atomic variables for this pattern
        unique_vars = list(set([occ['variable'] for occ in occurrences]))
        print(f"   Unique non-atomic variables: {len(unique_vars)}")
        for var in unique_vars[:5]:  # Show first 5
            count = len([occ for occ in occurrences if occ['variable'] == var])
            print(f"   - {var} ({count} times)")
        if len(unique_vars) > 5:
            print(f"   ... and {len(unique_vars) - 5} more")
        
        # Show example ability
        if occurrences:
            print(f"   Example ability: {occurrences[0]['ability']}")
            print(f"   All variables: {occurrences[0]['all_vars']}")
    
    # Save detailed analysis
    analysis_data = {
        'total_patterns_with_nonatomic': len(pattern_nonatomic_mapping),
        'pattern_analysis': {}
    }
    
    for pattern_name, occurrences in sorted_patterns:
        unique_vars = list(set([occ['variable'] for occ in occurrences]))
        analysis_data['pattern_analysis'][pattern_name] = {
            'count': len(occurrences),
            'unique_nonatomic_vars': len(unique_vars),
            'variables': [{'value': var, 'count': len([occ for occ in occurrences if occ['variable'] == var])} for var in unique_vars],
            'example_abilities': [occ['ability'] for occ in occurrences[:3]]
        }
    
    with open('../data/pattern_nonatomic_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(analysis_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nDetailed analysis saved to ../data/pattern_nonatomic_analysis.json")

if __name__ == "__main__":
    analyze_pattern_nonatomic()
