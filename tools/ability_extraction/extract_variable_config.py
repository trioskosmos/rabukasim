#!/usr/bin/env python3
"""
One-time script to extract current variables from ability_coverage_log.json
and write them to variable_config.json for use in extract_card_abilities.py
"""

import json
from pathlib import Path

def extract_variable_config():
    """Extract variable configuration from coverage log."""
    coverage_file = Path("data/ability_coverage_log.json")
    config_file = Path("tools/ability_extraction/variable_config.json")
    
    # Load coverage log
    with open(coverage_file, 'r', encoding='utf-8') as f:
        coverage_data = json.load(f)
    
    unique_vars = coverage_data['unique_variables']
    
    # Create config structure
    config = {
        'card_types': unique_vars['card_types'],
        'zones': unique_vars['zones'],
        'players': unique_vars['players'],
        'positions': unique_vars['positions'],
        'timing_modifiers': unique_vars['timing_modifiers'],
        'group_names': unique_vars['group_names'],
        'character_names': unique_vars['character_names'],
    }
    
    # Write config file
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print(f"Variable configuration written to {config_file}")
    print(f"Card types: {len(config['card_types'])}")
    print(f"Zones: {len(config['zones'])}")
    print(f"Players: {len(config['players'])}")
    print(f"Positions: {len(config['positions'])}")
    print(f"Timing modifiers: {len(config['timing_modifiers'])}")
    print(f"Group names: {len(config['group_names'])}")
    print(f"Character names: {len(config['character_names'])}")

if __name__ == "__main__":
    extract_variable_config()
