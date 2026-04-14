import json
from collections import defaultdict
import re

def extract_variable_counts():
    """Extract all variables and their counts from pattern matching results"""
    
    # Load abilities_extracted.json (has pattern_variables data)
    with open('../data/abilities_extracted.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Load abilities_extracted_simple.json (has extracted_variables for each ability)
    with open('../data/abilities_extracted_simple.json', 'r', encoding='utf-8') as f:
        simple_data = json.load(f)
    
    print("=" * 80)
    print("VARIABLE EXTRACTION AND COUNTING")
    print("=" * 80)
    
    # Method 1: Extract from pattern_variables in abilities_extracted.json
    print("\n--- Method 1: From abilities_extracted.json pattern_variables ---")
    pattern_variables = data.get('pattern_variables', {})
    
    variable_counts = defaultdict(int)
    variable_values = defaultdict(set)
    
    for pattern_name, variables_list in pattern_variables.items():
        if variables_list:
            for var_entry in variables_list:
                if isinstance(var_entry, dict):
                    for var_name, var_value in var_entry.items():
                        variable_counts[var_name] += 1
                        variable_values[var_name].add(str(var_value)[:50])  # Truncate long values
                elif isinstance(var_entry, list):
                    for item in var_entry:
                        variable_counts[pattern_name] += 1
                        variable_values[pattern_name].add(str(item)[:50])
    
    print(f"Total unique variable names: {len(variable_counts)}")
    print(f"Total variable occurrences: {sum(variable_counts.values())}")
    
    # Method 2: Extract from abilities_extracted_simple.json extracted_variables
    print("\n--- Method 2: From abilities_extracted_simple.json extracted_variables ---")
    
    template_variable_counts = defaultdict(int)
    template_variable_examples = defaultdict(set)
    
    for ability in simple_data['abilities']:
        if 'pattern_matches' in ability:
            for match in ability['pattern_matches']:
                if 'extracted_variables' in match:
                    template = match['template']
                    variables = match['extracted_variables']
                    
                    # Extract variable names from template
                    var_names = re.findall(r'⟦([^⟧]+)⟧', template)
                    for i, var_name in enumerate(var_names):
                        if i < len(variables):
                            template_variable_counts[var_name] += 1
                            template_variable_examples[var_name].add(variables[i][:50])
    
    print(f"Total unique template variables: {len(template_variable_counts)}")
    print(f"Total template variable occurrences: {sum(template_variable_counts.values())}")
    
    # Combine both methods
    print("\n--- Combined Analysis ---")
    all_variable_counts = defaultdict(int)
    all_variable_examples = defaultdict(set)
    
    # Add from method 1
    for var_name, count in variable_counts.items():
        all_variable_counts[var_name] += count
        all_variable_examples[var_name].update(variable_values[var_name])
    
    # Add from method 2
    for var_name, count in template_variable_counts.items():
        all_variable_counts[var_name] += count
        all_variable_examples[var_name].update(template_variable_examples[var_name])
    
    print(f"Total unique variables (combined): {len(all_variable_counts)}")
    print(f"Total variable occurrences (combined): {sum(all_variable_counts.values())}")
    
    # Sort by count
    sorted_variables = sorted(all_variable_counts.items(), key=lambda x: x[1], reverse=True)
    
    print("\n--- Top 50 Most Common Variables ---")
    for var_name, count in sorted_variables[:50]:
        examples = list(all_variable_examples[var_name])[:3]
        print(f"{var_name}: {count} occurrences")
        print(f"  Examples: {examples}")
    
    # Categorize variables
    print("\n--- Variable Categories ---")
    
    # Game mechanics
    game_mechanics = ['ZONE', 'CARD_TYPE', 'NUMBER', 'RESOURCE', 'HEART', 'GROUP', 'ACTION', 'STATE', 'PLAYER', 'ATTRIBUTE', 'COST', 'SCORE', 'MEMBER', 'TARGET', 'SOURCE', 'DESTINATION']
    game_mechanic_vars = {k: v for k, v in all_variable_counts.items() if any(gm in k.upper() for gm in game_mechanics)}
    
    # Context/trigger
    context_vars = {k: v for k, v in all_variable_counts.items() if any(ctx in k.upper() for ctx in ['TRIGGER', 'CONDITION', 'CONTEXT', 'TURN', 'PHASE', 'DURATION', 'EVENT'])}
    
    # Generic/broad
    generic_vars = {k: v for k, v in all_variable_counts.items() if k.upper() in ['X', 'Y', 'ANY', 'OTHER', 'DIFFERENT', 'ALTERNATIVE']}
    
    print(f"Game mechanic variables: {len(game_mechanic_vars)} ({sum(game_mechanic_vars.values())} occurrences)")
    print(f"Context/trigger variables: {len(context_vars)} ({sum(context_vars.values())} occurrences)")
    print(f"Generic/broad variables: {len(generic_vars)} ({sum(generic_vars.values())} occurrences)")
    
    # Save results
    results = {
        'total_unique_variables': len(all_variable_counts),
        'total_variable_occurrences': sum(all_variable_counts.values()),
        'variable_counts': dict(sorted_variables),
        'variable_examples': {k: list(v)[:5] for k, v in all_variable_examples.items()},
        'categories': {
            'game_mechanics': dict(sorted(game_mechanic_vars.items(), key=lambda x: x[1], reverse=True)),
            'context_triggers': dict(sorted(context_vars.items(), key=lambda x: x[1], reverse=True)),
            'generic_broad': dict(sorted(generic_vars.items(), key=lambda x: x[1], reverse=True))
        }
    }
    
    output_file = '../data/variable_counts_analysis.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to {output_file}")
    
    return results

if __name__ == "__main__":
    results = extract_variable_counts()
