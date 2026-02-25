#!/usr/bin/env python3
"""Compare two card JSON files and report differences."""

import json
import sys

def main():
    old_path = 'data/cards.json'
    new_path = 'C:/Users/trios/Downloads/cards.json'
    
    # Load both files
    print(f"Loading {old_path}...")
    with open(old_path, 'r', encoding='utf-8') as f:
        old_cards = json.load(f)
    
    print(f"Loading {new_path}...")
    with open(new_path, 'r', encoding='utf-8') as f:
        new_cards = json.load(f)
    
    # Get keys in order
    old_keys = list(old_cards.keys())
    new_keys = list(new_cards.keys())
    
    print(f'\n=== SUMMARY ===')
    print(f'Old file: {len(old_keys)} cards')
    print(f'New file: {len(new_keys)} cards')
    print(f'Difference: {len(new_keys) - len(old_keys)} cards')
    
    # Check if keys are the same set
    old_set = set(old_keys)
    new_set = set(new_keys)
    
    added = new_set - old_set
    removed = old_set - new_set
    
    print(f'\nAdded cards: {len(added)}')
    print(f'Removed cards: {len(removed)}')
    
    if added:
        print('\n=== ADDED CARDS (first 20) ===')
        for k in sorted(added)[:20]:
            print(f'  + {k}: {new_cards[k].get("name", "?")}')
        if len(added) > 20:
            print(f'  ... and {len(added) - 20} more')
    
    if removed:
        print('\n=== REMOVED CARDS ===')
        for k in sorted(removed):
            print(f'  - {k}: {old_cards[k].get("name", "?")}')
    
    # Check order differences for common keys
    common_keys = old_set & new_set
    order_diffs = []
    for key in common_keys:
        old_idx = old_keys.index(key)
        new_idx = new_keys.index(key)
        if old_idx != new_idx:
            order_diffs.append((key, old_idx, new_idx))
    
    if order_diffs:
        print(f'\n=== ORDER CHANGES: {len(order_diffs)} cards ===')
        print('First 20:')
        for key, old_idx, new_idx in order_diffs[:20]:
            print(f'  {key}: position {old_idx} -> {new_idx}')
        if len(order_diffs) > 20:
            print(f'  ... and {len(order_diffs) - 20} more')
    else:
        print('\n=== ORDER: All common cards are in the same order! ===')
    
    # Check for name differences (affects card_id)
    name_diffs = []
    for key in common_keys:
        old_name = old_cards[key].get('name', '')
        new_name = new_cards[key].get('name', '')
        if old_name != new_name:
            name_diffs.append((key, old_name, new_name))
    
    if name_diffs:
        print(f'\n=== NAME DIFFERENCES: {len(name_diffs)} cards ===')
        print('(These WILL affect card_id assignment!)')
        for key, old_name, new_name in name_diffs[:30]:
            print(f'  {key}:')
            print(f'    OLD: "{old_name}"')
            print(f'    NEW: "{new_name}"')
        if len(name_diffs) > 30:
            print(f'  ... and {len(name_diffs) - 30} more')
    
    # Check for ability differences (affects card_id)
    ability_diffs = []
    for key in common_keys:
        old_ability = old_cards[key].get('ability', '')
        new_ability = new_cards[key].get('ability', '')
        if old_ability != new_ability:
            ability_diffs.append((key, old_ability[:80], new_ability[:80]))
    
    if ability_diffs:
        print(f'\n=== ABILITY DIFFERENCES: {len(ability_diffs)} cards ===')
        print('(These WILL affect card_id assignment!)')
        print('First 10:')
        for key, old_ab, new_ab in ability_diffs[:10]:
            print(f'  {key}:')
            print(f'    OLD: {old_ab}...')
            print(f'    NEW: {new_ab}...')
        if len(ability_diffs) > 10:
            print(f'  ... and {len(ability_diffs) - 10} more')
    
    # Summary of potential card_id impacts
    print('\n=== CARD ID IMPACT ASSESSMENT ===')
    critical_changes = len(name_diffs) + len(ability_diffs) + len(order_diffs)
    if critical_changes > 0:
        print(f'WARNING: {critical_changes} changes detected that WILL affect card_id assignment!')
        print('  - Name changes: {} (logic_key uses name)'.format(len(name_diffs)))
        print('  - Ability changes: {} (logic_key uses ability)'.format(len(ability_diffs)))
        print('  - Order changes: {} (affects variant_idx assignment)'.format(len(order_diffs)))
        print('\nTests that use hardcoded card_ids will likely fail!')
    else:
        print('No critical changes detected. Card IDs should remain stable.')

if __name__ == '__main__':
    main()
