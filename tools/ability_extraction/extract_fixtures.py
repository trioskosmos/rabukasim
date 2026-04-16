"""
Extract representative test cases from unique_abilities for fixture coverage.
This script extracts examples covering the most common cost/effect forms plus known edge cases.
"""
import json
from pathlib import Path

# Load abilities
with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Fixture categories to extract
fixtures = {
    'no_cost': [],
    'simple_energy_cost': [],
    'member_to_wait_cost': [],
    'reveal_cost': [],
    'simple_single_action': [],
    'compound_action_punctuation': [],
    'conditional_effect': [],
    'position_condition': [],
    'score_cost_limit_condition': [],
    'fallback_raw_text': []
}

# Extract examples for each category
for ab in data['unique_abilities']:
    triggerless = ab['triggerless_text']
    cost = ab.get('cost')
    effect = ab.get('effect')
    
    # No cost
    if cost is None:
        if len(fixtures['no_cost']) < 3:
            fixtures['no_cost'].append({
                'triggerless_text': triggerless,
                'cost': cost,
                'effect': effect,
                'card_count': ab['card_count']
            })
    
    # Simple energy cost
    elif cost and 'energy' in cost:
        if len(fixtures['simple_energy_cost']) < 3:
            fixtures['simple_energy_cost'].append({
                'triggerless_text': triggerless,
                'cost': cost,
                'effect': effect,
                'card_count': ab['card_count']
            })
    
    # Member-to-wait cost
    elif cost and 'member_to_waitroom' in cost:
        if len(fixtures['member_to_wait_cost']) < 3:
            fixtures['member_to_wait_cost'].append({
                'triggerless_text': triggerless,
                'cost': cost,
                'effect': effect,
                'card_count': ab['card_count']
            })
    
    # Reveal cost
    elif cost and 'reveal' in cost:
        if len(fixtures['reveal_cost']) < 3:
            fixtures['reveal_cost'].append({
                'triggerless_text': triggerless,
                'cost': cost,
                'effect': effect,
                'card_count': ab['card_count']
            })
    
    # Simple single action
    if effect and isinstance(effect, dict) and 'action' in effect and 'raw_text' not in effect:
        if len(fixtures['simple_single_action']) < 3:
            fixtures['simple_single_action'].append({
                'triggerless_text': triggerless,
                'cost': cost,
                'effect': effect,
                'card_count': ab['card_count']
            })
    
    # Compound action split by punctuation
    if effect and isinstance(effect, dict) and 'actions' in effect:
        if len(fixtures['compound_action_punctuation']) < 3:
            fixtures['compound_action_punctuation'].append({
                'triggerless_text': triggerless,
                'cost': cost,
                'effect': effect,
                'card_count': ab['card_count']
            })
    
    # Conditional effect
    if effect and isinstance(effect, dict) and 'condition' in effect:
        if len(fixtures['conditional_effect']) < 3:
            fixtures['conditional_effect'].append({
                'triggerless_text': triggerless,
                'cost': cost,
                'effect': effect,
                'card_count': ab['card_count']
            })
    
    # Position condition
    if effect and isinstance(effect, dict):
        effect_str = json.dumps(effect)
        if 'center' in effect_str or 'left_side' in effect_str or 'right_side' in effect_str:
            if len(fixtures['position_condition']) < 3:
                fixtures['position_condition'].append({
                    'triggerless_text': triggerless,
                    'cost': cost,
                    'effect': effect,
                    'card_count': ab['card_count']
                })
    
    # Score/cost-limit condition
    if effect and isinstance(effect, dict):
        effect_str = json.dumps(effect)
        if 'score' in effect_str or 'cost_min' in effect_str or 'cost_limit' in effect_str:
            if len(fixtures['score_cost_limit_condition']) < 3:
                fixtures['score_cost_limit_condition'].append({
                    'triggerless_text': triggerless,
                    'cost': cost,
                    'effect': effect,
                    'card_count': ab['card_count']
                })
    
    # Fallback raw text
    if effect and isinstance(effect, dict) and 'raw_text' in effect:
        if len(fixtures['fallback_raw_text']) < 3:
            fixtures['fallback_raw_text'].append({
                'triggerless_text': triggerless,
                'cost': cost,
                'effect': effect,
                'card_count': ab['card_count']
            })

# Write fixtures to JSON
with open('tools/ability_extraction/fixtures/extract_fixtures.json', 'w', encoding='utf-8') as f:
    json.dump(fixtures, f, ensure_ascii=False, indent=2)

print(f"Extracted fixtures:")
for category, examples in fixtures.items():
    print(f"  {category}: {len(examples)} examples")
