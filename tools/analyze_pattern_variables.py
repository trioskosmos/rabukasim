#!/usr/bin/env python3
"""
Analyze pattern variables for heart_specification, look_top, and basic_action_draw.
Extract variables, categorize them, and determine granularization potential.
"""

import json
from pathlib import Path
from collections import Counter, defaultdict

# Load abilities_extracted.json
data_file = Path(r"C:\Users\trios\.gemini\antigravity\vscode\loveca-copy\data\abilities_extracted.json")
with open(data_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Access pattern_variables
pattern_vars = data['analysis']['dsl_pattern_analysis']['pattern_variables']

target_patterns = {
    'heart_specification': 133,
    'look_top': 126,
    'basic_action_draw': 124
}

for pattern_name, expected_count in target_patterns.items():
    print(f"\n{'='*60}")
    print(f"Analyzing: {pattern_name} ({expected_count} matches)")
    print(f"{'='*60}")
    
    if pattern_name not in pattern_vars:
        print(f"Pattern {pattern_name} not found in pattern_variables")
        continue
    
    variables = pattern_vars[pattern_name]
    print(f"Actual count: {len(variables)}")
    
    if not variables:
        print("No variables found")
        continue
    
    # Analyze variable structure
    print(f"\nVariable structure analysis:")
    print(f"  Type: {type(variables)}")
    
    if isinstance(variables, list):
        print(f"  Sample items (first 3):")
        for i, var in enumerate(variables[:3]):
            print(f"    [{i}]: {var}")
        
        # Extract unique variable values
        if isinstance(variables[0], dict):
            # If variables are dicts, analyze keys and values
            print(f"\nVariable keys:")
            all_keys = set()
            for var in variables:
                all_keys.update(var.keys())
            for key in sorted(all_keys):
                print(f"  - {key}")
            
            # Analyze values for each key
            print(f"\nVariable value analysis:")
            for key in sorted(all_keys):
                values = [var.get(key) for var in variables if key in var]
                unique_values = set(str(v) for v in values)
                print(f"  {key}:")
                print(f"    Unique values: {len(unique_values)}")
                print(f"    Sample: {list(unique_values)[:5]}")
                
        elif isinstance(variables[0], (list, tuple)):
            # If variables are lists/tuples, analyze elements
            print(f"\nVariable elements:")
            element_counts = Counter()
            for var in variables:
                if isinstance(var, (list, tuple)):
                    for elem in var:
                        element_counts[str(elem)] += 1
            for elem, count in element_counts.most_common(20):
                print(f"  {elem}: {count}")
                
        else:
            # Simple values
            print(f"\nVariable values:")
            value_counts = Counter(str(v) for v in variables)
            for value, count in value_counts.most_common(20):
                print(f"  {value}: {count}")
    
    # Determine granularization potential
    print(f"\nGranularization Assessment:")
    if isinstance(variables, list) and len(variables) > 10:
        print(f"  ✓ High match count ({len(variables)}) - good candidate for granularization")
        
        if isinstance(variables[0], dict):
            num_keys = len(set().union(*[var.keys() for var in variables]))
            print(f"  ✓ Has {num_keys} variable dimensions")
            
            # Check if values are diverse
            for key in sorted(set().union(*[var.keys() for var in variables])):
                values = [var.get(key) for var in variables if key in var]
                unique_ratio = len(set(str(v) for v in values)) / len(values)
                print(f"    {key}: {unique_ratio:.2%} unique values")
                if unique_ratio > 0.3:
                    print(f"      → Can granularize by {key}")
        else:
            unique_ratio = len(set(str(v) for v in variables)) / len(variables)
            print(f"  Unique ratio: {unique_ratio:.2%}")
            if unique_ratio > 0.3:
                print(f"  ✓ High diversity - good for granularization")
    else:
        print(f"  ✗ Low match count - may not need granularization")

print(f"\n{'='*60}")
print("Analysis complete")
print(f"{'='*60}")
