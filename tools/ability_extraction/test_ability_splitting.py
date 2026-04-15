#!/usr/bin/env python3
"""
Script to test splitting abilities into game-logic components.
Decomposes abilities into: Trigger, Condition, Player Action, Automatic Effect.
"""

import json
from pathlib import Path
import re

def load_abilities():
    """Load abilities from the extracted abilities JSON file."""
    abilities_file = Path("data/abilities_extracted_from_cards.json")
    with open(abilities_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['unique_abilities']

def split_cost_effect(text: str) -> tuple:
    """
    Split text into cost and effect based on colon separator.
    Returns (cost, effect) tuple.
    """
    if '：' in text:
        parts = text.split('：', 1)
        return parts[0].strip(), parts[1].strip()
    return '', text.strip()

def identify_condition(text: str) -> dict:
    """
    Identify condition phrases in the text.
    Returns dict with condition info.
    """
    condition_markers = [
        '場合', '時', 'とき', 'かぎり', 'につき',
        'そうした場合', 'その後', 'さらに'
    ]
    
    conditions = []
    remaining_text = text
    
    for marker in sorted(condition_markers, key=len, reverse=True):
        if marker in remaining_text:
            # Find the condition before the marker
            marker_pos = remaining_text.find(marker)
            # Look for condition text before marker
            condition_end = marker_pos + len(marker)
            
            # Extract condition (simplified - just get text before marker)
            condition_start = max(0, remaining_text.rfind('、', 0, marker_pos))
            if condition_start == -1:
                condition_start = max(0, remaining_text.rfind('。', 0, marker_pos))
            if condition_start == -1:
                condition_start = 0
            else:
                condition_start += 1  # Skip the separator
            
            condition_text = remaining_text[condition_start:condition_end].strip()
            if condition_text:
                conditions.append({
                    'marker': marker,
                    'text': condition_text,
                    'type': classify_condition_type(marker)
                })
    
    return {
        'has_condition': len(conditions) > 0,
        'conditions': conditions
    }

def classify_condition_type(marker: str) -> str:
    """Classify condition type based on marker."""
    if marker in ['場合', '時', 'とき']:
        return 'conditional'
    elif marker == 'かぎり':
        return 'continuous'
    elif marker == 'につき':
        return 'per_unit'
    elif marker in ['そうした場合', 'その後', 'さらに']:
        return 'follow_up'
    return 'unknown'

def identify_player_actions(text: str) -> dict:
    """
    Identify player decision points in the text.
    Returns dict with player action info.
    """
    player_markers = [
        'てもよい', '選ぶ', '好きな', '以下から1つを選ぶ',
        '代わりに', 'か、'  # OR separator for player choice
    ]
    
    actions = []
    
    for marker in sorted(player_markers, key=len, reverse=True):
        if marker in text:
            # Find context around marker
            marker_pos = text.find(marker)
            context_start = max(0, marker_pos - 20)
            context_end = min(len(text), marker_pos + len(marker) + 20)
            context = text[context_start:context_end]
            
            actions.append({
                'marker': marker,
                'context': context,
                'type': classify_action_type(marker)
            })
    
    return {
        'has_player_action': len(actions) > 0,
        'actions': actions
    }

def classify_action_type(marker: str) -> str:
    """Classify action type based on marker."""
    if 'てもよい' in marker:
        return 'optional'
    elif '選ぶ' in marker:
        return 'choice'
    elif '好きな' in marker:
        return 'free_choice'
    elif '代わりに' in marker:
        return 'alternative'
    elif marker == 'か、':
        return 'or_condition'
    return 'unknown'

def decompose_ability(ability: dict) -> dict:
    """
    Decompose an ability into game-logic components.
    Returns dict with trigger, condition, player_action, automatic_effect.
    """
    full_text = ability.get('full_text', '')
    effect = ability.get('effect', '')
    triggers = ability.get('triggers', [])
    
    # Split cost and effect
    cost, effect_body = split_cost_effect(effect)
    
    # Identify conditions in effect body
    condition_info = identify_condition(effect_body)
    
    # Identify player actions in cost and effect
    cost_actions = identify_player_actions(cost)
    effect_actions = identify_player_actions(effect_body)
    
    # Determine automatic effect (effect without player choices)
    automatic_effect = effect_body
    if cost_actions['has_player_action']:
        automatic_effect = automatic_effect  # Cost has player action
    if effect_actions['has_player_action']:
        automatic_effect = automatic_effect  # Effect has player action
    
    return {
        'trigger': triggers if triggers else ['automatic'],
        'cost': cost,
        'cost_has_player_action': cost_actions['has_player_action'],
        'cost_actions': cost_actions['actions'],
        'effect_body': effect_body,
        'condition': condition_info,
        'effect_has_player_action': effect_actions['has_player_action'],
        'effect_actions': effect_actions['actions'],
        'automatic_effect': automatic_effect,
        'full_text': full_text
    }

def display_decomposition(ability_data: dict, index: int):
    """Display the decomposed ability structure."""
    print(f"\n{'='*80}")
    print(f"ABILITY #{index + 1}")
    print(f"{'='*80}")
    print(f"Full Text: {ability_data['full_text']}")
    print(f"\n--- DECOMPOSED STRUCTURE ---")
    print(f"TRIGGER: {ability_data['trigger']}")
    print(f"\nCOST: {ability_data['cost']}")
    print(f"Cost has player action: {ability_data['cost_has_player_action']}")
    if ability_data['cost_actions']:
        for action in ability_data['cost_actions']:
            print(f"  - {action['type']}: {action['marker']} (context: {action['context']})")
    
    print(f"\nEFFECT BODY: {ability_data['effect_body']}")
    print(f"Effect has condition: {ability_data['condition']['has_condition']}")
    if ability_data['condition']['conditions']:
        for cond in ability_data['condition']['conditions']:
            print(f"  - {cond['type']}: {cond['marker']} (text: {cond['text']})")
    
    print(f"Effect has player action: {ability_data['effect_has_player_action']}")
    if ability_data['effect_actions']:
        for action in ability_data['effect_actions']:
            print(f"  - {action['type']}: {action['marker']} (context: {action['context']})")
    
    print(f"\nAUTOMATIC EFFECT: {ability_data['automatic_effect']}")
    print(f"\n--- GAME LOGIC FLOW ---")
    print(f"1. TRIGGER: {ability_data['trigger']}")
    if ability_data['condition']['has_condition']:
        print(f"2. CHECK CONDITION: {ability_data['condition']['conditions'][0]['text']}")
    if ability_data['cost_has_player_action']:
        print(f"3. PLAYER DECISION: {ability_data['cost_actions'][0]['type']}")
    if ability_data['cost']:
        print(f"4. EXECUTE COST: {ability_data['cost']}")
    if ability_data['effect_has_player_action']:
        print(f"5. PLAYER DECISION: {ability_data['effect_actions'][0]['type']}")
    print(f"6. EXECUTE EFFECT: {ability_data['automatic_effect']}")

def main():
    """Main function to test ability splitting."""
    print("Loading abilities...")
    abilities = load_abilities()
    
    print(f"Total abilities: {len(abilities)}")
    
    # Test on first 10 abilities
    test_abilities = abilities[:10]
    
    print(f"\nTesting decomposition on {len(test_abilities)} abilities...\n")
    
    decomposed = []
    for i, ability in enumerate(test_abilities):
        decomp = decompose_ability(ability)
        decomposed.append(decomp)
        display_decomposition(decomp, i)
    
    # Write to file
    output_file = Path("ability_decomposition_test.txt")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("ABILITY DECOMPOSITION TEST\n")
        f.write("="*80 + "\n\n")
        
        for i, decomp in enumerate(decomposed):
            f.write(f"ABILITY #{i + 1}\n")
            f.write("="*80 + "\n")
            f.write(f"Full Text: {decomp['full_text']}\n\n")
            f.write(f"TRIGGER: {decomp['trigger']}\n")
            f.write(f"COST: {decomp['cost']}\n")
            f.write(f"COST PLAYER ACTION: {decomp['cost_has_player_action']}\n")
            f.write(f"EFFECT BODY: {decomp['effect_body']}\n")
            f.write(f"CONDITION: {decomp['condition']}\n")
            f.write(f"EFFECT PLAYER ACTION: {decomp['effect_has_player_action']}\n")
            f.write(f"AUTOMATIC EFFECT: {decomp['automatic_effect']}\n\n")
    
    print(f"\n{'='*80}")
    print(f"Decomposition test complete. Output written to {output_file}")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
