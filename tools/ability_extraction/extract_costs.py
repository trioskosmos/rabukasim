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
    result = {}
    text = text.strip()
    
    # Check for ability gain pattern first: "「...」を得る"
    if '「' in text and '」を得る' in text:
        ability_match = re.search(r'「(.+?)」を得る', text)
        if ability_match:
            ability_text = ability_match.group(1).strip()
            result['action'] = {
                'action': 'gain_ability',
                'ability': ability_text
            }
            return result
    
    # Check for blade transformation pattern (e.g., "すべて[青ブレード]になる")
    if 'すべて' in text and 'になる' in text:
        blade_match = re.search(r'すべて\[([^\]]+)\]になる', text)
        if blade_match:
            target_blade = blade_match.group(1).strip()
            result['action'] = 'transform_blades'
            result['target_blade'] = target_blade
            return result
    
    # Check for "見る" (look at/reveal cards) pattern
    if re.search(r'カードを(\d+)枚見る', text):
        match = re.search(r'カードを(\d+)枚見る', text)
        if match:
            result['action'] = 'look_at_cards'
            result['count'] = int(match.group(1))
            result['source'] = 'deck_top'
            return result
    
    # Check for "ポジションチェンジさせる" (position change) pattern
    if 'ポジションチェンジさせる' in text:
        result['action'] = 'position_change'
        # Extract target if present
        if '自分のステージにいる' in text:
            result['target'] = 'self'
        elif '相手のステージにいる' in text:
            result['target'] = 'opponent'
        # Extract group if present
        group_match = re.search(r'『(.+?)』', text)
        if group_match:
            result['group'] = group_match.group(1)
        return result
    
    # Check for "公開して手札に加えてもよい" (reveal and add to hand, may) pattern
    if '公開して手札に加えてもよい' in text:
        # Extract the count and card type
        count_match = re.search(r'(\d+)枚', text)
        if count_match:
            result['action'] = 'add_to_hand'
            result['count'] = int(count_match.group(1))
            result['may'] = True
            result['reveal'] = True
            
            # Extract card type
            if 'メンバーカード' in text:
                result['card_type'] = 'member_card'
            elif 'ライブカード' in text:
                result['card_type'] = 'live_card'
            elif 'カード' in text:
                result['card_type'] = 'card'
            
            # Extract group if present
            group_match = re.search(r"『(.+?)』", text)
            if group_match:
                result['group'] = group_match.group(1)
            
            # Extract heart type selection if present (e.g., "{{heart_02.png|heart02}}か{{heart_04.png|heart04}}を持つ")
            if re.search(r'{{heart_\d+\.png.*?}}.*?を持つ', text):
                heart_matches = re.findall(r'{{heart_(\d+)\.png\|heart\d+}}', text)
                if heart_matches:
                    result['selection'] = {
                        'heart_types': heart_matches,
                        'operator': 'or'
                    }
            
            # Extract cost selection if present (e.g., "コスト9以上の") - only when "その中から" is present
            if 'その中から' in text and 'コスト' in text and '以上' in text:
                cost_match = re.search(r'コスト(\d+)以上', text)
                if cost_match:
                    if 'selection' not in result:
                        result['selection'] = {}
                    result['selection']['cost_min'] = int(cost_match.group(1))
            # Extract cost condition if present (only when NOT in "その中から" context)
            elif 'コスト' in text:
                if '以上' in text:
                    cost_match = re.search(r'コスト(\d+)以上', text)
                    if cost_match:
                        result['cost_min'] = int(cost_match.group(1))
                elif '以下' in text:
                    cost_match = re.search(r'コスト(\d+)以下', text)
                    if cost_match:
                        result['cost_limit'] = int(cost_match.group(1))
            
            return result
    
    # Check for parenthetical notes BEFORE stripping period (period inside parentheses)
    if text == '(対戦相手のカードの効果でも発動する。)' or text == '（手札のこのカードもこの効果で控え室に置ける。）':
        return {'action': 'note', 'raw_text': text}
    
    # Check for heart type choice selection pattern BEFORE period removal (e.g., "{{heart_01}}か{{heart_03}}か{{heart_06}}のうち、1つを選ぶ")
    if re.search(r'{{heart_\d+\.png.*?}}.*?のうち.*?1つを選ぶ', text):
        result = {}
        result['action'] = 'choose_heart'
        result['choice'] = True
        # Extract heart types
        heart_matches = re.findall(r'{{heart_(\d+)\.png\|heart\d+}}', text)
        if heart_matches:
            result['heart_types'] = heart_matches
            result['count'] = 1
        return result
    
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
            # Capture position requirement
            if prefix == '{{center.png|センター}}':
                result['position_requirement'] = 'center'
            elif prefix == '【左サイド】':
                result['position_requirement'] = 'left_side'
            elif prefix == '【右サイド】':
                result['position_requirement'] = 'right_side'
            text = text.replace(prefix, '').strip()
            break  # Always break after finding a position prefix
    
    # Check for source modifiers at the beginning (e.g., "自分のエネルギーデッキから")
    if '自分のエネルギーデッキから' in text:
        text = text.replace('自分のエネルギーデッキから', '').replace('、', '').strip()
        if not text:
            return {'source': 'energy_deck', 'raw_text': '自分のエネルギーデッキから'}
        else:
            result['source'] = 'energy_deck'
    
    if '自分の控え室から' in text:
        text = text.replace('自分の控え室から', '').replace('、', '').strip()
        # Check for heart count condition in source
        heart_count_match = re.search(r'必要ハートに.*?を(\d+)以上含む', text)
        if heart_count_match:
            result['heart_count'] = int(heart_count_match.group(1))
            # Remove the heart count condition from text
            text = re.sub(r'必要ハートに.*?を\d+以上含む', '', text).strip()
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
        # Check for heart count condition in source
        heart_count_match = re.search(r'必要ハートに.*?を(\d+)以上含む', text)
        if heart_count_match:
            result['heart_count'] = int(heart_count_match.group(1))
            # Remove the heart count condition from text
            text = re.sub(r'必要ハートに.*?を\d+以上含む', '', text).strip()
        if not text:
            return {'location': 'waitroom', 'raw_text': '自分の控え室にある'}
        else:
            result['source'] = 'waitroom'
    elif '自分のエネルギー置き場にある' in text:
        text = text.replace('自分のエネルギー置き場にある', '').replace('、', '').strip()
        if not text:
            return {'source': 'energy_zone', 'raw_text': '自分のエネルギー置き場にある'}
        else:
            result['source'] = 'energy_zone'
    
    # Check for heart count condition in source (e.g., "heart count >= 3")
    heart_count_match = re.search(r'ハート(\d+)以上', text)
    if heart_count_match:
        result['heart_count'] = int(heart_count_match.group(1))
    
    # Check for heart count condition with specific heart type (e.g., "必要ハートに{{heart_xx}}を3以上含む")
    heart_condition_match = re.search(r'必要ハートに.*?を(\d+)以上含む', text)
    if heart_condition_match:
        result['heart_count'] = int(heart_condition_match.group(1))
    
    # Check for score condition in source (e.g., "score <= 3")
    score_condition_match = re.search(r'スコア(\d+)以下', text)
    if score_condition_match:
        result['score_condition'] = {'operator': '<=', 'value': int(score_condition_match.group(1))}
    score_condition_match = re.search(r'スコア(\d+)以上', text)
    if score_condition_match:
        result['score_condition'] = {'operator': '>=', 'value': int(score_condition_match.group(1))}
    
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
        'アクティブにならない': 'cannot_activate',
        'ウェイトにする': 'member_to_wait',
        '控え室に置く': 'discard_to_waitroom',
        '登場させる': 'deploy_to_stage',
        '登場させてもよい': 'may_deploy_to_stage',
        '得る': 'gain_resource',
        '加算する': 'add_score',
        '置くことができない': 'cannot_place',
        '置けない': 'cannot_place',
        '置いてもよい': 'may_place_card',
        '置く': 'place_card',
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
        '見る': 'look_at_cards',  # For looking at cards from deck
        '(対戦相手のカードの効果でも発動する。)': 'note',
        '（手札のこのカードもこの効果で控え室に置ける。）': 'note'
    }
    
    result = {}
    
    # Check for "up_to" patterns (1人まで, 1枚まで)
    up_to_match = re.search(r'(\d+)人まで', text)
    if up_to_match:
        result['count'] = int(up_to_match.group(1))
        result['up_to'] = int(up_to_match.group(1))
    up_to_match = re.search(r'(\d+)枚まで', text)
    if up_to_match:
        result['count'] = int(up_to_match.group(1))
        result['up_to'] = int(up_to_match.group(1))
    
    # Check for explicit count patterns (1人, 1枚)
    count_match = re.search(r'(\d+)人を', text)
    if count_match:
        result['count'] = int(count_match.group(1))
    count_match = re.search(r'(\d+)枚を', text)
    if count_match:
        result['count'] = int(count_match.group(1))
    
    # Check for "all" modifier (すべて)
    if 'すべてのメンバー' in text:
        result['all'] = True
    
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
    
    # Check for blade count condition (e.g., "元々持つ{{icon_blade.png|ブレード}}の数が1つ以下")
    blade_condition_match = re.search(r'元々持つ.*?ブレード.*?の数が(\d+)以下', text)
    if blade_condition_match:
        result['condition'] = {
            'type': 'blade_count',
            'value': int(blade_condition_match.group(1)),
            'operator': '<='
        }
        # Remove the blade count condition from text
        text = re.sub(r'元々持つ.*?ブレード.*?の数が\d+以下', '', text).strip()
    
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
    
    # Extract person count with up_to (e.g., "1人を" implies up_to 1 in some contexts)
    person_match = re.search(r'(\d+)人を', context)
    if person_match:
        variables['count'] = int(person_match.group(1))
        # For opponent target actions, "1人を" often implies "up_to 1"
        if '相手' in context:
            variables['up_to'] = int(person_match.group(1))
    
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
    
    # Check for group names in brackets (e.g., "『Liella!』のメンバー")
    group_matches = re.findall(r"『(.+?)』", context)
    if group_matches:
        if len(group_matches) > 1:
            # Multiple groups - could be a choice pattern
            variables['groups'] = group_matches
            variables['group'] = group_matches[0]  # Also set first group for compatibility
        else:
            variables['group'] = group_matches[0]
    
    # Check for character names in quotes (e.g., "「上原歩夢」のメンバーカード")
    char_match = re.search(r'「(.+?)」', context)
    if char_match:
        variables['character'] = char_match.group(1)
    
    # Check for cost reduction pattern (e.g., "コストは1減る")
    cost_reduction_match = re.search(r'コストは(\d+)減る', context)
    if cost_reduction_match:
        variables['cost_reduction'] = int(cost_reduction_match.group(1))
    cost_reduction_match = re.search(r'コストは(\d+)少なくなる', context)
    if cost_reduction_match:
        variables['cost_reduction'] = int(cost_reduction_match.group(1))
    
    # Check for "として扱う" (treated as) pattern - multiple groups.
    if '能力を持たない' in context:
        variables['no_ability'] = True
    
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
        # Check if this is a blade count condition (e.g., "元々持つ{{icon_blade.png|ブレード}}の数が1つ以下")
        blade_condition_match = re.search(r'元々持つ.*?ブレード.*?の数が(\d+)以下', context)
        if blade_condition_match:
            variables['blade_count_condition'] = int(blade_condition_match.group(1))
            variables['blade_count_operator'] = '<='
        else:
            variables['blade_count'] = len(blade_icons)
            if 'resource_count' not in variables:
                variables['resource'] = 'blade'
                variables['resource_count'] = len(blade_icons)
    
    return variables

