#!/usr/bin/env python3
"""
Extract effects from simple abilities (0 commas, 1 full stop) using backwards parsing.
Reads from: data/abilities_extracted_from_cards.json
Writes to: data/simple_effects_extracted.json
"""

import json
import re

with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Filter to simple abilities (0 commas, 1 full stop)
simple_abilities = []
for ab in data['unique_abilities']:
    costless_text = ab.get('costless_text', '')
    if costless_text and '、' not in costless_text and costless_text.count('。') == 1:
        simple_abilities.append(ab)

print(f"Found {len(simple_abilities)} simple abilities")

def parse_backwards(text):
    """Parse text backwards to extract action and variables."""
    # Check for parenthetical notes BEFORE stripping period (period inside parentheses)
    if text == '(対戦相手のカードの効果でも発動する。)' or text == '（手札のこのカードもこの効果で控え室に置ける。）':
        return {'action': 'note', 'raw_text': text}
    
    # Remove the final period
    text = text.rstrip('。')
    
    # Identify the main action verb (usually at or near the end)
    action_patterns = {
        '引く': 'draw_cards',
        '手札に加える': 'add_to_hand',
        'アクティブにする': 'activate_energy',
        'アクティブにしない': 'cannot_activate',
        'ウェイトにする': 'member_to_wait',
        '控え室に置く': 'discard_to_waitroom',
        '登場させる': 'deploy_to_stage',
        '登場させてもよい': 'may_deploy_to_stage',
        '得る': 'gain_resource',
        '加算する': 'add_score',
        '置く': 'place_card',
        '置いてもよい': 'may_place_card',
        '置けない': 'cannot_place',
        'できない': 'cannot',
        '減る': 'reduce',
        '減らす': 'reduce',
        '発動させる': 'activate_ability',
        'ポジションチェンジする': 'position_change',
        '聞く': 'ask',
        '(対戦相手のカードの効果でも発動する。)': 'note',
        '（手札のこのカードもこの効果で控え室に置ける。）': 'note'
    }
    
    result = {}
    
    # Check for generic score patterns (+xする)
    score_match = re.search(r'\+(\d+)する', text)
    if score_match:
        result['action'] = 'add_score'
        result['amount'] = int(score_match.group(1))
        return result
    
    # Check for parenthetical notes (text entirely wrapped in parentheses)
    # Handle both cases: period inside or outside parentheses
    if (text.startswith('(') and (text.endswith(')') or text.endswith(')。'))) or (text.startswith('（') and (text.endswith('）') or text.endswith('）。'))):
        result['action'] = 'note'
        result['raw_text'] = text
        return result
    
    # Check for baton touch restriction (more specific pattern)
    if 'バトンタッチで控え室に置けない' in text:
        result['action'] = 'cannot_baton_touch'
        return result
    
    # Find the action by checking from the end backwards
    for action, action_type in action_patterns.items():
        if action in text:
            result['action'] = action_type
            # Extract text before the action
            before_action = text.split(action)[0].strip()
            
            # Parse context backwards to extract variables
            variables = parse_context_backwards(before_action)
            result.update(variables)
            break
    
    if not result:
        result['raw_text'] = text
    
    return result

def parse_context_backwards(context):
    """Parse context backwards to extract variables."""
    variables = {}
    
    # Extract count (e.g., "1枚", "2枚")
    count_match = re.search(r'(\d+)枚', context)
    if count_match:
        variables['count'] = int(count_match.group(1))
    
    # Extract max (e.g., "1枚まで")
    max_match = re.search(r'(\d+)枚まで', context)
    if max_match:
        variables['up_to'] = int(max_match.group(1))
    
    # Extract source (e.g., "自分の控え室から", "デッキの上から")
    if '控え室' in context:
        variables['source'] = 'waitroom'
    elif 'デッキ' in context and '上' in context:
        variables['source'] = 'deck_top'
    elif 'デッキ' in context and '下' in context:
        variables['source'] = 'deck_bottom'
    elif '手札' in context:
        variables['source'] = 'hand'
    elif 'エネルギーデッキ' in context:
        variables['source'] = 'energy_deck'
    
    # Extract card type (e.g., "ライブカード", "メンバーカード")
    if 'ライブカード' in context:
        variables['card_type'] = 'live_card'
    elif 'メンバーカード' in context:
        variables['card_type'] = 'member_card'
    elif 'エネルギーカード' in context:
        variables['card_type'] = 'energy_card'
    
    # Extract group (e.g., "『虹ヶ咲』", "『Aqours』")
    group_match = re.search(r"『(.+?)』", context)
    if group_match:
        variables['group'] = group_match.group(1)
    
    # Extract cost limit (e.g., "コスト2以下" or "2コスト以下")
    cost_match = re.search(r"コスト(\d+)以下", context)
    if not cost_match:
        cost_match = re.search(r"(\d+)コスト以下", context)
    if cost_match:
        variables['cost_limit'] = int(cost_match.group(1))
    
    # Extract target (e.g., "相手の", "自分の")
    if '相手' in context:
        variables['target'] = 'opponent'
    elif '自分' in context:
        variables['target'] = 'self'
    
    # Extract position (left_side, right_side, center)
    if '【左サイド】' in context:
        variables['position'] = 'left_side'
    elif '【右サイド】' in context:
        variables['position'] = 'right_side'
    elif '{{center.png|センター}}' in context:
        variables['position'] = 'center'
    
    # Extract heart icon count and resource type
    heart_icons = re.findall(r'{{heart_(\d+)\.png\|heart\d+}}', context)
    if heart_icons:
        variables['resource_count'] = len(heart_icons)
        # Extract unique heart types
        unique_hearts = list(set(heart_icons))
        if len(unique_hearts) == 1:
            variables['resource'] = f'heart_{unique_hearts[0]}'
        else:
            variables['resource_types'] = [f'heart_{h}' for h in unique_hearts]
    
    return variables

# Extract effects from simple abilities
extracted = []
for ab in simple_abilities:
    costless_text = ab.get('costless_text', '')
    parsed = parse_backwards(costless_text)
    extracted.append({
        'costless_text': costless_text,
        'parsed': parsed,
        'triggers': ab.get('triggers'),
        'card_count': ab.get('card_count')
    })

# Write to file
with open('data/simple_effects_extracted.json', 'w', encoding='utf-8') as f:
    json.dump(extracted, f, ensure_ascii=False, indent=2)

print(f"Extracted effects from {len(extracted)} simple abilities")
print(f"Output written to data/simple_effects_extracted.json")
