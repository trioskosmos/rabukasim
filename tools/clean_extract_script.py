#!/usr/bin/env python3
"""
Clean up extract_card_abilities.py - remove unused code
Keep only essential functions for simplified extraction
"""

essential_functions = [
    'extract_trigger',
    'split_cost_effect', 
    'extract_abilities_from_card',
    'extract_all_abilities',
    'test_parsing',
    'main'
]

essential_imports = [
    'json',
    're',
    'from pathlib import Path',
    'from datetime import datetime',
    'from collections import defaultdict'
]

# Read the original file
with open('tools/ability_extraction/extract_card_abilities.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Build the cleaned version
cleaned_lines = []
in_function = False
current_function = None
function_lines = []
function_indent = 0
keep_function = False

for i, line in enumerate(lines):
    # Check for function definition
    if line.strip().startswith('def '):
        # Save previous function if we were in one
        if in_function:
            if keep_function:
                cleaned_lines.extend(function_lines)
            function_lines = []
            in_function = False
        
        # Start new function
        in_function = True
        current_function = line.strip().split('(')[0].replace('def ', '')
        function_lines = [line]
        function_indent = len(line) - len(line.lstrip())
        keep_function = current_function in essential_functions
    elif in_function:
        function_lines.append(line)
        # Check if function ended (same or less indentation)
        if line.strip() and len(line) - len(line.lstrip()) <= function_indent and not line.strip().startswith('#'):
            # Function ended
            if keep_function:
                cleaned_lines.extend(function_lines)
            function_lines = []
            in_function = False
    else:
        # Not in function, keep if it's essential import or top-level code
        if any(imp in line for imp in essential_imports):
            cleaned_lines.append(line)
        elif line.strip().startswith('#') or line.strip() == '':
            cleaned_lines.append(line)
        elif '__name__' in line:
            cleaned_lines.append(line)

# Handle case where file ends while in function
if in_function and keep_function:
    cleaned_lines.extend(function_lines)

# Write cleaned file
with open('tools/ability_extraction/extract_card_abilities.py', 'w', encoding='utf-8') as f:
    f.writelines(cleaned_lines)

print("Cleaned extract_card_abilities.py - removed unused functions")