def parse_conditional_effect(text):
    """Parse conditional effect with condition marker."""
    result = {}
    text = text.strip()
    
    # Check for ability gain pattern: "「...」を得る" - do this FIRST before any other processing
    if '「' in text and '」を得る' in text:
        ability_match = re.search(r'「(.+?)」を得る', text)
        if ability_match:
            ability_text = ability_match.group(1).strip()
            # Extract the condition part before the ability gain
            condition_text = text[:ability_match.start()].rstrip('、').strip()
            # Check for "かつ" (and) pattern
            if 'かつ' in condition_text:
                parts = condition_text.split('かつ')
                result['conditions'] = []
                for part in parts:
                    cond = parse_condition(part.strip())
                    if cond:
                        result['conditions'].append(cond)
            else:
                condition = parse_condition(condition_text)
                if condition:
                    result['condition'] = condition
            result['action'] = 'gain_ability'
            result['ability'] = ability_text
            return result
    
    # Check for "この能力は" pattern (e.g., "この能力は、自分のライブ中、～")
    if 'この能力は' in text:
        before_ability, after_ability = text.split('この能力は', 1)
        after_ability = after_ability.strip()
        # Check for activation restriction in after_ability
        if 'のみ起動できる' in after_ability:
            result['activation_restriction'] = 'only_this_card'
        elif 'のみ発動する' in after_ability:
            result['activation_restriction'] = 'only_this_card'
        
        # Use the part before "この能力は" for further parsing
        text = before_ability
    
    # Check for heart type choice selection pattern BEFORE any processing (e.g., "{{heart_01}}か{{heart_03}}か{{heart_06}}のうち、1つを選ぶ")
    if re.search(r'{{heart_\d+\.png.*?}}.*?のうち.*?1つを選ぶ', text):
        result['action'] = 'choose_heart'
        result['choice'] = True
        # Extract heart types
        heart_matches = re.findall(r'{{heart_(\d+)\.png\|heart\d+}}', text)
        if heart_matches:
            result['heart_types'] = heart_matches
            result['count'] = 1
        # Extract duration if present
        if 'ライブ終了時まで' in text:
            result['duration'] = 'until_end_of_live'
        return result
    
    # Check for activation restriction patterns (e.g., "のみ起動できる", "のみ発動する")
    if 'のみ起動できる' in text:
        result['activation_restriction'] = 'only_this_card'
        text = text.replace('のみ起動できる', '').replace('）', '').strip()
    elif 'のみ発動する' in text:
        result['activation_restriction'] = 'only_this_card'
        text = text.replace('のみ発動する', '').replace('）', '').strip()
    
    # Check for position markers at the start of text
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
    
    # Check for ability gain pattern: "「...」を得る" - do this BEFORE condition marker split
    if '「' in text and '」を得る' in text:
        ability_match = re.search(r'「(.+?)」を得る', text)
        if ability_match:
            ability_text = ability_match.group(1).strip()
            # Extract the condition part before the ability gain
            condition_text = text[:ability_match.start()].rstrip('、').strip()
            # Check for "かつ" (and) pattern
            if 'かつ' in condition_text:
                parts = condition_text.split('かつ')
                result['conditions'] = []
                for part in parts:
                    cond = parse_condition(part.strip())
                    if cond:
                        result['conditions'].append(cond)
            else:
                condition = parse_condition(condition_text)
                if condition:
                    result['condition'] = condition
            result['action'] = 'gain_ability'
            result['ability'] = ability_text
            return result
    
    # Split on condition markers
    condition_markers = ['なら', '場合', 'たび']
    for marker in condition_markers:
        if marker in text:
            parts = text.split(marker)
            if len(parts) == 2:
                condition_part = parts[0].strip()
                action_part = parts[1].strip()
                
                # Check if action part contains only activation restriction (e.g., "のみ起動できる")
                if action_part in ['のみ起動できる', 'のみ発動する', 'のみ起動できる。', 'のみ発動する。）'] or action_part.replace('。', '').replace('）', '') in ['のみ起動できる', 'のみ発動する']:
                    # This is an activation restriction, add it to the condition
                    result['activation_restriction'] = 'only_this_card'
                    # Parse the condition part as the action (since it's actually the effect)
                    action = parse_effect_backwards(condition_part)
                    if action:
                        result['action'] = action
                    return result
                
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
    
    # Check for activation restriction at the end of condition (e.g., "のみ起動できる")
    if 'のみ起動できる' in condition_part:
        condition['activation_restriction'] = 'only_this_card'
        condition_part = condition_part.replace('のみ起動できる', '').strip()
    elif 'のみ発動する' in condition_part:
        condition['activation_restriction'] = 'only_this_card'
        condition_part = condition_part.replace('のみ発動する', '').strip()
    
    # Check for different card names condition (e.g., "カード名が異なる")
    if 'カード名が異なる' in condition_part:
        condition['different'] = 'card_name'
    
    # Check for different group names condition (e.g., "グループ名が異なる")
    if 'グループ名が異なる' in condition_part:
        condition['different'] = 'group_name'
    
    # Check for heart type selection with "のうち" (among) pattern (e.g., "{{heart_01}}か{{heart_03}}か{{heart_06}}のうち")
    if re.search(r'{{heart_\d+\.png.*?}}.*?のうち', condition_part):
        heart_matches = re.findall(r'{{heart_(\d+)\.png\|heart\d+}}', condition_part)
        if heart_matches:
            condition['heart_types'] = heart_matches
            condition['operator'] = 'or'
    
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
        # Extract group name if present
        group_match = re.search(r"『(.+?)』", condition_part)
        if group_match:
            condition['group'] = group_match.group(1)
        # Check for different names condition
        if '名前が異なる' in condition_part:
            condition['names_different'] = True
    
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
    elif condition_part.startswith('{{center.png|センター}}'):
        condition['type'] = 'position'
        condition['value'] = 'center'
        condition['operator'] = '=='
        condition['position_requirement'] = 'center'
        return condition
    
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
        condition['position_requirement'] = 'center'
    
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
    
    # Check for heart count condition (e.g., "必要ハートに{{heart_xx}}を3以上含む")
    heart_count_match = re.search(r'必要ハートに.*?を(\d+)以上含む', condition_part)
    if heart_count_match:
        condition['type'] = 'heart_count'
        condition['value'] = int(heart_count_match.group(1))
        condition['operator'] = '>='
        return condition
    
    # Check for blade count condition (e.g., "元々持つ{{icon_blade.png|ブレード}}の数が1つ以下")
    blade_count_match = re.search(r'元々持つ.*?ブレード.*?の数が(\d+)以下', condition_part)
    if blade_count_match:
        condition['type'] = 'blade_count'
        condition['value'] = int(blade_count_match.group(1))
        condition['operator'] = '<='
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
    if re.search(r'(カード|メンバーカード|ライブカード)が(\d+)枚以上', condition_part):
        count_match = re.search(r'(\d+)枚以上', condition_part)
        if count_match:
            condition['type'] = 'card_count'
            condition['value'] = int(count_match.group(1))
            condition['operator'] = '>='
        
        # Extract card type
        if 'ライブカード' in condition_part:
            condition['card_type'] = 'live_card'
        elif 'メンバーカード' in condition_part:
            condition['card_type'] = 'member_card'
        elif 'カード' in condition_part:
            condition['card_type'] = 'card'
        
        # Extract location
        if '控え室' in condition_part:
            condition['location'] = 'waitroom'
    
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
    
    # Check for score comparison conditions (e.g., "ライブの合計スコアが相手より高い場合")
    if 'スコア' in condition_part and '相手より' in condition_part:
        if '高い' in condition_part:
            condition['type'] = 'score_comparison'
            condition['operator'] = '>'
            condition['target'] = 'opponent'
        elif '低い' in condition_part:
            condition['type'] = 'score_comparison'
            condition['operator'] = '<'
            condition['target'] = 'opponent'
    
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
    
    # Check for ability gain pattern first: "「...」を得る"
    if '「' in text and '」を得る' in text:
        # Use a more flexible regex to match the ability text including icons
        ability_match = re.search(r'「(.+?)」を得る', text)
        if ability_match:
            ability_text = ability_match.group(1).strip()
            # Extract the condition part before the ability gain
            condition_text = text[:ability_match.start()].rstrip('、').strip()
            # Parse the condition
            if condition_text:
                # Check for "かつ" (and) pattern
                if 'かつ' in condition_text:
                    parts = condition_text.split('かつ')
                    result['conditions'] = []
                    for part in parts:
                        cond = parse_condition(part.strip())
                        if cond:
                            result['conditions'].append(cond)
                else:
                    condition = parse_condition(condition_text)
                    if condition:
                        result['condition'] = condition
            # Set action directly without extra wrapper
            result['action'] = 'gain_ability'
            result['ability'] = ability_text
            return result
    
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
    parts = split_commas_smartly(text)
    if len(parts) == 3:
        condition1_part = parts[0].strip()
        condition2_part = parts[1].strip()
        action_part = parts[2].rstrip('。').strip()
        
        # Check if second part has condition marker or "かつ" (and)
        if any(marker in condition2_part for marker in ['場合', 'とき', 'かつ']):
            # This is likely condition1, condition2, action
            result['conditions'] = []
            cond1 = parse_condition(condition1_part)
            if cond1:
                result['conditions'].append(cond1)
            cond2 = parse_condition(condition2_part)
            if cond2:
                result['conditions'].append(cond2)
            
            # Check for ability gain pattern "「...」を得る"
            if '「' in action_part and '」を得る' in action_part:
                ability_match = re.search(r'「(.+?)」を得る', action_part)
                if ability_match:
                    ability_text = ability_match.group(1).strip()
                    result['action'] = {
                        'action': 'gain_ability',
                        'ability': ability_text
                    }
                    return result
            
            action = parse_effect_backwards(action_part)
            if action and 'raw_text' not in action:
                result['action'] = action
            else:
                result['action'] = {'raw_text': action_part}
            
            return result
    
    # Split on comma
    parts = split_commas_smartly(text)
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
        # Check if action part has subject marker pattern ending with "は、"
        # If so, the subject marker should be preserved as part of the action
        # We need to handle this by removing the subject marker temporarily, parsing, then adding it back
        if re.search(r'は、', action_part) and not re.search(r'その後、', action_part):
            # Subject marker present and no sequence marker
            # Split on subject marker to get subject and actual action
            subject_match = re.search(r'(.+?)は、(.+)', action_part)
            if subject_match:
                subject = subject_match.group(1).strip()
                actual_action = subject_match.group(2).strip()
                # Parse the actual action (without subject marker)
                action = parse_effect_backwards(actual_action)
                if action and 'raw_text' not in action:
                    # Add subject to the action
                    action['subject'] = subject
                    result['action'] = action
                else:
                    # parse_effect_backwards failed - construct action manually
                    result['action'] = {
                        'action': 'gain_resource',
                        'subject': subject,
                        'raw_text': actual_action
                    }
                return result  # Return early to prevent further processing
            else:
                # Fallback - couldn't extract subject
                action = parse_effect_backwards(action_part)
                if action and 'raw_text' not in action:
                    result['action'] = action
                else:
                    result['action'] = {'raw_text': action_part}
                return result  # Return early to prevent further processing
        else:
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
            # Merge position_requirement if present
            if 'position_requirement' in action:
                result['position_requirement'] = action['position_requirement']
                del action['position_requirement']
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
        
        # Check for subject marker "は、" in second_part - this should be preserved as part of the action
        if re.search(r'は、', second_part) and not re.search(r'その後、', second_part):
            # Subject marker present and no sequence marker - treat as single action with subject
            subject_match = re.search(r'(.+?)は、(.+)', second_part)
            if subject_match:
                subject = subject_match.group(1).strip()
                actual_action = subject_match.group(2).rstrip('。').strip()
                # Parse the actual action (without subject marker)
                action = parse_effect_backwards(actual_action)
                if action and 'raw_text' not in action:
                    # Add subject to the action
                    action['subject'] = subject
                    result['action'] = action
                else:
                    result['action'] = {'raw_text': second_part}
            else:
                # Fallback - couldn't extract subject, parse normally
                result['action'] = {'raw_text': second_part}
            return result
        
        # Parse the action (may contain nested structure)
        if '、' in second_part:
            # Check for sequence marker "その後、" - this should split into separate actions
            if 'その後、' in second_part:
                # Split on sequence marker
                sub_parts = second_part.split('その後、')
                result['actions'] = []
                # Parse first action (before "その後、")
                action1 = parse_effect_backwards(sub_parts[0].rstrip('。').strip())
                if action1 and 'raw_text' not in action1:
                    result['actions'].append(action1)
                else:
                    result['actions'].append({'raw_text': sub_parts[0].rstrip('。').strip()})
                # Parse second action (after "その後、")
                action2 = parse_effect_backwards(sub_parts[1].rstrip('。').strip())
                if action2 and 'raw_text' not in action2:
                    result['actions'].append(action2)
                else:
                    result['actions'].append({'raw_text': sub_parts[1].rstrip('。').strip()})
            else:
                # Nested structure in action - could be two actions
                sub_parts = split_commas_smartly(second_part)
                # Check if this looks like two separate actions vs complex single action
                # Simple heuristic: if first sub_part ends with a verb, it's likely two actions
                action1 = parse_effect_backwards(sub_parts[0].strip())
                if action1 and 'raw_text' not in action1:
                    # Merge position_requirement if present
                    if 'position_requirement' in action1:
                        result['position_requirement'] = action1['position_requirement']
                        del action1['position_requirement']
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
                        # Merge position_requirement if present
                        if 'position_requirement' in action:
                            result['position_requirement'] = action['position_requirement']
                            del action['position_requirement']
                        result['action'] = action
                    else:
                        result['action'] = {'raw_text': second_part}
        else:
            action = parse_effect_backwards(second_part)
            if action and 'raw_text' not in action:
                # Merge position_requirement if present
                if 'position_requirement' in action:
                    result['position_requirement'] = action['position_requirement']
                    del action['position_requirement']
                result['action'] = action
            else:
                result['action'] = {'raw_text': second_part}
    else:
        # This is action + action structure
        result['actions'] = []
        first_action = parse_effect_backwards(first_part)
        if first_action and 'raw_text' not in first_action:
            # Merge position_requirement if present
            if 'position_requirement' in first_action:
                result['position_requirement'] = first_action['position_requirement']
                del first_action['position_requirement']
            result['actions'].append(first_action)
        else:
            result['actions'].append({'raw_text': first_part})
        
        second_action = parse_effect_backwards(second_part)
        if second_action and 'raw_text' not in second_action:
            result['actions'].append(second_action)
        else:
            result['actions'].append({'raw_text': second_part})
    
    return result

