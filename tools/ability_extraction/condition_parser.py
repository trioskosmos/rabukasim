"""Condition parsing for ability extraction."""
import re

try:
    from .parser_utils import extract_all_quoted_names, extract_group_name, extract_heart_types, extract_int
except ImportError:
    from parser_utils import extract_all_quoted_names, extract_group_name, extract_heart_types, extract_int


def _extract_location(text):
    """Extract location from condition text."""
    if 'ライブカード置き場' in text:
        return 'live_card_zone'
    if '成功ライブカード置き場' in text:
        return 'success_live_card_zone'
    if '控え室' in text:
        return 'waitroom'
    if 'エールにより公開された自分のカードの中' in text:
        return 'cheer_revealed'
    if 'エネルギー' in text:
        return 'energy'
    if '手札' in text:
        return 'hand'
    if 'ライブ中の' in text or 'ライブカード' in text:
        return 'live'
    return None


def _extract_card_type(text):
    """Extract card type from condition text."""
    if 'ブレードを持つカード' in text:
        return 'blade_card'
    if 'ライブカード' in text:
        return 'live_card'
    if 'メンバーカード' in text:
        return 'member_card'
    if 'エネルギーカード' in text:
        return 'energy_card'
    return None


def _set_condition(condition, condition_type, *, value=None, operator=None, **extra):
    """Populate common condition fields and return the same dict."""
    condition['type'] = condition_type
    if value is not None:
        condition['value'] = value
    if operator is not None:
        condition['operator'] = operator
    condition.update({key: item for key, item in extra.items() if item is not None})
    return condition


def _extract_target(text):
    if '相手の' in text:
        return 'opponent'
    if '自分と相手の' in text:
        return 'both'
    if '自分の' in text:
        return 'self'
    return None


def _extract_position_value(text):
    if 'センターエリア' in text or '{{center.png|センター}}' in text:
        return 'center'
    if '左サイドエリア' in text or text.startswith('【左サイド】'):
        return 'left_side'
    if '右サイドエリア' in text or text.startswith('【右サイド】'):
        return 'right_side'
    return None


def _extract_location_subset(text):
    if '成功ライブカード置き場' in text:
        return 'success_live_card_zone'
    if 'エールにより公開された' in text:
        return 'cheer_revealed'
    if 'ライブカード置き場' in text:
        return 'live_card_zone'
    return None


