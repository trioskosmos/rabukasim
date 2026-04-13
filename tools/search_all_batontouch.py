#!/usr/bin/env python3
"""
Search for all batontouch-related patterns in abilities_extracted.json.
"""

import json
from pathlib import Path

# Load the extracted data
extracted_file = Path(r"C:\Users\trios\.gemini\antigravity\vscode\loveca-copy\data\abilities_extracted.json")
with open(extracted_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Check pattern_variables
if 'analysis' in data and 'dsl_pattern_analysis' in data['analysis']:
    dsl_analysis = data['analysis']['dsl_pattern_analysis']
    
    if 'pattern_variables' in dsl_analysis:
        pattern_vars = dsl_analysis['pattern_variables']
        
        print("All pattern names containing 'batontouch':")
        for pattern_name in sorted(pattern_vars.keys()):
            if 'batontouch' in pattern_name.lower():
                count = len(pattern_vars[pattern_name]) if isinstance(pattern_vars[pattern_name], list) else 0
                print(f"  {pattern_name}: {count} items")
        
        print("\nAll pattern names (first 50):")
        for i, pattern_name in enumerate(sorted(pattern_vars.keys())[:50]):
            count = len(pattern_vars[pattern_name]) if isinstance(pattern_vars[pattern_name], list) else 0
            print(f"  {i+1}. {pattern_name}: {count}")

print("\nDone")