def split_commas_smartly(text):
    """Split text by commas, but preserve structural commas.
    Structural commas (should NOT split):
    - Subject markers: "は、" (wa particle)
    - Duration prefixes: "ライブ終了時まで、" (until end of live)
    - Time markers: "時、" (when) in certain contexts
    - Condition markers: "場合、" (if)
    
    Action separators (should split):
    - Sequence markers: "その後、" (after that)
    - Verb connectors: "し、" (and then)
    """
    parts = []
    current = ""
    i = 0
    while i < len(text):
        if text[i] == '、':
            # Check if this is a structural comma
            # Look ahead to see what precedes this comma
            if i >= 1:
                prev_char = text[i-1]
                # Subject marker: "は、"
                if prev_char == 'は':
                    current += '、'
                    i += 1
                    continue
                # Duration prefix: "ライブ終了時まで、"
                if i >= 7 and text[i-7:i] == 'ライブ終了時まで':
                    current += '、'
                    i += 1
                    continue
                # Condition marker: "場合、"
                if i >= 2 and text[i-2:i] == '場合':
                    current += '、'
                    i += 1
                    continue
            # Action separator: "その後、"
            if i >= 3 and text[i-3:i] == 'その後':
                parts.append(current)
                current = ""
                i += 1
                continue
            # Default: split on this comma
            parts.append(current)
            current = ""
        else:
            current += text[i]
        i += 1
    if current:
        parts.append(current)
    return [p.strip() for p in parts if p.strip()]

