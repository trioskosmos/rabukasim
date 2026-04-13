#!/usr/bin/env python3
"""
Verify the new flexible batontouch pattern by checking abilities_extracted.json.
"""

import json
from pathlib import Path

# Load the extracted data
extracted_file = Path(r"C:\Users\trios\.gemini\antigravity\vscode\loveca-copy\data\abilities_extracted.json")
with open(extracted_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Check pattern statistics
if 'analysis' in data and 'dsl_pattern_analysis' in data['analysis']:
    dsl_analysis = data['analysis']['dsl_pattern_analysis']
    
    # Check pattern match counts
    if 'pattern_counts' in dsl_analysis:
        pattern_counts = dsl_analysis['pattern_counts']
        
        print("Pattern match counts for batontouch-related patterns:")
        for pattern_name in sorted(pattern_counts.keys()):
            if 'batontouch' in pattern_name.lower():
                print(f"  {pattern_name}: {pattern_counts[pattern_name]}")
    
    # Check pattern_variables
    if 'pattern_variables' in dsl_analysis:
        pattern_vars = dsl_analysis['pattern_variables']
        
        print("\nPattern variables for batontouch-related patterns:")
        for pattern_name in sorted(pattern_vars.keys()):
            if 'batontouch' in pattern_name.lower():
                count = len(pattern_vars[pattern_name]) if isinstance(pattern_vars[pattern_name], list) else 0
                print(f"  {pattern_name}: {count} items")

print("\nDone")
