#!/usr/bin/env python3
"""
Generate Rust constants for hardcoded card abilities.

This script extracts cards with hardcoded rules and generates a Rust file
with named constants instead of magic numbers.
"""

import json
import sys
from pathlib import Path

def extract_hardcoded_cards(compiled_json_path: str) -> dict:
    """Extract cards with hardcoded implementations from compiled data."""
    try:
        with open(compiled_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: {compiled_json_path} not found", file=sys.stderr)
        return {}
    
    # These are the hardcoded card IDs from hardcoded.rs
    # organized by rule type
    hardcoded_groups = {
        'PAY_ENERGY_1_AB_0': [64, 159, 682, 163, 688, 234, 4330, 309, 472, 473, 474, 501, 4597, 542, 545],
        'PAY_ENERGY_0_AB_0': [577],
        'PAY_ENERGY_1_AB_1': [722, 873, 882, 4978],
    }
    
    results = {}
    for group_name, card_ids in hardcoded_groups.items():
        results[group_name] = []
        for card_id in card_ids:
            card_data = None
            # Check all DB types
            for db_type in ['member_db', 'live_db', 'energy_db']:
                if str(card_id) in data.get(db_type, {}):
                    card_data = data[db_type][str(card_id)]
                    break
            
            if card_data:
                name = card_data.get('name', f'Card {card_id}')
                results[group_name].append({'card_id': card_id, 'name': name})
            else:
                results[group_name].append({'card_id': card_id, 'name': f'Unknown Card {card_id}'})
    
    return results

def generate_rust_constants(hardcoded_data: dict) -> str:
    """Generate Rust constants from hardcoded card data."""
    lines = [
        "//! Hardcoded card IDs and ability indices for special rule handling",
        "//! ",
        "//! These are extracted from the hardcoded_abilities() match statement.",
        "//! Cards listed here have special-case implementations rather than being",
        "//! decoded from compiled bytecode.",
        "",
        "// Card IDs with hardcoded rule implementations",
    ]
    
    # Generate constants for each group
    for group_name, cards in hardcoded_data.items():
        card_ids = [c['card_id'] for c in cards]
        const_name = f"CARD_HARDCODED_{group_name}"
        
        if not card_ids:
            continue
        
        cards_str = ", ".join(str(cid) for cid in card_ids)
        lines.append(f"pub const {const_name}: &[i32] = &[{cards_str}];")
    
    lines.extend([
        "",
        "// Ability indices",
        "pub const ABILITY_IDX_0: usize = 0;",
        "pub const ABILITY_IDX_1: usize = 1;",
        "",
        "/// Get the energy cost for a hardcoded ability, if one exists",
        "/// Returns `Some(energy_cost)` if the card/ability pair is hardcoded, or `None`",
        "pub fn get_hardcoded_energy_cost(card_id: i32, ability_idx: usize) -> Option<i32> {",
    ])
    
    # Add rules for each group
    for group_name, cards in hardcoded_data.items():
        const_name = f"CARD_HARDCODED_{group_name}"
        if 'PAY_ENERGY' in group_name:
            # Extract energy cost from group name
            parts = group_name.split('_')
            energy_val = parts[2]  # e.g., "1" from "PAY_ENERGY_1_AB_0"
            ab_idx = parts[4]  # e.g., "0" from "PAY_ENERGY_1_AB_0"
            
            lines.append(f"    // Ability {ab_idx} with {energy_val} energy cost")
            lines.append(f"    if ability_idx == ABILITY_IDX_{ab_idx} && {const_name}.contains(&card_id) {{")
            lines.append(f"        return Some({energy_val});")
            lines.append("    }")
            lines.append("")
    
    lines.extend([
        "    None",
        "}",
    ])
    
    return "\n".join(lines)

def main():
    """Main entry point."""
    # Find compiled cards file
    compiled_paths = [
        'data/cards_compiled.json',
        'engine/data/cards_compiled.json',
        Path('engine_rust_src').parent / 'data' / 'cards_compiled.json',
    ]
    
    compiled_json = None
    for path in compiled_paths:
        if Path(path).exists():
            compiled_json = path
            break
    
    if not compiled_json:
        print(f"Warning: Could not find compiled cards file", file=sys.stderr)
        # Use stub data
        hardcoded_data = {
            'PAY_ENERGY_1_AB_0': [],
            'PAY_ENERGY_0_AB_0': [],
            'PAY_ENERGY_1_AB_1': [],
        }
    else:
        hardcoded_data = extract_hardcoded_cards(compiled_json)
    
    # Generate Rust constants
    rust_code = generate_rust_constants(hardcoded_data)
    print(rust_code)

if __name__ == '__main__':
    main()