def parse_generic_effect(text):
    """Parse generic effect when no specific pattern matches."""
    result = {}
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    # Check for activation restriction pattern (e.g., "自分のアクティブフェイズにアクティブにしない")
    if '自分のアクティブフェイズにアクティブにしない' in text:
        result['action'] = 'cannot_activate'
        result['phase'] = 'active_phase'
        result['target'] = 'this_member'
        text = text.replace('このメンバーは自分のアクティブフェイズにアクティブにしない。', '').strip()
        if not text:
            return result
    
    # Check for dynamic count pattern (e.g., "これにより置いた枚数分")
    if 'これにより置いた枚数分' in text:
        result['count'] = 'dynamic'
        result['count_reference'] = 'placed_cards'
        text = text.replace('これにより置いた枚数分', '').strip()
        if not text:
            return result
    
    # Check for cost reduction pattern (e.g., "コストは1減る")
    cost_reduction_match = re.search(r'コストは(\d+)減る', text)
    if cost_reduction_match:
        result['action'] = {
            'action': 'reduce_cost',
            'amount': int(cost_reduction_match.group(1))
        }
        return result
    
    # Check for duration-at-start pattern with subject marker: "duration, subject, action"
    if text.startswith('ライブ終了時まで、') and 'は、' in text:
        result['duration'] = 'until_end_of_live'
        # Remove duration prefix
        text_without_duration = text.replace('ライブ終了時まで、', '', 1).strip()
        # Extract subject and action
        subject_match = re.search(r'(.+?)は、(.+)', text_without_duration)
        if subject_match:
            subject = subject_match.group(1).strip()
            actual_action = subject_match.group(2).rstrip('。').strip()
            result['subject'] = subject
            action = parse_effect_backwards(actual_action)
            if action and 'raw_text' not in action:
                result['action'] = action
            else:
                result['action'] = {'raw_text': actual_action}
            return result
    
    # Check for blade transformation pattern (e.g., "すべて[青ブレード]になる")
    if 'すべて' in text and 'になる' in text:
        # Extract the target blade type
        blade_match = re.search(r'すべて\[([^\]]+)\]になる', text)
        if blade_match:
            target_blade = blade_match.group(1).strip()
            result['action'] = 'transform_blades'
            result['target_blade'] = target_blade
            return result
    
    if cost_reduction_match:
        result['cost_reduction'] = int(cost_reduction_match.group(1))
        # Remove cost reduction part and continue parsing
        text = text.replace(cost_reduction_match.group(0), '').strip()
        if not text:
            return result
    cost_reduction_match = re.search(r'コストは(\d+)少なくなる', text)
    if cost_reduction_match:
        result['cost_reduction'] = int(cost_reduction_match.group(1))
        # Remove cost reduction part and continue parsing
        text = text.replace(cost_reduction_match.group(0), '').strip()
        if not text:
            return result
    
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
    
    # Check for score limit condition (e.g., "スコア3以下")
    score_limit_match = re.search(r'スコア([\d０-９]+)以下', text)
    if score_limit_match:
        # Convert full-width to half-width if needed
        score_str = score_limit_match.group(1).translate(str.maketrans('０１２３４５６７８９', '0123456789'))
        result['score_limit'] = int(score_str)
        # Remove the score limit from text
        text = re.sub(r'スコア[\d０-９]+以下', '', text).strip()
    
    # Check for cost limit condition (e.g., "コスト4以下")
    cost_limit_match = re.search(r'コスト([\d０-９]+)以下', text)
    if cost_limit_match:
        # Convert full-width to half-width if needed
        cost_str = cost_limit_match.group(1).translate(str.maketrans('０１２３４５６７８９', '0123456789'))
        result['cost_limit'] = int(cost_str)
        # Remove the cost limit from text
        text = re.sub(r'コスト[\d０-９]+以下', '', text).strip()
    
    # Check for energy OR member choice pattern (e.g., "エネルギー1枚か『group』のメンバー1人")
    
    # Check for energy OR member choice pattern (e.g., "エネルギー1枚か『group』のメンバー1人")
    if 'エネルギー' in text and '枚か' in text and 'メンバー' in text:
        result['choice'] = True
        result['options'] = ['energy', 'member']
        # Extract energy count
        energy_match = re.search(r'エネルギー(\d+)枚', text)
        if energy_match:
            result['energy_count'] = int(energy_match.group(1))
        # Extract group if present
        group_match = re.search(r'『(.+?)』', text)
        if group_match:
            result['group'] = group_match.group(1)
        # Don't return yet, continue with other extractions
        member_count_match = re.search(r'メンバー(\d+)人', text)
        if member_count_match:
            result['member_count'] = int(member_count_match.group(1))
    
    # Check for source markers
    if '自分のエネルギー置き場にある' in text:
        result['source'] = 'energy_zone'
        text = text.replace('自分のエネルギー置き場にある', '').strip()
    if '自分の控え室にある' in text:
        result['source'] = 'waitroom'
        text = text.replace('自分の控え室にある', '').strip()
        # Check for heart count condition in source
        heart_count_match = re.search(r'必要ハートに.*?を(\d+)以上含む', text)
        if heart_count_match:
            result['heart_count'] = int(heart_count_match.group(1))
            # Remove the heart count condition from text
            text = re.sub(r'必要ハートに.*?を\d+以上含む', '', text).strip()
    if '自分の控え室から' in text:
        result['source'] = 'waitroom'
        text = text.replace('自分の控え室から', '').strip()
        # Check for heart count condition in source
        heart_count_match = re.search(r'必要ハートに.*?を(\d+)以上含む', text)
        if heart_count_match:
            result['heart_count'] = int(heart_count_match.group(1))
            # Remove the heart count condition from text
            text = re.sub(r'必要ハートに.*?を\d+以上含む', '', text).strip()
    
    # Check for blade count condition (e.g., "元々持つ{{icon_blade.png|ブレード}}の数が1つ以下")
    blade_condition_match = re.search(r'元々持つ.*?ブレード.*?の数が(\d+)以下', text)
    if blade_condition_match:
        result['condition'] = {
            'type': 'blade_count',
            'value': int(blade_condition_match.group(1)),
            'operator': '<='
        }
        # Remove the blade count condition from text
        text = re.sub(r'元々持つ.*?ブレード.*?の数が\d+以下', '', text).strip()
    
    # Check for score presence condition (e.g., "{{icon_score.png|スコア}}を持つ")
    if '{{icon_score.png|スコア}}を持つ' in text:
        result['condition'] = {
            'type': 'has_score',
            'operator': 'present'
        }
        # Remove the score presence condition from text
        text = text.replace('{{icon_score.png|スコア}}を持つ', '').strip()
    
    # Check for "other than this member" condition (e.g., "このメンバー以外")
    if 'このメンバー以外' in text:
        if 'condition' not in result:
            result['condition'] = {}
        result['condition']['exclude_this_member'] = True
        # Remove the condition from text
        text = text.replace('このメンバー以外', '').strip()
    
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
    elif text.startswith('{{center.png|センター}}'):
        result['condition'] = {
            'type': 'position',
            'value': 'center',
            'operator': '=='
        }
        text = text.replace('{{center.png|センター}}', '').strip()
    
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
    # Check for parenthetical notes - strip them
    if '(' in text and ')' in text:
        # Keep the main action, strip parenthetical
        text = re.sub(r'\([^)]+\)', '', text).strip()
    
    # Check for bullet point choice pattern with conditions BEFORE "以下から1つを選ぶ"
    # This should happen before condition marker check
    if '以下から1つを選ぶ' in text and '・' in text:
        # Check if there's a condition before the choice marker
        condition_markers = ['場合', 'とき', 'かぎり', 'なら']
        has_condition = False
        for marker in condition_markers:
            if marker in text and text.index(marker) < text.index('以下から1つを選ぶ'):
                # Split on condition marker
                parts = text.split(marker)
                if len(parts) == 2:
                    condition_part = parts[0].strip()
                    choice_part = parts[1].strip()
                    # Parse condition
                    condition = parse_condition(condition_part)
                    if condition:
                        result['condition'] = condition
                    # Parse choice pattern
                    result['choice'] = True
                    result['actions'] = []
                    # Strip the choice marker from choice_part if present
                    choice_part = choice_part.replace('以下から1つを選ぶ。', '').replace('以下から1つを選ぶ', '').strip()
                    # Strip leading comma if present
                    choice_part = choice_part.lstrip('、').strip()
                    # Split by bullet points
                    bullet_options = choice_part.split('・')
                    for option in bullet_options:
                        option = option.strip()
                        # Skip the choice marker itself (with or without period)
                        if option and option not in ['以下から1つを選ぶ', '以下から1つを選ぶ。']:
                            # Remove trailing period
                            option = option.rstrip('。')
                            # Handle parenthetical notes - strip them
                            if '(' in option and ')' in option:
                                # Keep the main action, strip parenthetical
                                option = re.sub(r'\([^)]+\)', '', option).strip()
                            # Check if this bullet option has its own condition BEFORE parsing
                            if '場合' in option or 'とき' in option:
                                # Split on condition marker
                                condition_markers = ['場合', 'とき']
                                for marker in condition_markers:
                                    if marker in option:
                                        parts = option.split(marker)
                                        if len(parts) == 2:
                                            condition_part = parts[0].strip()
                                            action_part = parts[1].strip()
                                            # Parse the action part only
                                            action = parse_effect_backwards(action_part)
                                            if action and 'raw_text' not in action:
                                                # Add condition to the action
                                                condition = parse_condition(condition_part)
                                                if condition:
                                                    action['condition'] = condition
                                                result['actions'].append(action)
                                            else:
                                                result['actions'].append({'raw_text': action_part})
                                            break
                                continue
                            action = parse_effect_backwards(option)
                            if action and 'raw_text' not in action:
                                # If the action has nested actions, flatten them
                                if 'actions' in action:
                                    result['actions'].extend(action['actions'])
                                else:
                                    result['actions'].append(action)
                            else:
                                result['actions'].append({'raw_text': option})
                    
                    # After parsing all actions, distribute condition with scope="action" to individual actions
                    if 'condition' in result and result['condition'].get('scope') == 'action':
                        action_condition = result['condition']
                        del action_condition['scope']  # Remove scope marker
                        del result['condition']  # Remove from top level
                        # Add condition to each individual action that doesn't already have one
                        for action in result['actions']:
                            if isinstance(action, dict) and 'condition' not in action and 'raw_text' not in action:
                                action['condition'] = action_condition.copy()
                    
                    return result
                has_condition = True
                break
        
        # If no condition before choice marker, handle simple bullet point choice
        if not has_condition:
            result['choice'] = True
            result['actions'] = []
            # Strip the choice marker and any conditional modifiers after it
            choice_text = text
            # Remove choice marker
            choice_text = choice_text.replace('以下から1つを選ぶ。', '').replace('以下から1つを選ぶ', '').strip()
            # Remove conditional modifiers like "自分の成功ライブカード置き場に『虹ヶ咲』のカードがある場合、代わりに1つ以上を選ぶ。"
            choice_text = re.sub(r'自分の成功ライブカード置き場に.*?場合、代わりに\d+つ以上を選ぶ。', '', choice_text).strip()
            # Split by bullet points
            bullet_options = choice_text.split('・')
            for option in bullet_options:
                option = option.strip()
                # Skip the choice marker itself (with or without period)
                if option and option not in ['以下から1つを選ぶ', '以下から1つを選ぶ。']:
                    # Remove trailing period
                    option = option.rstrip('。')
                    # Handle parenthetical notes - strip them
                    if '(' in option and ')' in option:
                        # Keep the main action, strip parenthetical
                        option = re.sub(r'\([^)]+\)', '', option).strip()
                    # Check if this bullet option has its own condition BEFORE parsing
                    if '場合' in option or 'とき' in option:
                        # Split on condition marker
                        condition_markers = ['場合', 'とき']
                        for marker in condition_markers:
                            if marker in option:
                                parts = option.split(marker)
                                if len(parts) == 2:
                                    condition_part = parts[0].strip()
                                    action_part = parts[1].strip()
                                    # Parse the action part only
                                    action = parse_effect_backwards(action_part)
                                    if action and 'raw_text' not in action:
                                        # Add condition to the action
                                        condition = parse_condition(condition_part)
                                        if condition:
                                            action['condition'] = condition
                                        result['actions'].append(action)
                                    else:
                                        result['actions'].append({'raw_text': action_part})
                                    break
                        continue
                    action = parse_effect_backwards(option)
                    if action and 'raw_text' not in action:
                        # If the action has nested actions, flatten them
                        if 'actions' in action:
                            result['actions'].extend(action['actions'])
                        else:
                            result['actions'].append(action)
                    else:
                        result['actions'].append({'raw_text': option})
            return result
    
    # Check for period-separated actions (multi-action with no commas)
    # This should happen before condition marker check
    if text.count('。') >= 2 and text.count('、') == 0:
        # Check for choice pattern "以下から1つを選ぶ" first
        if '以下から1つを選ぶ' in text:
            result['choice'] = True
            # Split by periods
            action_parts = text.rstrip('。').split('。')
            result['actions'] = []
            for action_part in action_parts:
                if action_part.strip():
                    # Skip the choice marker itself
                    if action_part.strip() == '以下から1つを選ぶ':
                        continue
                    # Handle bullet points if present
                    if action_part.strip().startswith('・'):
                        action_part = action_part.strip().lstrip('・')
                    action = parse_effect_backwards(action_part.strip())
                    if action and 'raw_text' not in action:
                        result['actions'].append(action)
                    else:
                        result['actions'].append({'raw_text': action_part.strip()})
            return result
        else:
            # Split by periods and parse each action
            action_parts = text.rstrip('。').split('。')
            result['actions'] = []
            for action_part in action_parts:
                if action_part.strip():
                    action = parse_effect_backwards(action_part.strip())
                    if action and 'raw_text' not in action:
                        result['actions'].append(action)
                    else:
                        result['actions'].append({'raw_text': action_part.strip()})
            return result
    
    # Check for negative actions (e.g., "アクティブにならない") before condition marker check
    if 'アクティブにならない' in text or 'ウェイトにならない' in text:
        action = parse_effect_backwards(text.rstrip('。'))
        if action and 'raw_text' not in action:
            result['action'] = action
        else:
            result['action'] = {'raw_text': text.rstrip('。')}
        return result
    
    # Check for "discard until condition" pattern (e.g., "手札の枚数が3枚になるまで手札を控え室に置き")
    if 'なるまで' in text and '控え室に置き' in text:
        # Check if there's a sequence marker after the discard
        if 'その後、' in text:
            # Split on sequence marker
            parts = text.split('その後、')
            discard_part = parts[0].strip()
            after_part = parts[1].strip()
            result['actions'] = []
            # Parse discard part
            until_match = re.search(r'(.+?)なるまで', discard_part)
            if until_match:
                condition_text = until_match.group(1).strip()
                discard_action = {
                    'action': 'discard_to_waitroom',
                    'source': 'hand',
                    'until_condition': condition_text
                }
                count_match = re.search(r'(\d+)枚', condition_text)
                if count_match:
                    discard_action['until_count'] = int(count_match.group(1))
                if '自分と相手' in discard_part or 'それぞれ' in discard_part:
                    discard_action['target'] = 'both_players'
                result['actions'].append(discard_action)
            # Parse the action after "その後、"
            after_action = parse_effect_backwards(after_part.rstrip('。').strip())
            if after_action and 'raw_text' not in after_action:
                result['actions'].append(after_action)
            else:
                result['actions'].append({'raw_text': after_part.rstrip('。').strip()})
            return result
        else:
            # Extract the condition (before "なるまで")
            until_match = re.search(r'(.+?)なるまで', text)
            if until_match:
                condition_text = until_match.group(1).strip()
                # Extract the action (after "なるまで")
                action_text = text.replace(until_match.group(0), '').strip()
                # Parse the discard action
                result['action'] = {
                    'action': 'discard_to_waitroom',
                    'source': 'hand',
                    'until_condition': condition_text
                }
                # Try to extract target count from condition
                count_match = re.search(r'(\d+)枚', condition_text)
                if count_match:
                    result['until_count'] = int(count_match.group(1))
                # Check if it applies to both players
                if '自分と相手' in text or 'それぞれ' in text:
                    result['target'] = 'both_players'
                return result
    
    # Check for area rotation movement pattern (e.g., "センターエリアのメンバーを左サイドエリアに、左サイドエリアのメンバーを右サイドエリアに、右サイドエリアのメンバーをセンターエリアに、それぞれ移動させる")
    if 'センターエリアのメンバーを左サイドエリアに' in text and '左サイドエリアのメンバーを右サイドエリアに' in text and '右サイドエリアのメンバーをセンターエリアに' in text and 'それぞれ移動させる' in text:
        result['action'] = 'rotate_areas'
        result['rotation'] = {
            'center_to': 'left_side',
            'left_side_to': 'right_side',
            'right_side_to': 'center'
        }
        if '自分と対戦相手' in text:
            result['target'] = 'both_players'
        return result
    
    # Check for heart cost choice pattern (e.g., "必要ハートは、Aか、Bか、Cのうち、選んだ1つにしてもよい")
    if '必要ハートは、' in text and 'のうち、選んだ1つにしてもよい' in text:
        # Extract the heart cost options
        choice_match = re.search(r'必要ハートは、(.+?)のうち、選んだ1つにしてもよい', text)
        if choice_match:
            options_text = choice_match.group(1).strip()
            # Split by "か、" to get individual options
            options = [opt.strip() for opt in options_text.split('か、') if opt.strip()]
            result['action'] = 'choose_heart_cost'
            result['options'] = []
            for option in options:
                # Parse each heart cost option
                hearts = re.findall(r'\{\{heart_(\d+)\.png\|heart\d+\}\}', option)
                if hearts:
                    heart_cost = {'hearts': hearts}
                    result['options'].append(heart_cost)
            return result
    
    # Check for blade transformation pattern (e.g., "すべて[青ブレード]になる")
    if 'すべて' in text and 'になる' in text:
        # Extract the target blade type
        blade_match = re.search(r'すべて\[([^\]]+)\]になる', text)
        if blade_match:
            target_blade = blade_match.group(1).strip()
            result['action'] = 'transform_blades'
            result['target_blade'] = target_blade
            # Try to extract source blades from text if present
            source_blades = re.findall(r'\[([^\]]+)\]', text)
            if source_blades:
                # Remove the target blade from source blades list
                if target_blade in source_blades:
                    source_blades.remove(target_blade)
                if source_blades:
                    result['source_blades'] = source_blades
            return result
    
    # Check for blade transformation pattern with icon syntax (e.g., "すべて{{icon_b_blue.png|青ブレード}}になる")
    if 'すべて' in text and 'になる' in text and '{{icon_b_' in text:
        # Extract the target blade type from icon syntax
        blade_match = re.search(r'すべて\{\{icon_b_[^}]+\|([^\}]+)\}\}になる', text)
        if blade_match:
            target_blade = blade_match.group(1).strip()
            result['action'] = 'transform_blades'
            result['target_blade'] = target_blade
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
                        # Check for subject marker "は、" in the remaining action_part
                        if re.search(r'は、', action_part) and not re.search(r'その後、', action_part):
                            # Subject marker present - extract subject and action
                            subject_match = re.search(r'(.+?)は、(.+)', action_part)
                            if subject_match:
                                subject = subject_match.group(1).strip()
                                actual_action = subject_match.group(2).strip()
                                action_part = actual_action  # Use only the action part for parsing
                                result['subject'] = subject
                                # Check if the action is a blade transformation
                                if 'すべて' in actual_action and 'になる' in actual_action:
                                    blade_match = re.search(r'すべて\[([^\]]+)\]になる', actual_action)
                                    if blade_match:
                                        target_blade = blade_match.group(1).strip()
                                        result['action'] = {
                                            'action': 'transform_blades',
                                            'target_blade': target_blade
                                        }
                                        return result
                    
                    # Check for blade transformation pattern (e.g., "すべて[青ブレード]になる")
                    if 'すべて' in action_part and 'になる' in action_part:
                        blade_match = re.search(r'すべて\[([^\]]+)\]になる', action_part)
                        if blade_match:
                            target_blade = blade_match.group(1).strip()
                            result['action'] = {
                                'action': 'transform_blades',
                                'target_blade': target_blade
                            }
                            return result
                    
                    # Check for sequence marker "その後、" - this should split into separate actions
                    if 'その後、' in action_part:
                        # Split on sequence marker
                        sub_parts = action_part.split('その後、')
                        result['actions'] = []
                        # Parse first action (before "その後、")
                        first_part = sub_parts[0].rstrip('。').strip().lstrip('、')
                        action1 = parse_effect_backwards(first_part)
                        if action1 and 'raw_text' not in action1:
                            result['actions'].append(action1)
                        else:
                            result['actions'].append({'raw_text': first_part})
                        # Parse second action (after "その後、")
                        second_part = sub_parts[1].rstrip('。').strip()
                        action2 = parse_effect_backwards(second_part)
                        if action2 and 'raw_text' not in action2:
                            result['actions'].append(action2)
                        else:
                            result['actions'].append({'raw_text': second_part})
                        return result
                    
                    # Check for timing marker "相手のライブ開始時" (opponent's live start time)
                    if '相手のライブ開始時' in action_part:
                        result['timing'] = 'opponent_live_start'
                        # Remove timing marker
                        action_part = action_part.replace('相手のライブ開始時、', '').strip()
                        # Check for target specification "相手のライブカード置き場にあるライブカード1枚は"
                        if '相手のライブカード置き場にあるライブカード1枚は' in action_part:
                            result['target'] = 'opponent_live_card_zone'
                            result['target_count'] = 1
                            action_part = action_part.replace('相手のライブカード置き場にあるライブカード1枚は、', '').strip()
                        # Parse the remaining action
                        action = parse_effect_backwards(action_part)
                        if action and 'raw_text' not in action:
                            result['action'] = action
                        else:
                            result['action'] = {'raw_text': action_part}
                        return result
                    
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
            # Merge position_requirement if present
            if 'position_requirement' in action:
                result['position_requirement'] = action['position_requirement']
                del action['position_requirement']
            result['action'] = action
        else:
            result['action'] = {'raw_text': text.rstrip('。')}
        return result
    
    # Check for cost reduction pattern (e.g., "コストは...少なくなる")
    if 'コストは' in text and '少なくなる' in text:
        action = parse_effect_backwards(text.rstrip('。'))
        if action and 'raw_text' not in action:
            # Merge position_requirement if present
            if 'position_requirement' in action:
                result['position_requirement'] = action['position_requirement']
                del action['position_requirement']
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
        # Merge position_requirement if present
        if 'position_requirement' in action:
            result['position_requirement'] = action['position_requirement']
            del action['position_requirement']
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
