#!/usr/bin/env python3
"""
Search for position change (ポジションチェンジ) in abilities_extracted.json.
"""

import json
from pathlib import Path

# Load abilities_extracted.json
extracted_file = Path(r"C:\Users\trios\.gemini\antigravity\vscode\loveca-copy\data\abilities_extracted.json")
with open(extracted_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

output_lines = []

# Search for ポジションチェンジ in the analysis section
if 'analysis' in data:
    analysis = data['analysis']
    
    # Check pattern_variables
    if 'dsl_pattern_analysis' in analysis:
        dsl_analysis = analysis['dsl_pattern_analysis']
        
        if 'pattern_variables' in dsl_analysis:
            pattern_vars = dsl_analysis['pattern_variables']
            
            output_lines.append("Pattern names containing 'position' or 'ポジション':")
            for pattern_name in sorted(pattern_vars.keys()):
                if 'position' in pattern_name.lower() or 'ポジション' in pattern_name:
                    count = len(pattern_vars[pattern_name]) if isinstance(pattern_vars[pattern_name], list) else 0
                    output_lines.append(f"  {pattern_name}: {count} items")
        
        # Check ability_pattern_variables
        if 'ability_pattern_variables' in dsl_analysis:
            ability_vars = dsl_analysis['ability_pattern_variables']
            
            output_lines.append("\nAbility-level pattern names containing 'position' or 'ポジション':")
            for pattern_name in sorted(ability_vars.keys()):
                if 'position' in pattern_name.lower() or 'ポジション' in pattern_name:
                    count = len(ability_vars[pattern_name]) if isinstance(ability_vars[pattern_name], list) else 0
                    output_lines.append(f"  {pattern_name}: {count} items")
    
    # Check effects_analysis
    if 'effects_analysis' in analysis:
        effects = analysis['effects_analysis']
        if 'unique_effects_data' in effects:
            unique_effects = effects['unique_effects_data']
            
            output_lines.append("\nEffect names containing 'position' or 'ポジション':")
            for effect_name in sorted(unique_effects.keys()):
                if 'position' in effect_name.lower() or 'ポジション' in effect_name:
                    count = unique_effects[effect_name]['count']
                    output_lines.append(f"  {effect_name}: {count} occurrences")

# Also check structures for position change
if 'structures' in data:
    structures = data['structures']
    output_lines.append(f"\nTotal structures: {len(structures)}")
    
    position_count = 0
    for struct in structures:
        if 'ポジションチェンジ' in struct.get('skeleton', ''):
            position_count += 1
            if position_count <= 3:
                output_lines.append(f"\nSample structure with ポジションチェンジ:")
                output_lines.append(f"  Count: {struct['count']}")
                output_lines.append(f"  Skeleton: {struct['skeleton']}")
                output_lines.append(f"  JP example: {struct.get('jp_examples', [''])[0] if struct.get('jp_examples') else ''}")
    
    output_lines.append(f"\nTotal structures containing ポジションチェンジ: {position_count}")

output_lines.append("\nDone")

# Save to file
output_file = Path(r"C:\Users\trios\.gemini\antigravity\vscode\loveca-copy\data\position_change_search.txt")
with open(output_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(output_lines))

print(f"Results saved to {output_file}")