def _extract_count_value(text, pattern):
    return extract_int(pattern, text)


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
        heart_matches = extract_heart_types(condition_part)
        if heart_matches:
            condition['heart_types'] = heart_matches
            condition['operator'] = 'or'
    
    # Check for energy condition
    energy_match = re.search(r'エネルギーが(\d+)枚以上', condition_part)
    if energy_match:
        _set_condition(condition, 'energy', value=int(energy_match.group(1)), operator='>=')
    
    # Check for surplus heart condition
    elif '余剰ハート' in condition_part:
        condition['type'] = 'surplus_heart'
        if '持たない' in condition_part:
            condition['value'] = 0
            condition['operator'] = '=='
        else:
            # Extract value if present
            condition['value'] = _extract_count_value(condition_part, r'余剰ハート.*?(\d+)つ以上') or 1
            condition['operator'] = '>='
        
        target = _extract_target(condition_part)
        if target in {'opponent', 'self'}:
            condition['target'] = target
    
    # Check for deck refresh condition
    elif 'デッキがリフレッシュしていた' in condition_part:
        condition['type'] = 'deck_refresh'
        condition['operator'] = 'true'
    
    # Check for all areas condition
    elif 'エリアすべてに' in condition_part:
        _set_condition(condition, 'all_areas', operator='true', group=extract_group_name(condition_part))
        # Check for different names condition
        if '名前が異なる' in condition_part:
            condition['names_different'] = True
    
    # Check for 'かぎり' (while/as long as) condition
    elif 'かぎり' in condition_part:
        condition['type'] = 'while'
        condition['operator'] = 'true'
    
    # Check for "登場か、エリアを移動したとき" (or condition)
    elif '登場か、エリアを移動したとき' in condition_part:
        _set_condition(condition, 'or_trigger', operator='or', triggers=['deploy', 'move'])
    
    # Check for "登場か、エリアを移動した" (or condition without marker)
    elif '登場か、エリアを移動した' in condition_part:
        _set_condition(condition, 'or_trigger', operator='or', triggers=['deploy', 'move'])
    
    # Check for "エリアを移動した" (area movement) condition
    elif 'エリアを移動した' in condition_part:
        _set_condition(condition, 'area_move', operator='true')
    
    # Check for "効果によってはアクティブにならない" (cannot become active by effects) condition
    elif '効果によってはアクティブにならない' in condition_part:
        _set_condition(condition, 'cannot_become_active', operator='true')
    
    # Check for "センターエリアにいるメンバーが最も大きいコストを持つ" (highest cost in center area) condition
    elif 'センターエリアにいるメンバーが最も大きいコストを持つ' in condition_part:
        _set_condition(condition, 'highest_cost_center', operator='true')
    
    # Check for card count condition
    elif '枚以上' in condition_part:
        count_value = _extract_count_value(condition_part, r'(\d+)枚以上')
        if count_value:
            _set_condition(
                condition,
                'card_count',
                value=count_value,
                operator='>=',
                location=_extract_location(condition_part),
                card_type=_extract_card_type(condition_part),
            )
    
    # Check for member count condition
    elif re.search(r'(\d+)人以上', condition_part):
        count_value = _extract_count_value(condition_part, r'(\d+)人以上')
        if count_value:
            _set_condition(condition, 'member_count', value=count_value, operator='>=')
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
        _set_condition(
            condition,
            'per_unit',
            value=_extract_count_value(condition_part, r'(\d+)枚につき') or 1,
            operator='*',
        )
        
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
        target = _extract_target(condition_part)
        if target in {'opponent', 'self'}:
            condition['target'] = target
        
        if 'ウェイト状態の' in condition_part:
            condition['state'] = 'wait'
        elif 'アクティブ状態の' in condition_part:
            condition['state'] = 'active'
        
        # Extract group name if present
        group = extract_group_name(condition_part)
        if group:
            condition['group'] = group
        
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
        _set_condition(condition, 'comparison', operator='==', compares='card_count')
    
    # Check for exact number conditions (ちょうどX枚)
    elif 'ちょうど' in condition_part:
        exact_count = _extract_count_value(condition_part, r'ちょうど(\d+)枚')
        if exact_count:
            _set_condition(condition, 'exact_count', value=exact_count, operator='==')
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
        group = extract_group_name(condition_part)
        if group:
            _set_condition(condition, 'group', value=group, operator='present')
    
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
        source_group = extract_group_name(condition_part)
        if source_group:
            condition['source_group'] = source_group
    
    # Check for position markers at the beginning of text
    if condition_part.startswith('【左サイド】'):
        _set_condition(condition, 'position', value='left_side', operator='==')
        return condition
    elif condition_part.startswith('【右サイド】'):
        _set_condition(condition, 'position', value='right_side', operator='==')
        return condition
    elif condition_part.startswith('{{center.png|センター}}'):
        _set_condition(condition, 'position', value='center', operator='==', position_requirement='center')
        return condition
    
    # Check for center + group condition (position + condition structure)
    elif '{{center.png|センター}}' in condition_part and 'のメンバーと' in condition_part:
        _set_condition(condition, 'group', value=extract_group_name(condition_part), operator='all')
        # Mark that position is required
        condition['position_required'] = 'center'
        condition['position_requirement'] = 'center'
    
    # Check for character names in quotes (individual members)
    char_names = extract_all_quoted_names(condition_part)
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
        _set_condition(condition, 'heart_count', value=int(heart_count_match.group(1)), operator='>=')
        return condition
    
    # Check for blade count condition (e.g., "元々持つ{{icon_blade.png|ブレード}}の数が1つ以下")
    blade_count_match = re.search(r'元々持つ.*?ブレード.*?の数が(\d+)以下', condition_part)
    if blade_count_match:
        _set_condition(condition, 'blade_count', value=int(blade_count_match.group(1)), operator='<=')
        return condition
    
    # Check for member presence/absence conditions
    elif re.search(r'(自分|相手|自分と相手)のステージに.*?メンバーが(いる|いない)', condition_part):
        condition['type'] = 'member_presence'
        if 'いない' in condition_part:
            condition['presence'] = 'absent'
        else:
            condition['presence'] = 'present'
        condition['target'] = _extract_target(condition_part) or 'self'
        
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
        count_value = _extract_count_value(condition_part, r'(\d+)枚以上')
        if count_value:
            _set_condition(condition, 'card_count', value=count_value, operator='>=')
        
        # Extract card type
        card_type = _extract_card_type(condition_part)
        if card_type:
            condition['card_type'] = card_type
        
        # Extract location
        if '控え室' in condition_part:
            condition['location'] = 'waitroom'
    
    # Check for cost conditions
    elif re.search(r'コスト(\d+)以上のメンバー', condition_part):
        cost_value = _extract_count_value(condition_part, r'コスト(\d+)以上')
        if cost_value:
            _set_condition(condition, 'cost', value=cost_value, operator='>=')
    
    # Check for score sum conditions
    elif re.search(r'スコアの合計が(\d+)以上', condition_part):
        score_value = _extract_count_value(condition_part, r'(\d+)以上')
        if score_value:
            _set_condition(
                condition,
                'score_sum',
                value=score_value,
                operator='>=',
                location='success_live_card_zone' if '成功ライブカード置き場にあるカード' in condition_part else ('live_total' if 'ライブの合計スコア' in condition_part else None),
            )
    
    # Check for score comparison conditions (e.g., "ライブの合計スコアが相手より高い場合")
    if 'スコア' in condition_part and '相手より' in condition_part:
        if '高い' in condition_part:
            _set_condition(condition, 'score_comparison', operator='>', target='opponent')
        elif '低い' in condition_part:
            _set_condition(condition, 'score_comparison', operator='<', target='opponent')
    
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
        _set_condition(condition, 'position', value=_extract_position_value(condition_part), operator='==')
    
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
        _set_condition(condition, 'live_success_trigger', operator='each_time', trigger_type='live_success')
    
    # Check for opponent live cards location condition
    elif '相手のライブカード置き場にあるすべてのライブカードは' in condition_part:
        _set_condition(condition, 'opponent_live_cards', operator='present')
    
    # Check for move action target condition (自分のステージにいるメンバーを)
    elif '自分のステージにいるメンバーを' in condition_part and '移動' not in condition_part:
        _set_condition(condition, 'stage_members_target', operator='present')
    
    # Check for blade count conditions
    elif re.search(r'ブレード.*?合計が(\d+)以上', condition_part):
        blade_value = _extract_count_value(condition_part, r'(\d+)以上')
        if blade_value:
            _set_condition(condition, 'blade_count', value=blade_value, operator='>=')
    
    # Check for heart count conditions
    elif re.search(r'ハート.*?(\d+)つ以上', condition_part):
        heart_value = _extract_count_value(condition_part, r'(\d+)つ以上')
        if heart_value:
            _set_condition(condition, 'heart_count', value=heart_value, operator='>=')
    
    # Check for state conditions
    elif 'アクティブ状態' in condition_part or 'ウェイト状態' in condition_part:
        _set_condition(condition, 'state', value='active' if 'アクティブ状態' in condition_part else 'wait', operator='==')
    
    # Check for card score conditions
    elif re.search(r'このカードのスコアが(\d+)', condition_part):
        score_value = _extract_count_value(condition_part, r'(\d+)')
        if score_value:
            _set_condition(condition, 'card_score', value=score_value, operator='==')
    
    # Check for combined location conditions (自分と相手の～)
    elif '自分と相手の' in condition_part and '合計' in condition_part:
        _set_condition(
            condition,
            'combined_location_count',
            value=_extract_count_value(condition_part, r'(\d+)枚以上'),
            operator='>=',
            location=_extract_location_subset(condition_part),
        )
    
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
        location = _extract_location_subset(condition_part)
        if location:
            condition['location'] = location
    
    # Check for simple card presence condition (～カードがある)
    elif 'カードがある' in condition_part:
        _set_condition(condition, 'card_presence', operator='present', location=_extract_location_subset(condition_part))
    
    # Default: raw condition
    if not condition:
        condition['type'] = 'raw'
        condition['text'] = condition_part
    
    return condition
