import json

def analyze_atomic_decomposition_results():
    """Analyze the results of atomic variable decomposition"""
    
    # Load the processed data
    with open('../data/abilities_extracted_with_atomic.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("=" * 80)
    print("ATOMIC DECOMPOSITION RESULTS ANALYSIS")
    print("=" * 80)
    
    # Count atomic components
    atomic_component_counts = {}
    total_atomic_vars = 0
    abilities_with_atomic = 0
    
    for ability in data['abilities']:
        if 'pattern_matches' in ability:
            for match in ability['pattern_matches']:
                if 'atomic_variables' in match and match['atomic_variables']:
                    abilities_with_atomic += 1
                    for var_name, atomic_components in match['atomic_variables'].items():
                        for component_type, component_value in atomic_components.items():
                            if component_type not in atomic_component_counts:
                                atomic_component_counts[component_type] = 0
                            atomic_component_counts[component_type] += 1
                            total_atomic_vars += 1
    
    print(f"\nAbilities with atomic decomposition: {abilities_with_atomic}/{data['total_unique_abilities']}")
    print(f"Total atomic components extracted: {total_atomic_vars}")
    
    print("\n--- Atomic Component Types ---")
    for component_type, count in sorted(atomic_component_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"{component_type}: {count} occurrences")
    
    # Show detailed examples
    print("\n--- Detailed Examples ---")
    example_count = 0
    for ability in data['abilities']:
        if example_count >= 5:
            break
        if 'pattern_matches' in ability:
            for match in ability['pattern_matches']:
                if 'atomic_variables' in match and match['atomic_variables']:
                    print(f"\nAbility: {ability['jp'][:60]}...")
                    print(f"Pattern: {match['pattern_name']}")
                    print(f"Original variables: {match['extracted_variables']}")
                    print(f"Atomic variables: {match['atomic_variables']}")
                    example_count += 1
                    break
    
    # Calculate atomic coverage
    print("\n--- Atomic Coverage Analysis ---")
    original_vars_count = 0
    atomic_vars_count = 0
    
    for ability in data['abilities']:
        if 'pattern_matches' in ability:
            for match in ability['pattern_matches']:
                if 'extracted_variables' in match:
                    original_vars_count += len(match['extracted_variables'])
                if 'atomic_variables' in match:
                    atomic_vars_count += len(match['atomic_variables'])
    
    print(f"Total original variables: {original_vars_count}")
    print(f"Total atomic variable groups: {atomic_vars_count}")
    print(f"Average atomic components per variable group: {total_atomic_vars / atomic_vars_count:.1f}" if atomic_vars_count > 0 else "N/A")
    
    # Save analysis
    analysis = {
        'abilities_with_atomic': abilities_with_atomic,
        'total_abilities': data['total_unique_abilities'],
        'total_atomic_components': total_atomic_vars,
        'component_counts': atomic_component_counts,
        'original_vars_count': original_vars_count,
        'atomic_vars_count': atomic_vars_count
    }
    
    with open('../data/atomic_decomposition_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    
    print(f"\nAnalysis saved to ../data/atomic_decomposition_analysis.json")

if __name__ == "__main__":
    analyze_atomic_decomposition_results()
