#!/usr/bin/env python3
"""
Analyze pattern match counts to identify patterns with specific match counts.
Looking for patterns with 133, 126, and 124 matches.
"""

import json
from pathlib import Path
from collections import Counter

# Load abilities_extracted.json
data_file = Path(r"C:\Users\trios\.gemini\antigravity\vscode\loveca-copy\data\abilities_extracted.json")
with open(data_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Access the dsl_pattern_analysis section
if 'analysis' in data and 'dsl_pattern_analysis' in data['analysis']:
    dsl_analysis = data['analysis']['dsl_pattern_analysis']

    # Look for pattern match statistics
    if 'pattern_match_counts' in dsl_analysis:
        pattern_counts = dsl_analysis['pattern_match_counts']
        print("Pattern Match Counts:")
        for pattern_name, count in pattern_counts.items():
            print(f"  {pattern_name}: {count} matches")
            if count in [133, 126, 124]:
                print(f"    *** TARGET MATCH COUNT ***")

    # Look for matched_sample to count pattern occurrences
    if 'matched_sample' in dsl_analysis:
        matched_sample = dsl_analysis['matched_sample']
        pattern_counter = Counter()
        for item in matched_sample:
            if 'pattern_name' in item:
                pattern_counter[item['pattern_name']] += 1

        print("\nPattern counts from matched_sample:")
        for pattern_name, count in pattern_counter.most_common():
            print(f"  {pattern_name}: {count} matches")
            if count in [133, 126, 124]:
                print(f"    *** TARGET MATCH COUNT ***")

    # Look for ability_pattern_variables to count pattern occurrences
    if 'ability_pattern_variables' in dsl_analysis:
        apv = dsl_analysis['ability_pattern_variables']
        if 'trigger_clause_sequence' in apv:
            tcs = apv['trigger_clause_sequence']
            pattern_counter = Counter()
            for sequence in tcs:
                if isinstance(sequence, list) and len(sequence) > 1:
                    pattern_counter[sequence[1]] += 1

            print("\nPattern counts from trigger_clause_sequence:")
            for pattern_name, count in pattern_counter.most_common():
                print(f"  {pattern_name}: {count} matches")
                if count in [133, 126, 124]:
                    print(f"    *** TARGET MATCH COUNT ***")
else:
    print("Could not find dsl_pattern_analysis section")
