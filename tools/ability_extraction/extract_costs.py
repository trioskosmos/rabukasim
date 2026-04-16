import json
import re
from pathlib import Path

"""
Extract cost information from ability text.
This script reads: data/abilities_extracted_from_cards.json
This script writes: data/abilities_extracted_from_cards.json
"""

with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

with open('tools/ability_extraction/variable_config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

def parse_cost(text):
    """Parse cost from triggerless text using pattern-based loop approach."""
    if '：' not in text and ':' not in text:
        return None
    
    cost_text = text.split('：')[0] if '：' in text else text.split(':')[0]
    cost_text = cost_text.strip()
    
    if not cost_text:
        return None
    
    cost = {}
    
    # Define cost patterns with their required phrases (order-independent)
    cost_patterns = [
        {
            'name': 'energy',
            'required_phrases': [],
            'check': lambda t: '{icon_energy.png|E}' in t,
            'extract': lambda t: t.count('{icon_energy.png|E}'),
            'output_key': 'energy'
        },
        {
            'name': 'member_to_waitroom',
            'required_phrases': ['ステージから控え室に置'],
            'check': lambda t: any(p in t for p in ['ステージから控え室に置']),
            'extract': lambda t: {
                'target': 'this_member' if 'このメンバー' in t else 'member',
                'optional': '置いてもよい' in t or 'でもよい' in t,
                'count': int(re.search(r'メンバー(\d+)人', t).group(1)) if re.search(r'メンバー(\d+)人', t) else 1,
                'exclude_member': re.search(r'「(.+?)」以外', t).group(1) if re.search(r'「(.+?)」以外', t) else None,
                'group': re.search(r"『(.+?)』", t).group(1) if re.search(r"『(.+?)』", t) else None
            },
            'output_key': 'member_to_waitroom'
        },
        {
            'name': 'member_to_wait',
            'required_phrases': ['ウェイトにする', 'ウェイトにしてもよい'],
            'check': lambda t: any(p in t for p in ['ウェイトにする', 'ウェイトにしてもよい']),
            'extract': lambda t: {
                'target': 'member' if 'このメンバー以外' in t else ('this_member' if 'このメンバー' in t else 'member'),
                'optional': 'でもよい' in t,
                'count': int(re.search(r'メンバー(\d+)人', t).group(1)) if re.search(r'メンバー(\d+)人', t) else (int(re.search(r'(\d+)人まで', t).group(1)) if re.search(r'(\d+)人まで', t) else 1),
                'max': bool(re.search(r'(\d+)人まで', t)),
                'group': re.search(r"『(.+?)』", t).group(1) if re.search(r"『(.+?)』", t) else None,
                'exclude_member': True if 'このメンバー以外' in t else None
            },
            'output_key': 'member_to_wait'
        },
        {
            'name': 'reveal',
            'required_phrases': ['手札', '公開する', '公開してもよい', '公開し'],
            'check': lambda t: '手札' in t and any(p in t for p in ['公開する', '公開してもよい', '公開し']),
            'extract': lambda t: {
                'source': 'hand',
                'optional': 'でもよい' in t or '公開してもよい' in t,
                'card_type': 'member_card' if 'メンバーカード' in t else ('live_card' if 'ライブカード' in t else None),
                'group': re.search(r"『(.+?)』", t).group(1) if re.search(r"『(.+?)』", t) else None,
                'count': 'all' if 'すべて' in t else (int(re.search(r'(\d+)枚', t).group(1)) if re.search(r'(\d+)枚', t) else 'any')
            },
            'output_key': 'reveal'
        },
        {
            'name': 'energy_to_member',
            'required_phrases': ['エネルギー置き場', 'このメンバーの下に置く'],
            'check': lambda t: 'エネルギー置き場' in t and 'このメンバーの下に置く' in t,
            'extract': lambda t: {
                'count': int(re.search(r'(\d+)枚', t).group(1)) if re.search(r'(\d+)枚', t) else 1,
                'source': 'energy_zone',
                'target': 'this_member'
            },
            'output_key': 'energy_to_member'
        },
        {
            'name': 'energy_to_energy_deck',
            'required_phrases': ['エネルギーデッキ', '置く'],
            'check': lambda t: 'エネルギーデッキ' in t and '置く' in t,
            'extract': lambda t: {
                'count': int(re.search(r'(\d+)枚', t).group(1)) if re.search(r'(\d+)枚', t) else 1,
                'target': 'energy_deck'
            },
            'output_key': 'energy_to_energy_deck'
        },
        {
            'name': 'waitroom_to_deck_bottom',
            'required_phrases': ['控え室', 'デッキの一番下に置く', 'デッキの一番下に置いてもよい'],
            'check': lambda t: '控え室' in t and any(p in t for p in ['デッキの一番下に置く', 'デッキの一番下に置いてもよい']),
            'extract': lambda t: {
                'count': int(re.search(r'(\d+)枚', t).group(1)) if re.search(r'(\d+)枚', t) else 1,
                'card_type': 'member_card' if 'メンバーカード' in t else 'card',
                'optional': 'でもよい' in t or '置いてもよい' in t,
                'order': 'any' if '好きな順番' in t else None
            },
            'output_key': 'waitroom_to_deck_bottom'
        },
        {
            'name': 'hand_to_deck_bottom',
            'required_phrases': ['デッキの一番下に置く', 'デッキの一番下に置いてもよい'],
            'check': lambda t: '手札' in t and any(p in t for p in ['デッキの一番下に置く', 'デッキの一番下に置いてもよい']),
            'extract': lambda t: {
                'count': int(re.search(r'(\d+)枚', t).group(1)) if re.search(r'(\d+)枚', t) else 1,
                'card_type': 'member_card' if 'メンバーカード' in t else ('live_card' if 'ライブカード' in t else 'card'),
                'optional': 'でもよい' in t or '置いてもよい' in t,
                'source': 'hand'
            },
            'output_key': 'hand_to_deck_bottom'
        },
        {
            'name': 'discard_from_hand',
            'required_phrases': ['手札', '控え室に置く', '控え室に置いてもよい'],
            'check': lambda t: '手札' in t and any(p in t for p in ['控え室に置く', '控え室に置いてもよい']),
            'extract': lambda t: {
                'count': int(re.search(r'(\d+)枚', t).group(1)) if re.search(r'(\d+)枚', t) else 1,
                'optional': '置いてもよい' in t or 'でもよい' in t or '支払ってもよい' in t,
                'card_type': 'member_card' if 'メンバーカード' in t else ('live_card' if 'ライブカード' in t else None),
                'group': re.search(r"『(.+?)』", t).group(1) if re.search(r"『(.+?)』", t) else None
            },
            'output_key': 'discard_from_hand'
        },
        {
            'name': 'discard_from_deck',
            'required_phrases': ['デッキ', '控え室に置く'],
            'check': lambda t: 'デッキ' in t and '控え室に置く' in t,
            'extract': lambda t: {
                'count': int(re.search(r'(\d+)枚', t).group(1)) if re.search(r'(\d+)枚', t) else 1,
                'optional': 'でもよい' in t or '支払ってもよい' in t
            },
            'output_key': 'discard_from_deck'
        }
    ]
    
    # Loop through patterns and extract costs
    for pattern in cost_patterns:
        if pattern['check'](cost_text):
            extracted = pattern['extract'](cost_text)
            # Remove None values
            if isinstance(extracted, dict):
                extracted = {k: v for k, v in extracted.items() if v is not None}
                # Remove 'max' key if False
                if 'max' in extracted and not extracted['max']:
                    del extracted['max']
            cost[pattern['output_key']] = extracted
    
    # Extract position (center, left_side, right_side)
    if 'センター' in cost_text:
        cost['position'] = 'center'
    elif '左サイド' in cost_text:
        cost['position'] = 'left_side'
    elif '右サイド' in cost_text:
        cost['position'] = 'right_side'
    
    # If no structured cost found, return raw text
    return cost_text if not cost else cost

def parse_effect_backwards(text):
    """Parse text backwards to extract action and variables."""
    # Check for parenthetical notes BEFORE stripping period (period inside parentheses)
    if text == '(対戦相手のカードの効果でも発動する。)' or text == '（手札のこのカードもこの効果で控え室に置ける。）':
        return {'action': 'note', 'raw_text': text}
    
    # Remove the final period
    text = text.rstrip('。')
    
    result = {}
    
    # Check for "として扱う" (treated as) pattern - multiple groups
    if 'として扱う' in text:
        result['action'] = 'treat_as'
        # Extract groups
        group_matches = re.findall(r"『(.+?)』", text)
        if group_matches:
            result['groups'] = group_matches
        return result
    
    # Check for "アクティブにならない" (cannot become active) pattern
    if 'アクティブにならない' in text:
        result['action'] = 'cannot_become_active'
        return result
    
    # Check for "し" (and) compound actions - only if followed by comma
    if 'し、' in text:
        # Split on "し、" to get compound actions
        parts = text.split('し、')
        if len(parts) >= 2:
            result['actions'] = []
            for part in parts:
                part = part.strip('、').strip()
                if part:
                    action = parse_effect_backwards(part)
                    if action and 'raw_text' not in action:
                        result['actions'].append(action)
                    else:
                        # If parsing fails, include as raw_text
                        result['actions'].append({'raw_text': part})
            if len(result['actions']) > 1:
                return result
            else:
                # If parsing failed, treat as single action
                result = {}
    
    # Strip position requirement prefixes (these are activation requirements, not part of effect)
    position_prefixes = [
        '{{center.png|センター}}',
        '【左サイド】',
        '【右サイド】'
    ]
    for prefix in position_prefixes:
        if text.startswith(prefix):
            text = text.replace(prefix, '').strip()
            if not text:
                return {'position_requirement': prefix.replace('{{', '').replace('}}', '').replace('【', '').replace('】', '')}
            break
    
    # Check for source modifiers at the beginning (e.g., "自分のエネルギーデッキから")
    if '自分のエネルギーデッキから' in text:
        text = text.replace('自分のエネルギーデッキから', '').replace('、', '').strip()
        if not text:
            return {'source': 'energy_deck', 'raw_text': '自分のエネルギーデッキから'}
        else:
            result['source'] = 'energy_deck'
    
    if '自分の控え室から' in text:
        text = text.replace('自分の控え室から', '').replace('、', '').strip()
        if not text:
            return {'source': 'waitroom', 'raw_text': '自分の控え室から'}
        else:
            result['source'] = 'waitroom'
    elif 'エールにより公開された自分のカードの中から' in text:
        text = text.replace('エールにより公開された自分のカードの中から', '').replace('、', '').strip()
        if not text:
            return {'source': 'cheer_revealed', 'raw_text': 'エールにより公開された自分のカードの中から'}
        else:
            result['source'] = 'cheer_revealed'
    elif '自分の控え室にある' in text:
        text = text.replace('自分の控え室にある', '').replace('、', '').strip()
        if not text:
            return {'location': 'waitroom', 'raw_text': '自分の控え室にある'}
        else:
            result['location'] = 'waitroom'
    
    # Check for multi-target (e.g., "自分と相手はそれぞれ")
    if '自分と相手はそれぞれ' in text:
        result['target'] = 'both_players'
        result['multi_target'] = True
        text = text.replace('自分と相手はそれぞれ', '').strip()
        if not text:
            return result
    
    # Check for opponent target (e.g., "相手は")
    if text.startswith('相手は'):
        result['target'] = 'opponent'
        text = text.replace('相手は', '').strip()
        if not text:
            return result
    
    # Check for choice pattern (～か)
    if 'か' in text and 'エネルギーを' in text:
        result['choice'] = True
        result['options'] = ['member', 'energy']
        # Remove the choice clause and continue parsing
        text = re.sub(r'自分のステージにいるメンバー\d+人かエネルギーを\d+枚', '', text).strip()
        if not text:
            return result
    action_patterns = {
        '引く': 'draw_cards',
        '引き': 'draw_cards',  # Conjunctive form
        '手札に加える': 'add_to_hand',
        'アクティブにする': 'activate_energy',
        'アクティブに': 'activate_energy',  # Without "する"
        'アクティブにしてもよい': 'may_activate',
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
        'ポジションチェンジさせてもよい': 'may_position_change',
        '移動させてもよい': 'may_move',
        '聞く': 'ask',
        '少なくなる': 'reduce_heart_cost',
        '多くなる': 'increase_heart_cost',
        'バトンタッチしてもよい': 'may_baton_touch',
        'ハートをすべて': 'transform_heart',
        '増やす': 'increase_heart_cost',  # For "必要ハートを...増やす"
        '(対戦相手のカードの効果でも発動する。)': 'note',
        '（手札のこのカードもこの効果で控え室に置ける。）': 'note'
    }
    
    result = {}
    
    # Check for duration modifiers (e.g., "ライブ終了時まで")
    duration_match = re.search(r'(ライブ終了時まで|ライブ終了時まで、)', text)
    if duration_match:
        result['duration'] = 'until_end_of_live'
        # Remove duration modifier and continue parsing
        text = text.replace(duration_match.group(1), '').strip()
        if not text:
            return result
    
    # Check for card play timing (e.g., "このカードのプレイに際し")
    timing_match = re.search(r'このカードのプレイに際し', text)
    if timing_match:
        result['timing'] = 'during_card_play'
        # Remove timing modifier and continue parsing
        text = text.replace(timing_match.group(0), '').strip()
        if not text:
            return result
    
    # Check for position modifiers (e.g., "【左サイド】")
    position_match = re.search(r'【(左サイド|右サイド)】', text)
    if position_match:
        position_map = {'左サイド': 'left_side', '右サイド': 'right_side'}
        result['position'] = position_map.get(position_match.group(1))
        # Remove position modifier and continue parsing
        text = text.replace(position_match.group(0), '').strip()
        if not text:
            return result
    
    # Check for center position + group condition (e.g., "{{center.png|センター}}自分のステージにいるすべての『Liella!』のメンバーと")
    if '{{center.png|センター}}' in text and 'のメンバーと' in text:
        result['position'] = 'center'
        # Extract group name
        group_match = re.search(r"『(.+?)』", text)
        if group_match:
            result['condition'] = {
                'type': 'group',
                'value': group_match.group(1),
                'operator': 'all'
            }
        # Remove the condition part and continue parsing
        text = re.sub(r'{{center\.png\|センター}}.*?のメンバーと、', '', text).strip()
        if not text:
            return result
    
    # Check for generic score patterns (+xする)
    score_match = re.search(r'\+(\d+)する', text)
    if score_match:
        # Check if this is actually cost modification, not score
        if 'コストを' in text or 'コスト' in text:
            result['action'] = 'modify_cost'
            result['amount'] = int(score_match.group(1))
        else:
            result['action'] = 'add_score'
            result['amount'] = int(score_match.group(1))
        return result
    
    # Check for score pattern without "する" (+N)
    score_match = re.search(r'\+(\d+)(?=し|、|$)', text)
    if score_match:
        result['action'] = 'add_score'
        result['amount'] = int(score_match.group(1))
        return result
    
    # Check for state setting patterns (e.g., "数は3つになる")
    state_match = re.search(r'数は(\d+)つになる', text)
    if state_match:
        result['action'] = 'set_count'
        result['value'] = int(state_match.group(1))
        return result
    
    # Check for "～は...になる" pattern (e.g., "必要ハートは...になる")
    if 'は' in text and 'になる' in text:
        result['action'] = 'set_state'
        # Extract the state name (before "は")
        before_ha = text.split('は')[0].strip()
        result['state_name'] = before_ha
        # Extract the value (after "は" and before "になる")
        after_ha = text.split('は')[1].split('になる')[0].strip()
        result['value'] = after_ha
        return result
    
    # Check for per-unit patterns (～につき) in simple effects
    if 'につき' in text:
        result['multiplier'] = True
        per_match = re.search(r'(\d+)枚につき', text)
        if per_match:
            result['per_unit'] = int(per_match.group(1))
        else:
            result['per_unit'] = 1
        
        # Extract unit type
        if 'エネルギーカード' in text:
            result['unit_type'] = 'energy_card'
        elif 'メンバー' in text:
            result['unit_type'] = 'member'
        elif 'カード' in text:
            result['unit_type'] = 'card'
        
        # Extract group if present
        group_match = re.search(r"『(.+?)』", text)
        if group_match:
            result['group'] = group_match.group(1)
        
        # Extract target
        if '相手の' in text:
            result['target'] = 'opponent'
        elif '自分の' in text:
            result['target'] = 'self'
        
        # Extract state
        if 'ウェイト状態の' in text:
            result['state'] = 'wait'
        elif 'アクティブ状態の' in text:
            result['state'] = 'active'
        
        # Remove the per-unit clause and continue parsing the action
        text = re.sub(r'.*?につき、', '', text).strip()
        if not text:
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
            variables = parse_effect_context_backwards(before_action)
            result.update(variables)
            break
    
    if not result:
        result['raw_text'] = text
    
    return result

def parse_effect_context_backwards(context):
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
    elif '自分のエネルギーデッキから' in context:
        variables['source'] = 'energy_deck'
    
    # Extract destination (e.g., "デッキの上に置く", "デッキの一番下に置く")
    if 'デッキの上に置く' in context or 'デッキの一番上に置く' in context:
        variables['destination'] = 'deck_top'
    elif 'デッキの下に置く' in context or 'デッキの一番下に置く' in context:
        variables['destination'] = 'deck_bottom'
    elif 'ステージに登場させる' in context:
        variables['destination'] = 'stage'
    elif '手札に加える' in context:
        variables['destination'] = 'hand'
    
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
        # Count each heart type separately
        heart_counts = {}
        for heart in heart_icons:
            heart_type = f'heart_{heart}'
            heart_counts[heart_type] = heart_counts.get(heart_type, 0) + 1
        
        # If only one heart type, simplify
        if len(heart_counts) == 1:
            heart_type = list(heart_counts.keys())[0]
            variables['resource'] = heart_type
            variables['resource_count'] = heart_counts[heart_type]
        else:
            variables['heart_resources'] = heart_counts
        
        variables['total_heart_count'] = len(heart_icons)
    
    # Extract blade icon count
    blade_icons = re.findall(r'{{icon_blade\.png\|ブレード}}', context)
    if blade_icons:
        variables['blade_count'] = len(blade_icons)
        if 'resource_count' not in variables:
            variables['resource'] = 'blade'
            variables['resource_count'] = len(blade_icons)
    
    return variables

def parse_conditional_effect(text):
    """Parse conditional effects (condition + action)."""
    result = {}
    
    # Check for source/location modifiers at the beginning
    if text.startswith('エールにより公開された自分のカードの中から'):
        result['source'] = 'cheer_revealed'
        text = text.replace('エールにより公開された自分のカードの中から', '').strip()
    elif text.startswith('自分のエネルギーデッキから'):
        result['source'] = 'energy_deck'
        text = text.replace('自分のエネルギーデッキから', '').strip()
    elif text.startswith('自分の控え室から'):
        result['source'] = 'waitroom'
        text = text.replace('自分の控え室から', '').strip()
    elif text.startswith('自分の控え室にある'):
        result['location'] = 'waitroom'
        text = text.replace('自分の控え室にある', '').strip()
    
    # Check for choice pattern
    if '自分のステージにいるメンバー1人か' in text:
        result['choice'] = True
        result['options'] = ['member', 'energy']
        text = text.replace('自分のステージにいるメンバー1人か', '').strip()
    
    # Split on condition markers
    condition_markers = ['なら', '場合', 'たび']
    for marker in condition_markers:
        if marker in text:
            parts = text.split(marker)
            if len(parts) == 2:
                condition_part = parts[0].strip()
                action_part = parts[1].strip()
                
                # Parse condition
                condition = parse_condition(condition_part)
                if condition:
                    result['condition'] = condition
                
                # Parse action
                action = parse_effect_backwards(action_part)
                if action:
                    result['action'] = action
                
                return result
    
    # If no condition marker found, treat as simple effect
    return parse_effect_backwards(text)

def parse_condition(condition_part):
    """Parse condition part of conditional effect."""
    condition = {}
    
    # Check for energy condition
    energy_match = re.search(r'エネルギーが(\d+)枚以上', condition_part)
    if energy_match:
        condition['type'] = 'energy'
        condition['value'] = int(energy_match.group(1))
        condition['operator'] = '>='
    
    # Check for surplus heart condition
    elif '余剰ハート' in condition_part:
        condition['type'] = 'surplus_heart'
        if '持たない' in condition_part:
            condition['value'] = 0
            condition['operator'] = '=='
        else:
            # Extract value if present
            value_match = re.search(r'余剰ハート.*?(\d+)つ以上', condition_part)
            if value_match:
                condition['value'] = int(value_match.group(1))
                condition['operator'] = '>='
            else:
                condition['value'] = 1
                condition['operator'] = '>='
        
        # Check for target (opponent vs self)
        if '相手の' in condition_part:
            condition['target'] = 'opponent'
        elif '自分の' in condition_part:
            condition['target'] = 'self'
    
    # Check for deck refresh condition
    elif 'デッキがリフレッシュしていた' in condition_part:
        condition['type'] = 'deck_refresh'
        condition['operator'] = 'true'
    
    # Check for all areas condition
    elif 'エリアすべてに' in condition_part:
        condition['type'] = 'all_areas'
        condition['operator'] = 'true'
    
    # Check for 'かぎり' (while/as long as) condition
    elif 'かぎり' in condition_part:
        condition['type'] = 'while'
        condition['operator'] = 'true'
    
    # Check for "登場か、エリアを移動したとき" (or condition)
    elif '登場か、エリアを移動したとき' in condition_part:
        condition['type'] = 'or_trigger'
        condition['operator'] = 'or'
        condition['triggers'] = ['deploy', 'move']
    
    # Check for "登場か、エリアを移動した" (or condition without marker)
    elif '登場か、エリアを移動した' in condition_part:
        condition['type'] = 'or_trigger'
        condition['operator'] = 'or'
        condition['triggers'] = ['deploy', 'move']
    
    # Check for "エリアを移動した" (area movement) condition
    elif 'エリアを移動した' in condition_part:
        condition['type'] = 'area_move'
        condition['operator'] = 'true'
    
    # Check for "効果によってはアクティブにならない" (cannot become active by effects) condition
    elif '効果によってはアクティブにならない' in condition_part:
        condition['type'] = 'cannot_become_active'
        condition['operator'] = 'true'
    
    # Check for "センターエリアにいるメンバーが最も大きいコストを持つ" (highest cost in center area) condition
    elif 'センターエリアにいるメンバーが最も大きいコストを持つ' in condition_part:
        condition['type'] = 'highest_cost_center'
        condition['operator'] = 'true'
    
    # Check for card count condition
    elif '枚以上' in condition_part:
        count_match = re.search(r'(\d+)枚以上', condition_part)
        if count_match:
            condition['type'] = 'card_count'
            condition['value'] = int(count_match.group(1))
            condition['operator'] = '>='
            
            # Extract location
            if 'ライブカード置き場' in condition_part:
                condition['location'] = 'live_card_zone'
            elif '成功ライブカード置き場' in condition_part:
                condition['location'] = 'success_live_card_zone'
            elif '控え室' in condition_part:
                condition['location'] = 'waitroom'
            elif 'エールにより公開された自分のカードの中' in condition_part:
                condition['location'] = 'cheer_revealed'
            elif 'エネルギー' in condition_part:
                condition['location'] = 'energy'
            elif '手札' in condition_part:
                condition['location'] = 'hand'
            elif 'ライブ中の' in condition_part or 'ライブカード' in condition_part:
                condition['location'] = 'live'
            
            # Extract card type if specified
            if 'ブレードを持つカード' in condition_part:
                condition['card_type'] = 'blade_card'
            elif 'ライブカード' in condition_part:
                condition['card_type'] = 'live_card'
            elif 'メンバーカード' in condition_part:
                condition['card_type'] = 'member_card'
            elif 'エネルギーカード' in condition_part:
                condition['card_type'] = 'energy_card'
    
    # Check for member count condition
    elif re.search(r'(\d+)人以上', condition_part):
        count_match = re.search(r'(\d+)人以上', condition_part)
        if count_match:
            condition['type'] = 'member_count'
            condition['value'] = int(count_match.group(1))
            condition['operator'] = '>='
            
            # Check for modifiers
            if '名前とコストが両方ともそれぞれ異なる' in condition_part:
                condition['different_name'] = True
                condition['different_cost'] = True
            elif '名前の異なる' in condition_part:
                condition['different_name'] = True
            elif 'コストの異なる' in condition_part:
                condition['different_cost'] = True
    
    # Check for per-unit modifier (～につき)
    elif 'につき' in condition_part:
        per_match = re.search(r'(\d+)枚につき', condition_part)
        if per_match:
            condition['type'] = 'per_unit'
            condition['value'] = int(per_match.group(1))
            condition['operator'] = '*'
        else:
            condition['type'] = 'per_unit'
            condition['value'] = 1
            condition['operator'] = '*'
        
        # Check for specific per-unit contexts
        if 'このメンバーの下にあるエネルギーカード' in condition_part:
            condition['unit_type'] = 'energy_under_member'
        elif 'これによりウェイト状態にしたメンバー' in condition_part:
            condition['unit_type'] = 'wait_by_this_effect'
        elif 'これにより支払った' in condition_part:
            condition['unit_type'] = 'energy_paid_by_this_effect'
        elif 'ステージにいる' in condition_part:
            condition['unit_type'] = 'stage_member'
        elif 'ライブカード置き場にある' in condition_part:
            condition['unit_type'] = 'live_card'
        elif '成功ライブカード置き場にある' in condition_part:
            condition['unit_type'] = 'success_live_card'
        
        # Check for target and state modifiers
        if '相手の' in condition_part:
            condition['target'] = 'opponent'
        elif '自分の' in condition_part:
            condition['target'] = 'self'
        
        if 'ウェイト状態の' in condition_part:
            condition['state'] = 'wait'
        elif 'アクティブ状態の' in condition_part:
            condition['state'] = 'active'
        
        # Extract group name if present
        group_match = re.search(r"『(.+?)』", condition_part)
        if group_match:
            condition['group'] = group_match.group(1)
        
        # Check for exclusion modifiers
        if 'このメンバー以外の' in condition_part:
            condition['exclusion'] = 'this_member'
        elif 'ほかの' in condition_part:
            condition['exclusion'] = 'other'
        elif '名前の異なる' in condition_part:
            condition['exclusion'] = 'different_name'
    
    # Check for opponent live card location modifier
    elif '相手のライブカード置き場にあるすべてのライブカードは' in condition_part:
        condition['type'] = 'opponent_live_cards_location'
        condition['operator'] = 'present'
    
    # Check for waitroom location modifier (自分の控え室にある)
    elif '自分の控え室にある' in condition_part:
        condition['type'] = 'waitroom_location'
        condition['operator'] = 'present'
    
    # Check for comparison condition (cost comparison)
    elif re.search(r'コストの大きい|コストが高い|コストが低い', condition_part):
        condition['type'] = 'comparison'
        condition['operator'] = '>'
    
    # Check for card count equal comparison
    elif 'カードの枚数が同じ' in condition_part or '枚数が同じ' in condition_part:
        condition['type'] = 'comparison'
        condition['operator'] = '=='
        condition['compares'] = 'card_count'
    
    # Check for exact number conditions (ちょうどX枚)
    elif 'ちょうど' in condition_part:
        exact_match = re.search(r'ちょうど(\d+)枚', condition_part)
        if exact_match:
            condition['type'] = 'exact_count'
            condition['value'] = int(exact_match.group(1))
            condition['operator'] = '=='
            # Extract what's being counted
            if 'エネルギー' in condition_part:
                condition['count_type'] = 'energy'
            elif 'カード' in condition_part:
                condition['count_type'] = 'card'
            elif 'ハート' in condition_part:
                condition['count_type'] = 'heart'
        return condition
    
    # Check for group condition
    elif '『' in condition_part and '』' in condition_part:
        group_match = re.search(r"『(.+?)』", condition_part)
        if group_match:
            condition['type'] = 'group'
            condition['value'] = group_match.group(1)
            condition['operator'] = 'present' 
    
    # Check for baton touch deployment condition
    elif 'バトンタッチして登場した' in condition_part:
        condition['type'] = 'baton_touch_deploy'
        condition['operator'] = 'true'
        
        # Extract source member detail
        if '能力を持たないメンバーから' in condition_part:
            condition['source_member'] = 'no_ability'
        
        # Extract character name from quotes
        char_match = re.search(r'「(.+?)」からバトンタッチ', condition_part)
        if char_match:
            condition['source_character'] = char_match.group(1)
        
        # Extract cost comparison if present
        cost_match = re.search(r'コストが(低い|高い)の', condition_part)
        if cost_match:
            condition['cost_comparison'] = cost_match.group(1)
        
        # Extract group if present
        group_match = re.search(r"『(.+?)』のメンバーから", condition_part)
        if group_match:
            condition['source_group'] = group_match.group(1)
    
    # Check for center + group condition (position + condition structure)
    elif '{{center.png|センター}}' in condition_part and 'のメンバーと' in condition_part:
        condition['type'] = 'group'
        condition['operator'] = 'all'
        # Extract group name
        group_match = re.search(r"『(.+?)』", condition_part)
        if group_match:
            condition['value'] = group_match.group(1)
        # Mark that position is required
        condition['position_required'] = 'center'
    
    # Check for position condition (ステージの左サイドエリアに登場しているなら)
    elif 'ステージの左サイドエリアに登場しているなら' in condition_part:
        condition['type'] = 'position'
        condition['value'] = 'left_side'
        condition['operator'] = '=='
    
    # Check for position condition
    elif '【左サイド】' in condition_part:
        condition['type'] = 'position'
        condition['value'] = 'left_side'
        condition['operator'] = '=='
    elif '【右サイド】' in condition_part:
        condition['type'] = 'position'
        condition['value'] = 'right_side'
        condition['operator'] = '=='
    elif '{{center.png|センター}}' in condition_part:
        condition['type'] = 'position'
        condition['value'] = 'center'
        condition['operator'] = '=='
    
    # Check for position markers at the beginning of text
    if condition_part.startswith('【左サイド】'):
        condition['type'] = 'position'
        condition['value'] = 'left_side'
        condition['operator'] = '=='
        return condition
    elif condition_part.startswith('【右サイド】'):
        condition['type'] = 'position'
        condition['value'] = 'right_side'
        condition['operator'] = '=='
        return condition
    
    # Check for character names in quotes (individual members)
    char_names = re.findall(r'「(.+?)」', condition_part)
    if char_names:
        condition['type'] = 'character_presence'
        condition['characters'] = char_names
        condition['operator'] = 'present' if 'いる' in condition_part or '登場' in condition_part else 'absent'
        if '自分のステージに' in condition_part:
            condition['target'] = 'self'
        elif '相手のステージに' in condition_part:
            condition['target'] = 'opponent'
        return condition
    
    # Check for member presence/absence conditions
    elif re.search(r'(自分|相手|自分と相手)のステージに.*?メンバーが(いる|いない)', condition_part):
        condition['type'] = 'member_presence'
        if 'いない' in condition_part:
            condition['presence'] = 'absent'
        else:
            condition['presence'] = 'present'
        if '相手の' in condition_part:
            condition['target'] = 'opponent'
        elif '自分と相手の' in condition_part:
            condition['target'] = 'both'
        else:
            condition['target'] = 'self'
        
        # Extract cost requirement
        cost_match = re.search(r'コスト(\d+)以上のメンバー', condition_part)
        if cost_match:
            condition['cost'] = int(cost_match.group(1))
        
        # Extract heart count requirement
        heart_match = re.search(r'heart\d+.*?(\d+)つ以上', condition_part)
        if heart_match:
            condition['heart_count'] = int(heart_match.group(1))
        
        # Extract exclusion details
        if 'このメンバー以外の' in condition_part:
            condition['exclusion'] = 'this_member'
        elif 'ほかの' in condition_part:
            condition['exclusion'] = 'other'
    
    # Check for card count conditions
    elif re.search(r'(カード|メンバーカード|ライブカード)が(\d+)枚以上', condition_part):
        count_match = re.search(r'(\d+)枚以上', condition_part)
        if count_match:
            condition['type'] = 'card_count'
            condition['value'] = int(count_match.group(1))
            condition['operator'] = '>='
    
    # Check for cost conditions
    elif re.search(r'コスト(\d+)以上のメンバー', condition_part):
        cost_match = re.search(r'コスト(\d+)以上', condition_part)
        if cost_match:
            condition['type'] = 'cost'
            condition['value'] = int(cost_match.group(1))
            condition['operator'] = '>='
    
    # Check for score sum conditions
    elif re.search(r'スコアの合計が(\d+)以上', condition_part):
        score_match = re.search(r'(\d+)以上', condition_part)
        if score_match:
            condition['type'] = 'score_sum'
            condition['value'] = int(score_match.group(1))
            condition['operator'] = '>='
            
            # Extract location
            if '成功ライブカード置き場にあるカード' in condition_part:
                condition['location'] = 'success_live_card_zone'
            elif 'ライブの合計スコア' in condition_part:
                condition['location'] = 'live_total'
    
    # Check for hand card count conditions
    elif re.search(r'手札の枚数が', condition_part):
        condition['type'] = 'hand_card_count'
        if 'より多い' in condition_part:
            condition['operator'] = '>'
        elif 'より2枚以上多い' in condition_part:
            condition['operator'] = '>=+2'
    
    # Check for energy comparison conditions
    elif re.search(r'エネルギーが.*?より', condition_part):
        condition['type'] = 'energy_comparison'
        if '多い' in condition_part:
            condition['operator'] = '>'
        elif '低い' in condition_part:
            condition['operator'] = '<'
    
    # Check for position conditions
    elif re.search(r'ステージの.*?エリアに(いる|登場している)', condition_part):
        condition['type'] = 'position'
        if 'センターエリア' in condition_part:
            condition['value'] = 'center'
        elif '左サイドエリア' in condition_part:
            condition['value'] = 'left_side'
        elif '右サイドエリア' in condition_part:
            condition['value'] = 'right_side'
        condition['operator'] = '=='
    
    # Check for answer conditions
    elif '回答が' in condition_part:
        condition['type'] = 'answer'
        condition['operator'] = '=='
        
        # Extract answer values
        if 'か' in condition_part:
            # Split by 'か' to get multiple answers
            answers_text = condition_part.replace('回答が', '').replace('の場合', '').strip()
            answers = answers_text.split('か')
            # Strip trailing particles from each answer
            condition['answers'] = [a.rstrip('の').strip() for a in answers]
        else:
            # Single answer - extract the word between "回答が" and "の場合"
            # Remove "回答が" prefix and "の場合" suffix
            answer_text = condition_part.replace('回答が', '').replace('の場合', '').strip()
            if answer_text:
                # Strip trailing particles
                condition['answers'] = [answer_text.rstrip('の').strip()]
    
    # Check for trigger condition (ライブ成功時能力が解決するたび)
    elif '{{live_success.png|ライブ成功時}}能力が解決するたび' in condition_part:
        condition['type'] = 'live_success_trigger'
        condition['trigger_type'] = 'live_success'
        condition['operator'] = 'each_time'
    
    # Check for opponent live cards location condition
    elif '相手のライブカード置き場にあるすべてのライブカードは' in condition_part:
        condition['type'] = 'opponent_live_cards'
        condition['operator'] = 'present'
    
    # Check for move action target condition (自分のステージにいるメンバーを)
    elif '自分のステージにいるメンバーを' in condition_part and '移動' not in condition_part:
        condition['type'] = 'stage_members_target'
        condition['operator'] = 'present'
    
    # Check for blade count conditions
    elif re.search(r'ブレード.*?合計が(\d+)以上', condition_part):
        blade_match = re.search(r'(\d+)以上', condition_part)
        if blade_match:
            condition['type'] = 'blade_count'
            condition['value'] = int(blade_match.group(1))
            condition['operator'] = '>='
    
    # Check for heart count conditions
    elif re.search(r'ハート.*?(\d+)つ以上', condition_part):
        heart_match = re.search(r'(\d+)つ以上', condition_part)
        if heart_match:
            condition['type'] = 'heart_count'
            condition['value'] = int(heart_match.group(1))
            condition['operator'] = '>='
    
    # Check for state conditions
    elif 'アクティブ状態' in condition_part or 'ウェイト状態' in condition_part:
        condition['type'] = 'state'
        if 'アクティブ状態' in condition_part:
            condition['value'] = 'active'
        elif 'ウェイト状態' in condition_part:
            condition['value'] = 'wait'
        condition['operator'] = '=='
    
    # Check for card score conditions
    elif re.search(r'このカードのスコアが(\d+)', condition_part):
        score_match = re.search(r'(\d+)', condition_part)
        if score_match:
            condition['type'] = 'card_score'
            condition['value'] = int(score_match.group(1))
            condition['operator'] = '=='
    
    # Check for combined location conditions (自分と相手の～)
    elif '自分と相手の' in condition_part and '合計' in condition_part:
        condition['type'] = 'combined_location_count'
        condition['operator'] = '>='
        total_match = re.search(r'(\d+)枚以上', condition_part)
        if total_match:
            condition['value'] = int(total_match.group(1))
        
        # Extract location
        if '成功ライブカード置き場' in condition_part:
            condition['location'] = 'success_live_card_zone'
        elif 'ライブカード置き場' in condition_part:
            condition['location'] = 'live_card_zone'
    
    # Check for comparison conditions (～より～)
    elif 'より' in condition_part:
        condition['type'] = 'comparison'
        if '高い' in condition_part:
            condition['operator'] = '>'
        elif '低い' in condition_part or '少ない' in condition_part:
            condition['operator'] = '<'
        elif '多い' in condition_part:
            condition['operator'] = '>'
        
        # Extract what's being compared
        if 'メンバーのコストの合計' in condition_part:
            condition['compares'] = 'member_cost_total'
        elif 'ライブの合計スコア' in condition_part:
            condition['compares'] = 'live_total_score'
        elif 'カード枚数' in condition_part:
            condition['compares'] = 'card_count'
        elif 'ハートの総数' in condition_part:
            condition['compares'] = 'heart_total'
        elif 'エールにより公開された自分のカードの枚数が、エールにより公開された相手のカードの枚数' in condition_part:
            condition['compares'] = 'cheer_revealed_card_count'
        elif 'エールにより公開されている自分のライブカードの枚数が、エールにより公開されている相手のライブカードの枚数' in condition_part:
            condition['compares'] = 'cheer_revealed_live_card_count'
        elif 'スコア' in condition_part and '合計' in condition_part:
            condition['compares'] = 'score_sum'
        elif '手札の枚数' in condition_part:
            condition['compares'] = 'hand_card_count'
        elif 'エネルギー' in condition_part:
            condition['compares'] = 'energy_count'
        elif '元々持つ{{icon_blade.png|ブレード}}の数' in condition_part:
            condition['compares'] = 'original_blade_count'
        elif 'コスト' in condition_part:
            condition['compares'] = 'cost'
        elif 'ハートを持つ' in condition_part and 'より' in condition_part:
            condition['compares'] = 'member_heart_count'
        elif '枚数が' in condition_part and 'より' in condition_part:
            condition['compares'] = 'card_count_comparison'
        
        # Extract location if applicable
        if '成功ライブカード置き場' in condition_part:
            condition['location'] = 'success_live_card_zone'
        elif 'エールにより公開された' in condition_part:
            condition['location'] = 'cheer_revealed'
        elif 'ライブカード置き場' in condition_part:
            condition['location'] = 'live_card_zone'
    
    # Check for simple card presence condition (～カードがある)
    elif 'カードがある' in condition_part:
        condition['type'] = 'card_presence'
        condition['operator'] = 'present'
        
        # Extract location
        if '成功ライブカード置き場' in condition_part:
            condition['location'] = 'success_live_card_zone'
        elif 'ライブカード置き場' in condition_part:
            condition['location'] = 'live_card_zone'
    
    # Default: raw condition
    if not condition:
        condition['type'] = 'raw'
        condition['text'] = condition_part
    
    return condition

def parse_compound_effect(text):
    """Parse compound effect (two actions separated by comma)."""
    # Split on comma
    parts = text.split('、')
    if len(parts) != 2:
        return None
    
    result = {'actions': []}
    
    # Parse first part (may contain condition or source/location modifiers)
    first_part = parts[0].strip()
    second_part = parts[1].strip()
    
    # Check if first part is a condition (contains condition markers or is a condition prefix)
    condition_markers = ['なら', '場合', 'たび']
    condition_prefixes = [
        'ステージの左サイドエリアに登場しているなら',
        '相手のライブカード置き場にあるすべてのライブカードは',
        '自分のステージにいるすべての『Liella!』のメンバーと',
        '自分のステージにいるメンバーの{{live_success.png|ライブ成功時}}能力が解決するたび',
        '自分のステージにいるメンバーを'
    ]
    
    is_condition = any(marker in first_part for marker in condition_markers) or \
                   any(prefix in first_part for prefix in condition_prefixes)
    
    if is_condition:
        # Parse as conditional effect
        condition = parse_condition(first_part)
        if condition and condition.get('type') != 'raw':
            result['condition'] = condition
            # Parse action from second part
            action = parse_effect_backwards(second_part)
            if action:
                result['action'] = action
            return result
    
    # Check for source/location modifiers in first part
    if first_part.startswith('エールにより公開された自分のカードの中から'):
        source_info = {'source': 'cheer_revealed'}
        first_part = first_part.replace('エールにより公開された自分のカードの中から', '').strip()
        result['actions'].append(source_info)
    elif first_part.startswith('自分のエネルギーデッキから'):
        source_info = {'source': 'energy_deck'}
        first_part = first_part.replace('自分のエネルギーデッキから', '').strip()
        result['actions'].append(source_info)
    elif first_part.startswith('自分の控え室から'):
        source_info = {'source': 'waitroom'}
        first_part = first_part.replace('自分の控え室から', '').strip()
        result['actions'].append(source_info)
    elif first_part.startswith('自分の控え室にある'):
        source_info = {'location': 'waitroom'}
        first_part = first_part.replace('自分の控え室にある', '').strip()
        result['actions'].append(source_info)
    elif first_part.startswith('自分のステージにいるメンバー1人か'):
        choice_info = {'choice': True, 'options': ['member', 'energy']}
        first_part = first_part.replace('自分のステージにいるメンバー1人か', '').strip()
        result['actions'].append(choice_info)
    
    # Parse remaining first part if not empty
    if first_part:
        first_action = parse_effect_backwards(first_part)
        if first_action and 'raw_text' not in first_action:
            result['actions'].append(first_action)
        else:
            result['actions'].append({'raw_text': first_part})
    
    # Parse second part
    second_action = parse_effect_backwards(second_part)
    if second_action:
        result['actions'].append(second_action)
    else:
        result['actions'].append({'raw_text': second_part})
    
    return result

def parse_complex_effect(text):
    """Parse complex effect with multiple parts (e.g., one-period two-comma)."""
    result = {}
    
    # Strip use_limit prefixes
    text = re.sub(r'［ターン\d+回］', '', text).strip()
    
    # Strip time prefixes
    time_prefixes = ['このターン、']
    for prefix in time_prefixes:
        if text.startswith(prefix):
            result['time'] = 'this_turn'
            text = text.replace(prefix, '').strip()
    
    # Strip duration prefixes
    duration_prefixes = ['ライブ終了時まで、']
    for prefix in duration_prefixes:
        if text.startswith(prefix):
            result['duration'] = 'until_end_of_live'
            text = text.replace(prefix, '').strip()
    
    # Check for duration in middle (condition, duration, action structure)
    # This needs to be checked early before other pattern matching
    if '、' in text and 'ライブ終了時まで、' in text:
        parts = text.split('、')
        if len(parts) == 2:
            first_part = parts[0].strip()
            second_part = parts[1].rstrip('。').strip()
            if 'ライブ終了時まで、' in second_part:
                # This is condition + duration + action
                condition = parse_condition(first_part)
                if condition:
                    result['condition'] = condition
                result['duration'] = 'until_end_of_live'
                # Extract action after duration
                action_part = second_part.replace('ライブ終了時まで、', '').strip()
                action = parse_effect_backwards(action_part)
                if action and 'raw_text' not in action:
                    result['action'] = action
                else:
                    result['action'] = {'raw_text': action_part}
                return result
        elif len(parts) == 3:
            # Check if middle part is duration or contains duration
            if parts[1].strip() == 'ライブ終了時まで' or 'ライブ終了時まで、' in parts[1]:
                # This is condition + duration + action
                condition = parse_condition(parts[0].strip())
                if condition:
                    result['condition'] = condition
                result['duration'] = 'until_end_of_live'
                # Extract action from third part
                full_action = parts[2].rstrip('。').strip()
                action = parse_effect_backwards(full_action)
                if action and 'raw_text' not in action:
                    result['action'] = action
                else:
                    result['action'] = {'raw_text': full_action}
                return result
    
    # Check for or_trigger pattern (登場か、エリアを移動したとき)
    if '登場か、エリアを移動したとき' in text:
        parts = text.split('、')
        if len(parts) == 2:
            condition_part = parts[0].strip()
            action_part = parts[1].rstrip('。').strip()
            condition = parse_condition(condition_part)
            if condition:
                result['condition'] = condition
            action = parse_effect_backwards(action_part)
            if action and 'raw_text' not in action:
                result['action'] = action
            else:
                result['action'] = {'raw_text': action_part}
            return result
    
    # Check for multiple conditions (multiple "場合" or "とき")
    # Also check for pattern like "condition1, condition2, action"
    if text.count('場合') >= 2 or text.count('とき') >= 2:
        # This has multiple conditions - split and handle
        parts = text.split('、')
        if len(parts) >= 3:
            # Pattern: condition1, condition2, action
            condition1_part = parts[0].strip()
            condition2_part = parts[1].strip()
            action_part = parts[2].rstrip('。').strip()
            
            result['conditions'] = []
            cond1 = parse_condition(condition1_part)
            if cond1:
                result['conditions'].append(cond1)
            cond2 = parse_condition(condition2_part)
            if cond2:
                result['conditions'].append(cond2)
            
            action = parse_effect_backwards(action_part)
            if action and 'raw_text' not in action:
                result['action'] = action
            else:
                result['action'] = {'raw_text': action_part}
            
            return result
        else:
            # Try parse_conditional_effect
            return parse_conditional_effect(text)
    
    # Check for pattern with two conditions but only 2 commas: "condition1, condition2, action"
    # where condition1 doesn't have "場合" but ends with "あり" or similar
    parts = text.split('、')
    if len(parts) == 3:
        condition1_part = parts[0].strip()
        condition2_part = parts[1].strip()
        action_part = parts[2].rstrip('。').strip()
        
        # Check if second part has condition marker
        if any(marker in condition2_part for marker in ['場合', 'とき']):
            # This is likely condition1, condition2, action
            result['conditions'] = []
            cond1 = parse_condition(condition1_part)
            if cond1:
                result['conditions'].append(cond1)
            cond2 = parse_condition(condition2_part)
            if cond2:
                result['conditions'].append(cond2)
            
            action = parse_effect_backwards(action_part)
            if action and 'raw_text' not in action:
                result['action'] = action
            else:
                result['action'] = {'raw_text': action_part}
            
            return result
    
    # Split on comma
    parts = text.split('、')
    if len(parts) != 2:
        return {'raw_text': text}
    
    first_part = parts[0].strip()
    second_part = parts[1].rstrip('。').strip()
    
    # Check if second part has duration in middle (condition, duration, action structure)
    if 'ライブ終了時まで、' in second_part:
        # This is condition + duration + action
        condition = parse_condition(first_part)
        if condition:
            result['condition'] = condition
        result['duration'] = 'until_end_of_live'
        # Extract action after duration
        action_part = second_part.replace('ライブ終了時まで、', '').strip()
        action = parse_effect_backwards(action_part)
        if action and 'raw_text' not in action:
            result['action'] = action
        else:
            result['action'] = {'raw_text': action_part}
        return result
    # Also check for duration at end of second part
    elif second_part.endswith('ライブ終了時まで'):
        condition = parse_condition(first_part)
        if condition:
            result['condition'] = condition
        result['duration'] = 'until_end_of_live'
        # Extract action before duration
        action_part = second_part.replace('ライブ終了時まで', '').strip()
        action = parse_effect_backwards(action_part)
        if action and 'raw_text' not in action:
            result['action'] = action
        else:
            result['action'] = {'raw_text': action_part}
        return result
    
    # Check if first part looks like a condition
    condition_markers = ['場合', 'かぎり', 'とき', '以上', '以下']
    is_condition = any(marker in first_part for marker in condition_markers)
    
    if is_condition:
        # This is condition + action structure
        condition = parse_condition(first_part)
        if condition and condition.get('type') != 'raw':
            result['condition'] = condition
        elif condition:
            # Include raw condition
            result['condition'] = condition
        
        # Parse the action (may contain nested structure)
        if '、' in second_part:
            # Nested structure in action - could be two actions
            sub_parts = second_part.split('、')
            # Check if this looks like two separate actions vs complex single action
            # Simple heuristic: if first sub_part ends with a verb, it's likely two actions
            action1 = parse_effect_backwards(sub_parts[0].strip())
            if action1 and 'raw_text' not in action1:
                result['actions'] = []
                result['actions'].append(action1)
                # Parse remaining parts
                remaining = '、'.join(sub_parts[1:]).rstrip('。').strip()
                action2 = parse_effect_backwards(remaining)
                if action2 and 'raw_text' not in action2:
                    result['actions'].append(action2)
                else:
                    result['actions'].append({'raw_text': remaining})
            else:
                # Treat as single complex action
                action = parse_effect_backwards(second_part)
                if action and 'raw_text' not in action:
                    result['action'] = action
                else:
                    result['action'] = {'raw_text': second_part}
        else:
            action = parse_effect_backwards(second_part)
            if action and 'raw_text' not in action:
                result['action'] = action
            else:
                result['action'] = {'raw_text': second_part}
    else:
        # This is action + action structure
        result['actions'] = []
        first_action = parse_effect_backwards(first_part)
        if first_action and 'raw_text' not in first_action:
            result['actions'].append(first_action)
        else:
            result['actions'].append({'raw_text': first_part})
        
        second_action = parse_effect_backwards(second_part)
        if second_action and 'raw_text' not in second_action:
            result['actions'].append(second_action)
        else:
            result['actions'].append({'raw_text': second_part})
    
    return result

def parse_generic_effect(text):
    """Parse generic effect when no specific pattern matches."""
    result = {}
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    # Check for OR pattern in card selection (e.g., "メンバーカードか、スコア２以下のライブカード")
    # Do this FIRST before any text modification to ensure full text is available
    if ('メンバーカードか' in text or 'ライブカードか' in text) and ('メンバーカード' in text and 'ライブカード' in text):
        result['choice'] = True
        result['options'] = ['member_card', 'live_card']
        # Extract score limit if present (for live_card option) - handle both half-width and full-width numbers
        score_match = re.search(r'スコア([\d０-９]+)以下', text)
        if score_match:
            # Convert full-width to half-width if needed
            score_str = score_match.group(1).translate(str.maketrans('０１２３４５６７８９', '0123456789'))
            result['score_limit'] = int(score_str)
        # Extract cost limit if present (for member_card option) - handle both half-width and full-width numbers
        cost_match = re.search(r'コスト([\d０-９]+)以下', text)
        if cost_match:
            # Convert full-width to half-width if needed
            cost_str = cost_match.group(1).translate(str.maketrans('０１２３４５６７８９', '0123456789'))
            result['cost_limit'] = int(cost_str)
        # Don't return yet, continue with other extractions
    
    # Check for position markers at the start of text
    if text.startswith('【左サイド】'):
        result['condition'] = {
            'type': 'position',
            'value': 'left_side',
            'operator': '=='
        }
        text = text.replace('【左サイド】', '').strip()
    elif text.startswith('【右サイド】'):
        result['condition'] = {
            'type': 'position',
            'value': 'right_side',
            'operator': '=='
        }
        text = text.replace('【右サイド】', '').strip()
    
    # Strip use_limit prefixes
    text = re.sub(r'［ターン\d+回］', '', text).strip()
    
    # Strip time prefixes
    time_prefixes = ['このターン、']
    for prefix in time_prefixes:
        if text.startswith(prefix):
            result['time'] = 'this_turn'
            text = text.replace(prefix, '').strip()
    
    # Strip duration prefixes
    duration_prefixes = ['ライブ終了時まで、']
    for prefix in duration_prefixes:
        if text.startswith(prefix):
            result['duration'] = 'until_end_of_live'
            text = text.replace(prefix, '').strip()
    
    # Check for negative actions (e.g., "アクティブにならない") before condition marker check
    if 'アクティブにならない' in text or 'ウェイトにならない' in text:
        action = parse_effect_backwards(text.rstrip('。'))
        if action and 'raw_text' not in action:
            result['action'] = action
        else:
            result['action'] = {'raw_text': text.rstrip('。')}
        return result
    
    # Look for condition markers in order of frequency
    condition_markers = ['場合', 'とき', 'かぎり', 'なら']
    for marker in condition_markers:
        if marker in text:
            # Split on the condition marker
            parts = text.split(marker)
            if len(parts) == 2:
                condition_part = parts[0].strip()
                action_part = parts[1].rstrip('。').strip()
                
                # Parse condition
                condition = parse_condition(condition_part)
                if condition:
                    result['condition'] = condition
                
                # Parse action (may have commas for compound actions)
                if '、' in action_part:
                    # Check if duration marker is in the action part
                    if 'ライブ終了時まで、' in action_part:
                        # This is condition + duration + action
                        result['duration'] = 'until_end_of_live'
                        action_part = action_part.replace('ライブ終了時まで、', '').strip('、')
                    
                    # Strip location modifiers
                    location_modifiers = ['自分のエネルギーデッキから', '相手のエネルギーデッキから', '自身のエネルギーデッキから']
                    for modifier in location_modifiers:
                        if modifier in action_part:
                            action_part = action_part.replace(modifier, '').strip('、')
                    
                    # Strip leading comma if present
                    action_part = action_part.lstrip('、')
                    
                    # Check if commas are separating list items vs separate actions
                    # Pattern 1: multiple items wrapped in 『』 with verb at end (e.g., "『A』、『B』、『C』として扱う")
                    # Pattern 2: 'か' (or) pattern in choices (e.g., "Aか、Bを得る")
                    # Pattern 3: 'し' (and) pattern in compound actions (e.g., "Aし、Bする")
                    # Pattern 4: '失い' (lose) pattern in compound actions (e.g., "Aを失い、Bする")
                    parts = action_part.split('、')
                    bracket_count = sum(1 for part in parts if '『' in part and '』' in part)
                    or_count = sum(1 for part in parts if 'か' in part and part.count('か') == 1)
                    and_count = sum(1 for part in parts if 'し' in part and part.count('し') == 1)
                    lose_count = sum(1 for part in parts if '失い' in part and part.count('失い') == 1)
                    
                    if (bracket_count >= 2 and ('として扱う' in parts[-1] or 'として' in parts[-1])) or or_count >= 1 or and_count >= 1 or lose_count >= 1:
                        # This is a list of groups/names, choices, or compound actions, not separate actions
                        action = parse_effect_backwards(action_part)
                        if action and 'raw_text' not in action:
                            result['action'] = action
                        else:
                            result['action'] = {'raw_text': action_part}
                    else:
                        # Treat as separate actions
                        # Strip leading/trailing commas
                        action_part = action_part.strip('、')
                        action_parts = action_part.split('、')
                        result['actions'] = []
                        for action_part_item in action_parts:
                            if action_part_item.strip():  # Skip empty parts
                                action = parse_effect_backwards(action_part_item.strip())
                                if action and 'raw_text' not in action:
                                    result['actions'].append(action)
                                else:
                                    result['actions'].append({'raw_text': action_part_item.strip()})
                else:
                    action = parse_effect_backwards(action_part)
                    if action and 'raw_text' not in action:
                        result['action'] = action
                    else:
                        result['action'] = {'raw_text': action_part}
                
                return result
    
    # No condition marker found - treat as simple action or compound action
    # Check for negative actions (e.g., "アクティブにならない") - treat as single action
    # This check needs to happen before comma-based checks
    if 'アクティブにならない' in text or 'ウェイトにならない' in text:
        action = parse_effect_backwards(text.rstrip('。'))
        if action and 'raw_text' not in action:
            result['action'] = action
        else:
            result['action'] = {'raw_text': text.rstrip('。')}
        return result
    
    # Check for cost reduction pattern (e.g., "コストは...少なくなる")
    if 'コストは' in text and '少なくなる' in text:
        action = parse_effect_backwards(text.rstrip('。'))
        if action and 'raw_text' not in action:
            result['action'] = action
        else:
            result['action'] = {'raw_text': text.rstrip('。')}
        return result
    
    # Check for action + duration + action pattern (no condition marker)
    if '、' in text and 'ライブ終了時まで、' in text:
        parts = text.split('、')
        if len(parts) == 2:
            # Check if first part is an action (not a condition)
            first_part = parts[0].strip()
            second_part = parts[1].rstrip('。').strip()
            if 'ライブ終了時まで、' in second_part:
                # This is action + duration + action
                result['duration'] = 'until_end_of_live'
                # Extract action after duration marker
                action_part = second_part.replace('ライブ終了時まで、', '').strip()
                result['actions'] = []
                action1 = parse_effect_backwards(first_part)
                if action1 and 'raw_text' not in action1:
                    result['actions'].append(action1)
                else:
                    result['actions'].append({'raw_text': first_part})
                action2 = parse_effect_backwards(action_part)
                if action2 and 'raw_text' not in action2:
                    result['actions'].append(action2)
                else:
                    result['actions'].append({'raw_text': action_part})
                return result
    
    # Check for compound action (multiple commas)
    if text.count('、') >= 2:
        # Check if commas are separating list items vs separate actions
        parts = text.rstrip('。').split('、')
        bracket_count = sum(1 for part in parts if '『' in part and '』' in part)
        or_count = sum(1 for part in parts if 'か' in part and part.count('か') == 1)
        and_count = sum(1 for part in parts if 'し' in part and part.count('し') == 1)
        lose_count = sum(1 for part in parts if '失い' in part and part.count('失い') == 1)
        
        if (bracket_count >= 2 and ('として扱う' in parts[-1] or 'として' in parts[-1])) or or_count >= 1 or and_count >= 1 or lose_count >= 1:
            # This is a list of groups/names, choices, or compound actions, not separate actions
            action = parse_effect_backwards(text.rstrip('。'))
            if action and 'raw_text' not in action:
                result['action'] = action
            else:
                result['action'] = {'raw_text': text.rstrip('。')}
        else:
            # Multiple actions
            action_parts = text.rstrip('。').split('、')
            result['actions'] = []
            for action_part in action_parts:
                action = parse_effect_backwards(action_part.strip())
                if action and 'raw_text' not in action:
                    result['actions'].append(action)
                else:
                    result['actions'].append({'raw_text': action_part.strip()})
        return result
    elif text.count('、') == 1:
        # Could be compound action or single action with comma
        parts = text.rstrip('。').split('、')
        action1 = parse_effect_backwards(parts[0].strip())
        action2 = parse_effect_backwards(parts[1].strip())
        
        if action1 and action2 and 'raw_text' not in action1 and 'raw_text' not in action2:
            result['actions'] = [action1, action2]
            return result
        else:
            # Treat as single complex action
            action = parse_effect_backwards(text.rstrip('。'))
            if action and 'raw_text' not in action:
                result['action'] = action
                return result
    
    # Simple action
    action = parse_effect_backwards(text.rstrip('。'))
    if action and 'raw_text' not in action:
        result['action'] = action
        return result
    
    # Fallback
    return {'raw_text': text}

for ab in data['unique_abilities']:
    ab['cost'] = parse_cost(ab['triggerless_text'])
    # Add costless field - true if no cost (null or no colon)
    ab['costless'] = ab['cost'] is None or (isinstance(ab['cost'], str) and ab['cost'] == ab['triggerless_text'])
    
    # Add use_limitless_text - ability text with use_limit removed
    use_limitless_text = ab['triggerless_text']
    if ab.get('use_limit'):
        # Remove use_limit pattern like {{turn1.png|ターン1回}}
        import re as re_module
        use_limitless_text = re_module.sub(r'\{\{[^}]+\}\s*', '', use_limitless_text)
    ab['use_limitless_text'] = use_limitless_text
    
    # Add costless_text - ability text with cost removed (after colon)
    costless_text = ab['triggerless_text']
    if '：' in costless_text:
        costless_text = costless_text.split('：')[1].strip()
    elif ':' in costless_text:
        costless_text = costless_text.split(':')[1].strip()
    ab['costless_text'] = costless_text
    
    # Add effect extraction - use generic condition marker detection
    if not costless_text:
        ab['effect'] = None
    else:
        ab['effect'] = parse_generic_effect(costless_text)

with open('data/abilities_extracted_from_cards.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
