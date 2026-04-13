#!/usr/bin/env python3
"""
Fix script to resolve duplicate match_dsl_patterns function definitions.
Moves dsl_patterns to module level and deletes incomplete first function.
"""

import re

def fix_extract_script():
    input_file = "tools/extract_abilities_to_template.py"
    output_file = "tools/extract_abilities_to_template.py"
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the first incomplete match_dsl_patterns function (lines 253-1780)
    # It starts with "def match_dsl_patterns" and ends before ABILITY_LEVEL_PATTERNS
    first_func_pattern = r'def match_dsl_patterns\(clauses:.*?\n\n\n# ABILITY-LEVEL DSL PATTERNS'
    match = re.search(first_func_pattern, content, re.DOTALL)
    
    if not match:
        print("Could not find first incomplete function")
        return False
    
    first_func_content = match.group(0)
    
    # Extract dsl_patterns list from the first function
    dsl_patterns_pattern = r'dsl_patterns = \[(.*?)\n    \]'
    dsl_match = re.search(dsl_patterns_pattern, first_func_content, re.DOTALL)
    
    if not dsl_match:
        print("Could not find dsl_patterns list")
        return False
    
    dsl_patterns_list = dsl_match.group(0)
    
    # Remove the first incomplete function
    content = content.replace(first_func_content, "")
    
    # Insert DSL_PATTERNS at module level after ABILITY_LEVEL_PATTERNS
    ability_level_end = "# ABILITY-LEVEL DSL PATTERNS.*?\n\]"
    ability_match = re.search(ability_level_end, content, re.DOTALL)
    
    if not ability_match:
        print("Could not find ABILITY_LEVEL_PATTERNS end")
        return False
    
    ability_end_pos = ability_match.end()
    
    # Create DSL_PATTERNS module-level variable
    dsl_module_level = "\n\n# CLAUSE-LEVEL DSL PATTERNS\nDSL_PATTERNS = " + dsl_patterns_list.replace("dsl_patterns = ", "")
    
    # Insert after ABILITY_LEVEL_PATTERNS
    content = content[:ability_end_pos] + dsl_module_level + content[ability_end_pos:]
    
    # Update the second function to use module-level patterns
    # Find the second function and add dsl_patterns = DSL_PATTERNS
    second_func_pattern = r'(def match_dsl_patterns\(clauses:.*?\n    # Use module-level ability level patterns\n    ability_level_patterns = ABILITY_LEVEL_PATTERNS)'
    second_match = re.search(second_func_pattern, content, re.DOTALL)
    
    if second_match:
        new_line = second_match.group(1) + "\n    dsl_patterns = DSL_PATTERNS"
        content = content.replace(second_match.group(1), new_line)
    
    # Write the fixed content
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fixed {input_file}")
    return True

if __name__ == "__main__":
    fix_extract_script()
