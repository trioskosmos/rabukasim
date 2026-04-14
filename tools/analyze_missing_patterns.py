#!/usr/bin/env python3
"""
Analyze abilities_extracted.json to identify patterns not covered by DSL_PATTERNS.
"""

import json
from pathlib import Path

# Read the extracted abilities
with open('data/abilities_extracted.json', encoding='utf-8') as f:
    abilities = json.load(f)

# Collect unique clause patterns
clause_patterns = {}
for ability in abilities:
    for clause in ability['clauses']:
        # Normalize for pattern matching
        normalized = clause
        
        # Extract pattern type based on structure
        if '：' in normalized:
            pattern_type = 'cost_effect'
        elif '場合' in normalized:
            pattern_type = 'conditional'
        elif 'から' in normalized and '加える' in normalized:
            pattern_type = 'add_from_zone'
        elif '見る' in normalized:
            pattern_type = 'look'
        elif '置く' in normalized:
            pattern_type = 'place'
        elif '引く' in normalized:
            pattern_type = 'draw'
        elif '得る' in normalized:
            pattern_type = 'gain'
        else:
            pattern_type = 'other'
        
        if pattern_type not in clause_patterns:
            clause_patterns[pattern_type] = []
        
        clause_patterns[pattern_type].append(clause)

# Write analysis
with open('pattern_analysis.txt', 'w', encoding='utf-8') as f:
    f.write("PATTERN TYPE ANALYSIS\n")
    f.write("=" * 50 + "\n\n")
    
    for pattern_type, clauses in sorted(clause_patterns.items()):
        f.write(f"{pattern_type}: {len(clauses)} clauses\n")
        f.write("-" * 50 + "\n")
        
        # Show unique patterns (first 10)
        unique_clauses = sorted(set(clauses))[:10]
        for clause in unique_clauses:
            f.write(f"  {clause}\n")
        
        if len(clauses) > 10:
            f.write(f"  ... and {len(clauses) - 10} more\n")
        f.write("\n")

print("Pattern analysis written to pattern_analysis.txt")
