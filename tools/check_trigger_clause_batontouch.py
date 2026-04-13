#!/usr/bin/env python3
"""
Check if batontouch appears in trigger_clause_sequence pattern variables.
"""

import json
from pathlib import Path

# Load abilities_extracted.json
extracted_file = Path(r"C:\Users\trios\.gemini\antigravity\vscode\loveca-copy\data\abilities_extracted.json")
with open(extracted_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Check trigger_clause_sequence in ability_pattern_variables
if 'analysis' in data and 'dsl_pattern_analysis' in data['analysis']:
    dsl_analysis = data['analysis']['dsl_pattern_analysis']
    
    if 'ability_pattern_variables' in dsl_analysis:
        ability_vars = dsl_analysis['ability_pattern_variables']
        
        if 'trigger_clause_sequence' in ability_vars:
            trigger_clause_seq = ability_vars['trigger_clause_sequence']
            
            print(f"trigger_clause_sequence has {len(trigger_clause_seq)} entries")
            
            # Search for batontouch in the sequences
            batontouch_count = 0
            batontouch_samples = []
            
            for i, sequence in enumerate(trigger_clause_seq):
                sequence_str = str(sequence)
                if 'batontouch' in sequence_str.lower() or 'バトンタッチ' in sequence_str:
                    batontouch_count += 1
                    if len(batontouch_samples) < 5:
                        batontouch_samples.append(sequence)
            
            print(f"\nFound {batontouch_count} sequences containing batontouch")
            
            if batontouch_samples:
                print("\nSample batontouch sequences:")
                for i, sample in enumerate(batontouch_samples):
                    print(f"  {i+1}. {sample}")

print("\nDone")
