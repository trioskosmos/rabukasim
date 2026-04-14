#!/usr/bin/env python3
"""
Remove patterns with zero matches from extract_abilities_to_template.py
"""

import json
import re
import sys

# Set UTF-8 encoding for output
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Load pattern match counts from abilities_extracted.json
with open('c:\\Users\\trios\\.gemini\\antigravity\\vscode\\loveca-copy\\data\\abilities_extracted_simple.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    abilities_data = data.get('abilities', [])

# Count pattern matches
pattern_counts = {}
for ability in abilities_data:
    for match in ability.get('pattern_matches', []):
        pattern_name = match['pattern_name']
        pattern_counts[pattern_name] = pattern_counts.get(pattern_name, 0) + 1

# Load the extract_abilities_to_template.py file
with open('c:\\Users\\trios\\.gemini\\antigravity\\vscode\\loveca-copy\\tools\\extract_abilities_to_template.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Extract DSL_PATTERNS list
pattern_match = re.search(r'DSL_PATTERNS\s*=\s*\[(.*?)\]\s*\n\s*LITERAL_PATTERNS', content, re.DOTALL)
if pattern_match:
    patterns_str = '[' + pattern_match.group(1) + ']'
    patterns = eval(patterns_str)
    
    # Find unused patterns
    unused_patterns = [p['name'] for p in patterns if p['name'] not in pattern_counts]
    
    print(f"Total patterns: {len(patterns)}")
    print(f"Unused patterns (zero matches): {len(unused_patterns)}")
    print(f"Active patterns: {len(patterns) - len(unused_patterns)}")
    
    print("\nUnused patterns to remove:")
    for name in unused_patterns:
        print(f"  - {name}")
    
    # Create new patterns list without unused patterns
    active_patterns = [p for p in patterns if p['name'] in pattern_counts]
    
    # Generate new patterns string
    new_patterns_str = json.dumps(active_patterns, ensure_ascii=False, indent=8)
    
    # Replace the old patterns with new ones
    new_content = content.replace(patterns_str, new_patterns_str)
    
    # Backup the original file
    with open('c:\\Users\\trios\\.gemini\\antigravity\\vscode\\loveca-copy\\tools\\extract_abilities_to_template.py.backup_unused_removal', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Write the modified content
    with open('c:\\Users\\trios\\.gemini\\antigravity\\vscode\\loveca-copy\\tools\\extract_abilities_to_template.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("\n✓ Removed unused patterns")
    print(f"✓ Backup created: extract_abilities_to_template.py.backup_unused_removal")
    print(f"✓ Modified: extract_abilities_to_template.py")
    
else:
    print("Could not find DSL_PATTERNS in the file")
