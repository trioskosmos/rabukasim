#!/usr/bin/env python3
"""
Search for batontouch in abilities_extracted.json to see where it's currently captured.
"""

import json
from pathlib import Path

# Load abilities_extracted.json
extracted_file = Path(r"C:\Users\trios\.gemini\antigravity\vscode\loveca-copy\data\abilities_extracted.json")
with open(extracted_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Search for batontouch in the analysis section
if 'analysis' in data:
    analysis = data['analysis']
    
    # Check pattern_variables
    if 'dsl_pattern_analysis' in analysis:
        dsl_analysis = analysis['dsl_pattern_analysis']
        
        if 'pattern_variables' in dsl_analysis:
            pattern_vars = dsl_analysis['pattern_variables']
            
            print("Pattern names containing 'batontouch':")
            for pattern_name in sorted(pattern_vars.keys()):
                if 'batontouch' in pattern_name.lower():
                    count = len(pattern_vars[pattern_name]) if isinstance(pattern_vars[pattern_name], list) else 0
                    print(f"  {pattern_name}: {count} items")
            
            print("\nAll pattern names (first 100):")
            for i, pattern_name in enumerate(sorted(pattern_vars.keys())[:100]):
                count = len(pattern_vars[pattern_name]) if isinstance(pattern_vars[pattern_name], list) else 0
                print(f"  {i+1}. {pattern_name}: {count}")
        
        # Check ability_pattern_variables (for ability-level patterns)
        if 'ability_pattern_variables' in dsl_analysis:
            ability_vars = dsl_analysis['ability_pattern_variables']
            
            print("\n\nAbility-level pattern names containing 'batontouch':")
            for pattern_name in sorted(ability_vars.keys()):
                if 'batontouch' in pattern_name.lower():
                    count = len(ability_vars[pattern_name]) if isinstance(ability_vars[pattern_name], list) else 0
                    print(f"  {pattern_name}: {count} items")
            
            print("\nAll ability-level pattern names:")
            for i, pattern_name in enumerate(sorted(ability_vars.keys())):
                count = len(ability_vars[pattern_name]) if isinstance(ability_vars[pattern_name], list) else 0
                print(f"  {i+1}. {pattern_name}: {count}")
    
    # Check effects_analysis for batontouch
    if 'effects_analysis' in analysis:
        effects = analysis['effects_analysis']
        if 'unique_effects_data' in effects:
            unique_effects = effects['unique_effects_data']
            
            print("\n\nEffect names containing 'batontouch':")
            for effect_name in sorted(unique_effects.keys()):
                if 'batontouch' in effect_name.lower():
                    count = unique_effects[effect_name]['count']
                    print(f"  {effect_name}: {count} occurrences")

print("\nDone")
