#!/usr/bin/env python3
"""Script to find duplicate patterns in extract_abilities_to_template.py"""

import ast
import sys
import io
from collections import defaultdict

# Set stdout to UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def extract_patterns_via_ast(file_path):
    """Extract patterns using Python AST with line numbers."""
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        content = f.read()
    
    # Parse the file as Python
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        print(f"Syntax error parsing file: {e}")
        return {'DSL_PATTERNS': [], 'LITERAL_PATTERNS': []}
    
    patterns = {'DSL_PATTERNS': [], 'LITERAL_PATTERNS': []}
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if target.id in ['DSL_PATTERNS', 'LITERAL_PATTERNS']:
                        # Evaluate the node to get the actual data
                        try:
                            pattern_list = ast.literal_eval(node.value)
                            patterns[target.id] = pattern_list
                        except:
                            print(f"Could not evaluate {target.id}")
    
    # Find actual line numbers by searching the file
    lines = content.split('\n')
    
    # Build a map of pattern names to their line numbers
    name_to_lines = defaultdict(list)
    for i, line in enumerate(lines, 1):
        if '"name":' in line:
            # Extract the pattern name from the line
            import re
            match = re.search(r'"name":\s*"([^"]+)"', line)
            if match:
                name = match.group(1)
                name_to_lines[name].append(i)
    
    # Assign line numbers to patterns
    for pattern_list in patterns.values():
        for pattern in pattern_list:
            name = pattern.get('name', '')
            if name and name in name_to_lines:
                # Get the next available line number for this pattern name
                if name_to_lines[name]:
                    pattern['_line'] = name_to_lines[name].pop(0)
    
    return patterns

def find_duplicates(patterns_list, key_fields):
    """Find patterns with identical values in specified key fields."""
    groups = defaultdict(list)
    
    for pattern in patterns_list:
        key = tuple(pattern.get(field, '') for field in key_fields)
        name = pattern.get('name', '')
        line = pattern.get('_line', 0)
        groups[key].append((name, line))
    
    # Find duplicates (groups with more than 1 item)
    duplicates = {}
    for key, info_list in groups.items():
        if len(info_list) > 1:
            duplicates[key] = info_list
    
    return duplicates

def main():
    file_path = 'tools/extract_abilities_to_template.py'
    patterns = extract_patterns_via_ast(file_path)
    
    print("=" * 80)
    print("FINDING DUPLICATE PATTERNS")
    print("=" * 80)
    
    # Check DSL_PATTERNS
    print(f"\nDSL_PATTERNS count: {len(patterns['DSL_PATTERNS'])}")
    dsl_duplicates = find_duplicates(patterns['DSL_PATTERNS'], ['regex', 'template', 'structure'])
    
    if dsl_duplicates:
        print(f"\nFound {len(dsl_duplicates)} duplicate regex patterns:")
        for i, (key, info_list) in enumerate(dsl_duplicates.items(), 1):
            regex, template, structure = key
            print(f"\n--- Duplicate {i} ---")
            for name, line in info_list:
                print(f"  {name} at line {line}")
            print(f"Regex: {regex[:100]}...")
            print(f"Template: {template[:100]}...")
            print(f"Structure: {structure}")
    else:
        print("\nNo duplicate regex patterns found in DSL_PATTERNS")
    
    # Check LITERAL_PATTERNS
    print(f"\nLITERAL_PATTERNS count: {len(patterns['LITERAL_PATTERNS'])}")
    literal_duplicates = find_duplicates(patterns['LITERAL_PATTERNS'], ['literal', 'template', 'structure'])
    
    if literal_duplicates:
        print(f"\nFound {len(literal_duplicates)} duplicate literal patterns:")
        for i, (key, info_list) in enumerate(literal_duplicates.items(), 1):
            literal, template, structure = key
            print(f"\n--- Duplicate {i} ---")
            for name, line in info_list:
                print(f"  {name} at line {line}")
            print(f"Literal: {literal[:100]}...")
            print(f"Template: {template[:100]}...")
            print(f"Structure: {structure}")
    else:
        print("\nNo duplicate literal patterns found in LITERAL_PATTERNS")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total duplicate regex patterns: {len(dsl_duplicates)}")
    print(f"Total duplicate literal patterns: {len(literal_duplicates)}")

if __name__ == "__main__":
    main()
