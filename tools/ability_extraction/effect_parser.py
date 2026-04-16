"""Effect parsing for ability extraction."""
import re

try:
    from .condition_parser import parse_condition
    from .parser_utils import (
        extract_all_groups,
        extract_blade_count,
        extract_cost,
        extract_count,
        extract_group_name,
        extract_heart_types,
        extract_int,
        extract_quoted_name,
        merge_position_requirement,
        normalize_fullwidth_digits,
        split_commas_smartly,
        strip_suffix_period,
    )
except ImportError:
    from condition_parser import parse_condition
    from parser_utils import (
        extract_all_groups,
        extract_blade_count,
        extract_cost,
        extract_count,
        extract_group_name,
        extract_heart_types,
        extract_int,
        extract_quoted_name,
        merge_position_requirement,
        normalize_fullwidth_digits,
        split_commas_smartly,
        strip_suffix_period,
    )


SOURCE_PATTERNS = [
    ('自分のエネルギーデッキから', 'energy_deck'),
    ('自分の控え室から', 'waitroom'),
    ('エールにより公開された自分のカードの中から', 'cheer_revealed'),
    ('自分の控え室にある', 'waitroom'),
    ('自分のエネルギー置き場にある', 'energy_zone'),
]

POSITION_PREFIXES = {
    '{{center.png|センター}}': 'center',
    '【左サイド】': 'left_side',
    '【右サイド】': 'right_side',
}


def _extract_source(text, result):
    """Extract source modifier from text and update result. Returns remaining text."""
    for pattern, source in SOURCE_PATTERNS:
        if pattern in text:
            text = text.replace(pattern, '').lstrip('、').strip()
            # Check for heart count condition
            heart_match = re.search(r'必要ハートに.*?を(\d+)以上含む', text)
            if heart_match:
                result['heart_count'] = int(heart_match.group(1))
                text = re.sub(r'必要ハートに.*?を\d+以上含む', '', text).strip()
            if not text:
                return None  # Signal that source was the only content
            result['source'] = source
            return text
    return text


def _extract_position_prefix(text, result):
    """Extract position prefix from text and update result. Returns remaining text."""
    for prefix, position in POSITION_PREFIXES.items():
        if text.startswith(prefix):
            result['position_requirement'] = position
            return text.replace(prefix, '').strip()
    return text


def _is_parsed_action(action):
    return bool(action and 'raw_text' not in action)


def _is_target_only_action(action):
    return isinstance(action, dict) and set(action.keys()) == {'target'}


def _is_duration_only_action(action):
    return isinstance(action, dict) and set(action.keys()) == {'duration'}


def _apply_target_only_action(action, target_action):
    if _is_target_only_action(action) and isinstance(target_action, dict) and 'target' not in target_action:
        target_action['target'] = action['target']
        return True
    return False


def _attach_player_choice(result, text):
    if not text.startswith('自分か相手を選ぶ'):
        return text
    result['choice'] = True
    result['options'] = ['self', 'opponent']
    return text.replace('自分か相手を選ぶ。', '', 1).replace('自分か相手を選ぶ', '', 1).strip()


def _extract_optional_payment(text):
    if '支払ってもよい' not in text and '支払った' not in text:
        return None, text

    prefix, suffix = (text.split('：', 1) + [''])[:2]
    if '支払ってもよい' not in prefix and '支払った' not in prefix:
        return None, text

    payment = {'optional': '支払ってもよい' in prefix}
    if 'icon_energy' in prefix or 'エネルギー' in prefix:
        payment['resource'] = 'energy'
    elif 'ブレード' in prefix:
        payment['resource'] = 'blade'
    amount = re.search(r'([\d０-９]+)(?:つ|枚)?(?:まで)?支払', prefix)
    if amount:
        payment['count'] = _normalized_int(amount.group(1))
    elif '1枚' in prefix or '1つ' in prefix or 'E' in prefix:
        payment['count'] = 1
    return payment, suffix.strip() if suffix else text


def _merge_subject_stub(parts):
    if len(parts) < 2:
        return parts
    first = parts[0].strip()
    if first and first.endswith('は') and '、' not in first and '。' not in first:
        parts = parts[1:]
        parts[0] = f'{first}、{parts[0].strip()}'
    return parts


def _raw_text(text):
    return {'raw_text': text}


def _note_action(text):
    return {'action': 'note', 'text': text}


def _select_member_action(text, *, target=None):
    result = {'action': 'select_member'}
    if target:
        result['target'] = target
    group = extract_group_name(text)
    if group:
        result['group'] = group
    char_name = extract_quoted_name(text)
    if char_name:
        result['character'] = char_name
    count_match = re.search(r'([\d０-９]+)人', text)
    if count_match:
        result['count'] = _normalized_int(count_match.group(1))
    if '以外' in text:
        result['exclude_this_member'] = True
    if '相手の' in text:
        result['target'] = 'opponent'
    elif '自分の' in text and target is None:
        result['target'] = 'self'
    return result


def _move_member_action(text):
    result = {'action': 'move_member'}
    if 'このメンバーがいたエリア' in text:
        result['source'] = 'origin_area'
    if 'そのエリア' in text:
        result['destination'] = 'chosen_area'
    if 'そのメンバー' in text:
        result['target'] = 'selected_member'
    elif 'このメンバー' in text:
        result['target'] = 'self'
    if 'そのメンバーは' in text and 'このメンバーがいたエリアに移動させる' in text:
        result['destination'] = 'chosen_area'
    return result


def _is_parenthetical_note(text):
    stripped = text.strip()
    if not stripped:
        return False
    if stripped.startswith(('(', '（')) and stripped.endswith((')', '）')):
        return True
    if stripped.endswith(('。）', '.)', ')')) and 'raw_text' not in stripped:
        return True
    return 'エールで公開する枚数を増やさない' in stripped or '対戦相手のカードの効果でも発動する' in stripped


def _parse_subject_action(text):
    subject_match = re.search(r'(.+?)は、(.+)', text)
    if not subject_match:
        return None, None
    return subject_match.group(1).strip(), strip_suffix_period(subject_match.group(2)).strip()


def _set_action_or_raw(result, text, *, key='action', merge_position=False):
    action = parse_effect_backwards(text)
    if _is_parsed_action(action):
        action = _normalize_action_shape(action)
        if merge_position:
            merge_position_requirement(result, action)
        result[key] = action
    else:
        result[key] = _raw_text(text)
    return result[key]


def _append_action_or_raw(actions, text):
    if not text:
        return None
    action = parse_effect_backwards(text)
    if _is_parsed_action(action):
        action = _normalize_action_shape(action)
    actions.append(action if _is_parsed_action(action) else _raw_text(text))
    return actions[-1]


def _prune_empty_raw_nodes(value):
    if isinstance(value, dict):
        keys_to_delete = []
        for key, item in value.items():
            if isinstance(item, dict) and item.get('raw_text') == '':
                keys_to_delete.append(key)
            else:
                _prune_empty_raw_nodes(item)
        for key in keys_to_delete:
            del value[key]
    elif isinstance(value, list):
        items_to_keep = []
        for item in value:
            if isinstance(item, dict) and item.get('raw_text') == '':
                continue
            _prune_empty_raw_nodes(item)
            items_to_keep.append(item)
        value[:] = items_to_keep
    return value


def _normalize_action_shape(action):
    if not isinstance(action, dict):
        return action
    nested = action.get('action')
    if isinstance(nested, dict) and 'actions' in nested:
        nested_action = action.pop('action')
        for key, value in nested_action.items():
            if key == 'actions' or key not in action:
                action[key] = value
    return action


def _normalized_int(value):
    return int(normalize_fullwidth_digits(value))


def _assign_condition(result, condition_text):
    condition = parse_condition(condition_text)
    if condition:
        result['condition'] = condition
    return condition


def _assign_conditions(result, condition_parts):
    conditions = []
    for condition_part in condition_parts:
        condition = parse_condition(condition_part.strip())
        if condition:
            conditions.append(condition)
    if conditions:
        result['conditions'] = conditions
    return conditions


def _assign_duration_action(result, condition_text, action_text, *, duration='until_end_of_live'):
    if condition_text:
        _assign_condition(result, condition_text)
    result['duration'] = duration
    _set_action_or_raw(result, strip_suffix_period(action_text).strip())
    return result


def _assign_subject_action(result, text, *, merge_position=False):
    subject, actual_action = _parse_subject_action(text)
    if not subject:
        result['action'] = _raw_text(text)
        return False

    action = parse_effect_backwards(actual_action)
    if _is_parsed_action(action):
        if merge_position:
            merge_position_requirement(result, action)
        action['subject'] = subject
        result['action'] = action
    else:
        result['action'] = _raw_text(text)
    return True


def _assign_sequence_actions(result, action_parts):
    result['actions'] = []
    for action_part in action_parts:
        _append_action_or_raw(result['actions'], strip_suffix_period(action_part).strip())
    return result['actions']


def _assign_ability_gain(result, ability_text):
    result['action'] = 'gain_ability'
    result['ability'] = ability_text
    return result


def _extract_limit(text, label):
    match = re.search(rf'{label}([\d０-９]+)以下', text)
    return _normalized_int(match.group(1)) if match else None


def _strip_waitroom_source(text, result):
    for marker in ['自分の控え室にある', '自分の控え室から', 'そのプレイヤーの控え室にある']:
        if marker in text:
            result['source'] = 'waitroom'
            if marker.startswith('そのプレイヤー'):
                result['target'] = 'selected_player'
            text = text.replace(marker, '').strip()
            heart_count = _extract_count_value_from_heart_requirement(text)
            if heart_count:
                result['heart_count'] = heart_count
                text = re.sub(r'必要ハートに.*?を\d+以上含む', '', text).strip()
    return text


def _extract_count_value_from_heart_requirement(text):
    match = re.search(r'必要ハートに.*?を(\d+)以上含む', text)
    return int(match.group(1)) if match else None


def _extract_ability_gain(text):
    ability_match = re.search(r'「(.+?)」を得る', text)
    if not ability_match:
        return None, None
    return ability_match.group(1).strip(), text[:ability_match.start()].rstrip('、').strip()


def _assign_prefixed_source(text, result):
    for prefix, payload in [
        ('エールにより公開された自分のカードの中から', {'source': 'cheer_revealed'}),
        ('自分のエネルギーデッキから', {'source': 'energy_deck'}),
        ('自分の控え室から', {'source': 'waitroom'}),
        ('自分の控え室にある', {'location': 'waitroom'}),
        ('そのプレイヤーの控え室にある', {'source': 'waitroom', 'target': 'selected_player'}),
    ]:
        if text.startswith(prefix):
            result.update(payload)
            return text.replace(prefix, '').strip()
    return text


def _looks_like_condition(text, markers=None, prefixes=None):
    markers = markers or []
    prefixes = prefixes or []
    return any(marker in text for marker in markers) or any(text.startswith(prefix) for prefix in prefixes)


def _match_complex_ability_gain(text):
    ability_text, condition_text = _extract_ability_gain(text)
    if not ability_text:
        return None
    result = {}
    if condition_text:
        if 'かつ' in condition_text:
            _assign_conditions(result, condition_text.split('かつ'))
        else:
            _assign_condition(result, condition_text)
    _assign_ability_gain(result, ability_text)
    return result


def _match_complex_duration_structure(text):
    if '、' not in text or 'ライブ終了時まで、' not in text:
        return None

    parts = text.split('、')
    if len(parts) == 2:
        first_part = parts[0].strip()
        second_part = parts[1].rstrip('。').strip()
        if 'ライブ終了時まで、' not in second_part:
            return None
        result = {}
        _assign_duration_action(result, first_part, second_part.replace('ライブ終了時まで、', ''))
        return result

    if len(parts) == 3 and (parts[1].strip() == 'ライブ終了時まで' or 'ライブ終了時まで、' in parts[1]):
        result = {}
        _assign_duration_action(result, parts[0].strip(), parts[2])
        return result

    return None


def _match_complex_or_trigger(text):
    if '登場か、エリアを移動したとき' not in text:
        return None
    parts = text.split('、')
    if len(parts) != 2:
        return None
    result = {}
    _assign_condition(result, parts[0].strip())
    _set_action_or_raw(result, strip_suffix_period(parts[1]).strip())
    return result


def _match_complex_multi_conditions(text):
    if text.count('場合') < 2 and text.count('とき') < 2:
        return None
    parts = text.split('、')
    if len(parts) < 3:
        return parse_conditional_effect(text)
    result = {}
    _assign_conditions(result, [parts[0].strip(), parts[1].strip()])
    _set_action_or_raw(result, parts[2].rstrip('。').strip())
    return result


def _match_complex_three_part_condition(text):
    parts = split_commas_smartly(text)
    if len(parts) != 3:
        return None

    condition1_part = parts[0].strip()
    condition2_part = parts[1].strip()
    action_part = strip_suffix_period(parts[2]).strip()

    if not any(marker in condition2_part for marker in ['場合', 'とき', 'かつ']):
        return None

    result = {}
    _assign_conditions(result, [condition1_part, condition2_part])
    ability_text, _ = _extract_ability_gain(action_part)
    if ability_text:
        _assign_ability_gain(result, ability_text)
        return result
    _set_action_or_raw(result, action_part)
    return result


def parse_effect_backwards(text):
    """Parse text backwards to extract action and variables."""
    result = {}
    text = text.strip()
    text = _attach_player_choice(result, text)
    payment, text = _extract_optional_payment(text)
    if payment:
        result['payment'] = payment
    
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
                heart_matches = extract_heart_types(text)
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
        return _note_action(text)

    if _is_parenthetical_note(text):
        return _note_action(strip_suffix_period(text).strip())

    # Check for heart type choice selection pattern BEFORE period removal (e.g., "{{heart_01}}か{{heart_03}}か{{heart_06}}のうち、1つを選ぶ")
    if re.search(r'{{heart_\d+\.png.*?}}.*?のうち.*?1つを選ぶ', text):
        result = {}
        result['action'] = 'choose_heart'
        result['choice'] = True
        # Extract heart types
        heart_matches = extract_heart_types(text)
        if heart_matches:
            result['heart_types'] = heart_matches
            result['count'] = 1
        return result

    if '{{heart_' in text and 'のうち' in text:
        heart_matches = extract_heart_types(text)
        if heart_matches:
            result = {}
            result['action'] = 'choose_heart'
            result['choice'] = True
            result['heart_types'] = heart_matches
            if '1つ' in text:
                result['count'] = 1
            return result

    # Remove the final period
    text = strip_suffix_period(text)
    text = text.strip('「」『』')

    result = {}

    if text == 'このカードを手札に加えてもよい' or text == 'このカードを手札に加える':
        result['action'] = 'may_add_to_hand'
        result['target'] = 'self'
        return result

    if 'エールにより公開された自分のカードの中にライブカードが1枚以上ある場合' in text:
        condition = parse_condition(text)
        if condition:
            return {'condition': condition}

    if text == 'このカードを手札に加えてもよい。この能力は' or text == 'このカードを手札に加えてもよい。この能力は、':
        result['action'] = 'may_add_to_hand'
        result['target'] = 'self'
        return result

    if re.fullmatch(r'エネルギーを([\d０-９]+)枚アクティブに(?:する)?', text):
        count_match = re.fullmatch(r'エネルギーを([\d０-９]+)枚アクティブに(?:する)?', text)
        result['action'] = 'activate_energy'
        result['count'] = _normalized_int(count_match.group(1))
        return result

    if '自分のエールによって公開されている場合のみ発動する' in text:
        result['action'] = 'activation_restriction'
        result['restriction'] = 'cheer_revealed_self'
        return result

    if text.startswith('これにより控え室に置いたメンバーカードより') or text.startswith('これにより控え室に置いたメンバーカードを1枚'):
        result['action'] = 'selected_discarded_member_card'
        result['source'] = 'waitroom'
        if text.endswith('1枚'):
            result['count'] = 1
        return result

    if 'ライブの合計スコアを－' in text and '０未満にはならない' in text:
        result['action'] = 'reduce_score'
        match = re.search(r'ライブの合計スコアを－([\d０-９]+)する', text)
        if match:
            result['amount'] = _normalized_int(match.group(1))
        result['note'] = 'live_total_score_cannot_go_below_zero'
        return result

    if text == 'そのエールで得たブレードハートを失い、もう一度エールを行う':
        result['action'] = 'retry_cheer'
        return result

    if 'そのメンバーは' in text and '移動させる' in text:
        action = _move_member_action(text)
        action['target'] = 'selected_member'
        return action

    if 'のうち1色につき' in text and 'メンバーが持つ{{heart_' in text:
        result['action'] = 'add_score'
        result['amount'] = 1
        result['condition'] = {
            'type': 'heart_selection',
            'operator': 'any',
            'target': 'self',
        }
        heart_types = extract_heart_types(text)
        if heart_types:
            result['heart_types'] = heart_types
        group = extract_group_name(text)
        if group:
            result['group'] = group
        return result

    if text in ('そのメンバーは', 'そのメンバーは、'):
        result['action'] = 'selected_member_reference'
        result['target'] = 'selected_member'
        return result

    if text in ('このメンバーがいたエリアに移動させる', 'このメンバーがいたエリアに移動する'):
        return _move_member_action(text)

    if 'フォーメーションチェンジ' in text:
        result['action'] = 'formation_change'
        result['may'] = 'もよい' in text or 'してもよい' in text
        if '自分のステージにいるメンバー' in text or '自分のステージにいるの' in text:
            result['target'] = 'self'
        return result

    if '自分のステージにいる' in text and 'メンバー1人は' in text:
        return _select_member_action(text, target='self')

    if '相手のステージにいる「ミア・テイラー」以外のメンバーを1人選ぶ' in text:
        action = _select_member_action(text, target='opponent')
        action['exclude_character'] = 'ミア・テイラー'
        return action

    if '元々の{{icon_blade.png|ブレード}}の数が同じ場合についても同じことを行う' in text:
        result['action'] = 'repeat_same_effect'
        result['compares'] = 'original_blade_count'
        return result

    # Check for cost-total conditional pattern (e.g., "それらのカードのコストの合計が、6の場合")
    # This handles effects that branch based on the total cost of cards placed in the cost
    cost_total_match = re.search(r'(それらのカード|公開したカード|それら)のコストの合計', text)
    if cost_total_match:
        result['condition'] = {
            'type': 'cost_total',
            'reference': cost_total_match.group(1),  # "それらのカード" or "公開したカード"
            'operator': '==',
        }
        result['cost_reference'] = True  # Flag indicating this references cost cards
        
        # Extract all cost-value branches (e.g., "6の場合、...。合計が8の場合、...")
        branches = []
        # Pattern for single value: "Xの場合、Y" or "合計がXの場合、Y"
        # Match both with and without "合計が" prefix, with or without comma
        single_branches = re.findall(r'(?:合計が)?、?(\d+)の場合、(.+?)(?=(?:合計が)?、?\d+の場合|$)', text)
        
        if single_branches:
            for cost_val, effect_text in single_branches:
                effect_text = effect_text.rstrip('。').strip()
                if effect_text:
                    branch = {
                        'cost_total': int(cost_val),
                        'effect': parse_effect_backwards(effect_text)
                    }
                    branches.append(branch)
        
        # Pattern for multiple values: "10、20、30、40、50のいずれかの場合"
        multi_value_match = re.search(r'(\d+、\d+(?:、\d+)*)のいずれかの場合、(.+)', text)
        if multi_value_match:
            values = [int(v) for v in multi_value_match.group(1).split('、')]
            effect_text = multi_value_match.group(2).rstrip('。').strip()
            for val in values:
                branch = {
                    'cost_total': val,
                    'effect': parse_effect_backwards(effect_text)
                }
                branches.append(branch)
        
        if branches:
            result['branches'] = branches
            return result
        else:
            # If no branches parsed, fall through to generic parsing
            pass

    # Choice prefix for "self or opponent" selection.
    if text.startswith('自分か相手を選ぶ'):
        result['choice'] = True
        result['options'] = ['self', 'opponent']
        text = text.replace('自分か相手を選ぶ。', '', 1).replace('自分か相手を選ぶ', '', 1).strip()

    if text in ('のみ起動できる', 'のみ発動する', 'のみ起動できる。', 'のみ発動する。'):
        result['action'] = 'activation_restriction'
        result['restriction'] = 'only_this_card'
        return result

    if text in ('このメンバーをポジションチェンジしてもよい。', 'このメンバーをポジションチェンジしてもよい', 'このメンバーをポジションチェンジする。', 'このメンバーをポジションチェンジする'):
        result['action'] = 'may_position_change'
        result['target'] = 'self'
        return result
    
    # Check for "として扱う" (treated as) pattern - multiple groups
    if 'として扱う' in text:
        result['action'] = 'treat_as'
        # Extract groups
        group_matches = extract_all_groups(text)
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
            for index, part in enumerate(parts):
                part = part.strip('、').strip()
                if index == 0 and part.endswith(('アクティブに', 'ウェイトに', '登場させ')) and 'し、' in text:
                    part += 'し'
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
    text = _extract_position_prefix(text, result)
    
    # Check for source modifiers at the beginning (e.g., "自分のエネルギーデッキから")
    text = _extract_source(text, result)
    if text is None:
        return result
    
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
        text = text.replace(duration_match.group(1), '').strip()
        if not text:
            return result
    
    # Check for card play timing (e.g., "このカードのプレイに際し")
    timing_match = re.search(r'このカードのプレイに際し', text)
    if timing_match:
        result['timing'] = 'during_card_play'
        text = text.replace(timing_match.group(0), '').strip()
        if not text:
            return result
    
    # Check for position modifiers (e.g., "【左サイド】")
    position_match = re.search(r'【(左サイド|右サイド)】', text)
    if position_match:
        position_map = {'左サイド': 'left_side', '右サイド': 'right_side'}
        result['position'] = position_map.get(position_match.group(1))
        text = text.replace(position_match.group(0), '').strip()
        if not text:
            return result

    # Check for member activation patterns.
    if 'エネルギー' in text and 'アクティブ' in text and ('アクティブにし' in text or 'アクティブにする' in text):
        result['action'] = 'activate_energy'
        count_match = re.search(r'([\d０-９]+)枚', text)
        if count_match:
            result['count'] = _normalized_int(count_match.group(1))
        if 'もよい' in text:
            result['may'] = True
        return result

    if 'メンバー' in text and 'アクティブ' in text and ('アクティブにし' in text or 'アクティブにする' in text):
        result['action'] = 'activate_member'
        if 'ウェイト状態' in text:
            result['source_state'] = 'wait'
        elif 'アクティブ状態' in text:
            result['source_state'] = 'active'
        if '自分のステージ' in text:
            result['source'] = 'stage'
            result['target'] = 'self'
        elif '相手のステージ' in text:
            result['source'] = 'stage'
            result['target'] = 'opponent'
        count_match = re.search(r'([\d０-９]+)人', text)
        if count_match:
            result['count'] = _normalized_int(count_match.group(1))
        if 'もよい' in text:
            result['may'] = True
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
        if 'コストを' in text or 'コスト' in text:
            result['action'] = 'modify_cost'
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
    if '元々持つ{{icon_blade.png|ブレード}}の数は' in text and 'になる' in text:
        blade_value_match = re.search(r'元々持つ\{\{icon_blade\.png\|ブレード\}\}の数は([\d０-９]+)つになる', text)
        if blade_value_match:
            result['action'] = 'set_original_blade_count'
            result['scope'] = 'original_blade_count'
            result['value'] = _normalized_int(blade_value_match.group(1))
            if 'センターエリア' in text:
                result['position_requirement'] = 'center'
            if '『' in text and '』' in text:
                group = extract_group_name(text)
                if group:
                    result['group'] = group
            if '自分のステージ' in text:
                result['source'] = 'stage'
                result['target'] = 'self'
            elif '相手のステージ' in text:
                result['source'] = 'stage'
                result['target'] = 'opponent'
            return result

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
        
        # Remove the per-unit clause and continue parsing
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

    if result.get('action') == 'member_to_wait':
        original_blade_match = re.search(r'元々持つ.*?ブレード.*?(\d+)つ以下', text)
        if original_blade_match:
            result['original_blade_count'] = _normalized_int(original_blade_match.group(1))
            result['original_blade_operator'] = '<='
        if 'ウェイト状態の' in text:
            result['source_state'] = 'wait'
        if 'アクティブ状態の' in text:
            result['source_state'] = 'active'

    if not result:
        result['raw_text'] = text
    
    return result

def parse_effect_context_backwards(context):
    """Parse context backwards to extract variables using utility functions."""
    variables = {}
    
    # Extract count (e.g., "1枚", "2枚")
    count = extract_count(context)
    if count:
        variables['count'] = count
    
    # Extract max (e.g., "1枚まで")
    max_count = extract_int(r'(\d+)枚まで', context)
    if max_count:
        variables['up_to'] = max_count
    
    # Extract person count with up_to (e.g., "1人を" implies up_to 1 in some contexts)
    person_count = extract_int(r'(\d+)人を', context)
    if person_count:
        variables['count'] = person_count
        # For opponent target actions, "1人を" often implies "up_to 1"
        if '相手' in context:
            variables['up_to'] = person_count
    
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
    elif 'ステージ' in context:
        variables['source'] = 'stage'
    
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
    
    # Extract groups
    group = extract_group_name(context)
    if group:
        variables['group'] = group
    else:
        # Check for multiple groups
        group_matches = extract_all_groups(context)
        if group_matches:
            variables['groups'] = group_matches
            variables['group'] = group_matches[0]  # Also set first group for compatibility
    
    # Check for character names in quotes (e.g., "「上原歩夢」のメンバーカード")
    character = extract_quoted_name(context)
    if character:
        variables['character'] = character
    
    # Check for cost reduction pattern (e.g., "コストは1減る")
    cost_reduction = extract_int(r'コストは(\d+)減る', context)
    if cost_reduction:
        variables['cost_reduction'] = cost_reduction
    cost_reduction = extract_int(r'コストは(\d+)少なくなる', context)
    if cost_reduction:
        variables['cost_reduction'] = cost_reduction
    
    # Check for "として扱う" (treated as) pattern - multiple groups.
    if '能力を持たない' in context:
        variables['no_ability'] = True
    
    # Extract cost limit (e.g., "コスト2以下" or "2コスト以下")
    cost_limit = extract_int(r"コスト(\d+)以下", context)
    if not cost_limit:
        cost_limit = extract_int(r"(\d+)コスト以下", context)
    if cost_limit:
        variables['cost_limit'] = cost_limit
    
    # Extract target (e.g., "相手の", "自分の")
    if 'そのプレイヤー' in context:
        variables['target'] = 'selected_player'
    elif '相手' in context:
        variables['target'] = 'opponent'
    elif '自分' in context:
        variables['target'] = 'self'
    
    # Extract position (left_side, right_side, center)
    if '【左サイド】' in context:
        variables['position'] = 'left_side'
    elif '【右サイド】' in context:
        variables['position'] = 'right_side'
    elif '【センター】' in context:
        variables['position'] = 'center'
    
    # Extract heart types
    heart_types = extract_heart_types(context)
    if heart_types:
        variables['heart_types'] = heart_types
    
    # Extract blade count
    blade_count = extract_blade_count(context)
    if blade_count > 0:
        variables['blade_count'] = blade_count
        if 'resource' not in variables:
            variables['resource'] = 'blade'
        if 'resource_count' not in variables:
            variables['resource_count'] = blade_count
    
    # Extract cost (e.g., "コスト3以上")
    cost = extract_cost(context)
    if cost:
        variables['cost'] = cost
    
    # Check for "all" modifier (e.g., "すべて")
    if 'すべて' in context:
        variables['all'] = True
    
    # Check for "different" modifier (e.g., "異なる")
    if '異なる' in context:
        if 'カード名' in context:
            variables['different'] = 'card_name'
        elif 'グループ名' in context:
            variables['different'] = 'group_name'
    
    # Check for "exclude_this_member" (e.g., "このメンバー以外の")
    if 'このメンバー以外の' in context or 'ほかの' in context:
        variables['exclude_this_member'] = True
    
    # Check for "cost_min" (e.g., "コスト3以上の")
    cost_min = extract_int(r'コスト(\d+)以上', context)
    if cost_min:
        variables['cost_min'] = cost_min
    
    return variables

def parse_conditional_effect(text):
    """Parse conditional effect with condition marker."""
    result = {}
    text = text.strip()

    if '選んだエリアにメンバーがいる場合' in text:
        result['condition'] = {
            'type': 'selected_area_member_presence',
            'operator': 'present',
            'target': 'selected_area',
        }
        if 'その後、' in text:
            before_then, after_then = text.split('その後、', 1)
            if before_then.strip():
                first_action = parse_effect_backwards(before_then.rstrip('。 、'))
                if _is_parsed_action(first_action):
                    result.setdefault('actions', []).append(first_action)
            action_before_condition, action_after_condition = after_then.split('選んだエリアにメンバーがいる場合', 1)
            if action_before_condition.strip():
                middle_action = parse_effect_backwards(action_before_condition.rstrip('。 、'))
                if _is_parsed_action(middle_action):
                    result.setdefault('actions', []).append(middle_action)
            final_action = parse_effect_backwards(action_after_condition.rstrip('。 、'))
            if _is_parsed_action(final_action):
                result.setdefault('actions', []).append(final_action)
            return result

        before_condition, after_condition = text.split('選んだエリアにメンバーがいる場合', 1)
        if before_condition.strip():
            first_action = parse_effect_backwards(before_condition.rstrip('。 、'))
            if _is_parsed_action(first_action):
                result.setdefault('actions', []).append(first_action)
        final_action = parse_effect_backwards(after_condition.rstrip('。 、'))
        if _is_parsed_action(final_action):
            result.setdefault('actions', []).append(final_action)
        return result

    if 'その後、' in text and '場合' in text and text.index('その後、') < text.index('場合'):
        before_then, after_then = text.split('その後、', 1)
        first_action = parse_effect_backwards(before_then.rstrip('。 、'))
        if _is_parsed_action(first_action):
            result.setdefault('actions', []).append(first_action)
        elif before_then.strip():
            result.setdefault('actions', []).append(_raw_text(before_then.rstrip('。 、')))
        text = after_then.strip()

    if text.startswith('自分か相手を選ぶ') and 'そうした場合' in text:
        text = _attach_player_choice(result, text)
        first_part, second_part = text.split('そうした場合', 1)
        result['actions'] = []
        first_action = parse_effect_backwards(first_part.strip('。 、'))
        if _is_parsed_action(first_action):
            result['actions'].append(first_action)
        else:
            result['actions'].append(_raw_text(first_part.strip('。 、')))
        second_action = parse_effect_backwards(second_part.strip('。 、'))
        if _is_parsed_action(second_action):
            result['actions'].append(second_action)
        else:
            result['actions'].append(_raw_text(second_part.strip('。 、')))
        return result
    
    # Check for ability gain pattern: "「...」を得る" - do this FIRST before any other processing
    ability_text, condition_text = _extract_ability_gain(text)
    if ability_text:
        if 'かつ' in condition_text:
            _assign_conditions(result, condition_text.split('かつ'))
        elif condition_text:
            _assign_condition(result, condition_text)
        _assign_ability_gain(result, ability_text)
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
        heart_matches = extract_heart_types(text)
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
    
    text = _assign_prefixed_source(text, result)
    
    # Check for choice pattern
    if '自分のステージにいるメンバー1人か' in text:
        result['choice'] = True
        result['options'] = ['member', 'energy']
        text = text.replace('自分のステージにいるメンバー1人か', '').strip()
    
    # Check for ability gain pattern: "「...」を得る" - do this BEFORE condition marker split
    ability_text, condition_text = _extract_ability_gain(text)
    if ability_text:
        if 'かつ' in condition_text:
            _assign_conditions(result, condition_text.split('かつ'))
        elif condition_text:
            _assign_condition(result, condition_text)
        _assign_ability_gain(result, ability_text)
        return result
    
    # Split on condition markers
    condition_markers = ['なら', '場合', 'たび']
    for marker in condition_markers:
        if marker in text:
            parts = text.split(marker, 1)
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
                _assign_condition(result, condition_part)
                
                # Parse action
                action = parse_effect_backwards(action_part)
                if action:
                    result['action'] = action
                
                return result
    
    # If no condition marker found, treat as simple effect
    return parse_effect_backwards(text)


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
    
    is_condition = _looks_like_condition(first_part, condition_markers, condition_prefixes)
    
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
    original_first_part = first_part
    first_part = _assign_prefixed_source(first_part, result)
    if first_part != original_first_part:
        if 'source' in result:
            result['actions'].append({'source': result.pop('source')})
        elif 'location' in result:
            result['actions'].append({'location': result.pop('location')})
    elif first_part.startswith('自分のステージにいるメンバー1人か'):
        choice_info = {'choice': True, 'options': ['member', 'energy']}
        first_part = first_part.replace('自分のステージにいるメンバー1人か', '').strip()
        result['actions'].append(choice_info)
    
    # Parse remaining first part if not empty
    if first_part:
        _append_action_or_raw(result['actions'], first_part)
    
    # Parse second part
    _append_action_or_raw(result['actions'], second_part)
    
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

    for matcher in (
        _match_complex_ability_gain,
        _match_complex_duration_structure,
        _match_complex_or_trigger,
        _match_complex_multi_conditions,
        _match_complex_three_part_condition,
    ):
        matched = matcher(text)
        if matched is not None:
            result.update(matched)
            return result
    
    # Split on comma
    parts = split_commas_smartly(text)
    if len(parts) != 2:
        return {'raw_text': text}
    
    first_part = parts[0].strip()
    second_part = strip_suffix_period(parts[1]).strip()
    
    # Check if second part has duration in middle (condition, duration, action structure)
    if 'ライブ終了時まで、' in second_part:
        # This is condition + duration + action
        # Extract action after duration
        action_part = strip_suffix_period(second_part.replace('ライブ終了時まで、', '')).strip()
        _assign_condition(result, first_part)
        result['duration'] = 'until_end_of_live'
        # Check if action part has subject marker pattern ending with "は、"
        # If so, the subject marker should be preserved as part of the action
        # We need to handle this by removing the subject marker temporarily, parsing, then adding it back
        if re.search(r'は、', action_part) and not re.search(r'その後、', action_part):
            # Subject marker present and no sequence marker
            # Split on subject marker to get subject and actual action
            if _assign_subject_action(result, action_part):
                return result
            _set_action_or_raw(result, action_part)
            return result
        else:
            _set_action_or_raw(result, action_part)
        return result
    # Also check for duration at end of second part
    elif second_part.endswith('ライブ終了時まで'):
        _assign_duration_action(result, first_part, second_part.replace('ライブ終了時まで', ''))
        if 'action' in result and isinstance(result['action'], dict):
            merge_position_requirement(result, result['action'])
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
            _assign_subject_action(result, second_part)
            return result
        
        # Parse the action (may contain nested structure)
        if '、' in second_part:
            # Check for sequence marker "その後、" - this should split into separate actions
            if 'その後、' in second_part:
                # Split on sequence marker
                _assign_sequence_actions(result, second_part.split('その後、'))
            else:
                # Nested structure in action - could be two actions
                sub_parts = split_commas_smartly(second_part)
                # Check if this looks like two separate actions vs complex single action
                # Simple heuristic: if first sub_part ends with a verb, it's likely two actions
                action1 = parse_effect_backwards(sub_parts[0].strip())
                if action1 and 'raw_text' not in action1:
                    # Merge position_requirement if present
                    merge_position_requirement(result, action1)
                    result['actions'] = []
                    result['actions'].append(action1)
                    # Parse remaining parts
                    remaining = '、'.join(sub_parts[1:]).rstrip('。').strip()
                    action2 = parse_effect_backwards(remaining)
                    if _is_parsed_action(action2):
                        merge_position_requirement(result, action2)
                        result['actions'].append(action2)
                    else:
                        result['actions'].append(_raw_text(remaining))
                else:
                    # Treat as single complex action
                    _set_action_or_raw(result, second_part, merge_position=True)
        else:
            _set_action_or_raw(result, second_part, merge_position=True)
    else:
        # This is action + action structure
        result['actions'] = []
        first_action = parse_effect_backwards(first_part)
        if _is_parsed_action(first_action):
            merge_position_requirement(result, first_action)
            result['actions'].append(first_action)
        else:
            result['actions'].append(_raw_text(first_part))
        
        second_action = parse_effect_backwards(second_part)
        if _is_parsed_action(second_action):
            result['actions'].append(second_action)
        else:
            result['actions'].append(_raw_text(second_part))
    
    return result

def parse_generic_effect(text):
    """Parse generic effect when no specific pattern matches."""
    result = {}
    
    # Remove leading/trailing whitespace
    text = text.strip()
    original_text = text

    # Check for cost-total conditional pattern (e.g., "それらのカードのコストの合計が、6の場合")
    # This handles effects that branch based on the total cost of cards placed in the cost
    cost_total_match = re.search(r'(それらのカード|公開したカード|それら)のコストの合計', text)
    if cost_total_match:
        result['condition'] = {
            'type': 'cost_total',
            'reference': cost_total_match.group(1),  # "それらのカード" or "公開したカード"
            'operator': '==',
        }
        result['cost_reference'] = True  # Flag indicating this references cost cards
        
        # Extract all cost-value branches (e.g., "6の場合、...。合計が8の場合、...")
        branches = []
        # Pattern for single value: "Xの場合、Y" or "合計がXの場合、Y"
        # Match both with and without "合計が" prefix, with or without comma
        single_branches = re.findall(r'(?:合計が)?、?(\d+)の場合、(.+?)(?=(?:合計が)?、?\d+の場合|$)', text)
        
        if single_branches:
            for cost_val, effect_text in single_branches:
                effect_text = effect_text.rstrip('。').strip()
                if effect_text:
                    branch = {
                        'cost_total': int(cost_val),
                        'effect': parse_effect_backwards(effect_text)
                    }
                    branches.append(branch)
        
        # Pattern for multiple values: "10、20、30、40、50のいずれかの場合"
        multi_value_match = re.search(r'(\d+、\d+(?:、\d+)*)のいずれかの場合、(.+)', text)
        if multi_value_match:
            values = [int(v) for v in multi_value_match.group(1).split('、')]
            effect_text = multi_value_match.group(2).rstrip('。').strip()
            for val in values:
                branch = {
                    'cost_total': val,
                    'effect': parse_effect_backwards(effect_text)
                }
                branches.append(branch)
        
        if branches:
            result['branches'] = branches
            return result

    # Preserve choice context before splitting the rest of the effect.
    text = _attach_player_choice(result, text)

    if original_text.startswith('自分か相手を選ぶ') and 'そうした場合' in original_text:
        return parse_conditional_effect(original_text)

    if original_text.startswith('自分か相手を選ぶ'):
        text = _attach_player_choice(result, original_text)
        result['actions'] = []
        action_parts = _merge_subject_stub(text.rstrip('。').split('。'))
        for action_part in action_parts:
            action_part = action_part.strip('。 、')
            if not action_part:
                continue
            action = parse_effect_backwards(action_part)
            if action and 'raw_text' not in action:
                result['actions'].append(action)
            else:
                result['actions'].append({'raw_text': action_part})
        return result

    if original_text.startswith('ライブ終了時まで') and 'メンバー1人は' in original_text and 'につき、' in original_text:
        return parse_effect_backwards(original_text)

    # Handle per-unit effects before general comma splitting so the multiplier context is preserved.
    payment, text = _extract_optional_payment(text)
    if payment:
        result['payment'] = payment

    if text.startswith('ライブ終了時まで、') and 'につき、' in text:
        result['duration'] = 'until_end_of_live'
        text = text.replace('ライブ終了時まで、', '', 1).strip()

    if 'につき、' in text:
        condition_part, action_part = text.split('、', 1)
        if condition_part.endswith('につき'):
            condition = parse_condition(condition_part)
            if condition:
                result['condition'] = condition
            parsed_action = parse_effect_backwards(action_part.rstrip('。').strip())
            if _is_parsed_action(parsed_action):
                parsed_action = _normalize_action_shape(parsed_action)
                if isinstance(parsed_action, dict) and set(parsed_action.keys()) == {'actions'}:
                    result['actions'] = parsed_action['actions']
                else:
                    merge_position_requirement(result, parsed_action)
                    if 'duration' in result and 'duration' not in parsed_action:
                        parsed_action['duration'] = result['duration']
                    result['action'] = parsed_action
            else:
                result['action'] = _raw_text(action_part.rstrip('。').strip())
            return result
    
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
        subject, actual_action = _parse_subject_action(text_without_duration)
        if subject:
            result['subject'] = subject
            _set_action_or_raw(result, actual_action)
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
        score_limit = _extract_limit(text, 'スコア')
        if score_limit is not None:
            result['score_limit'] = score_limit
        # Extract cost limit if present (for member_card option) - handle both half-width and full-width numbers
        cost_limit = _extract_limit(text, 'コスト')
        if cost_limit is not None:
            result['cost_limit'] = cost_limit
        # Don't return yet, continue with other extractions
    
    # Check for score limit condition (e.g., "スコア3以下")
    score_limit = _extract_limit(text, 'スコア')
    if score_limit is not None:
        result['score_limit'] = score_limit
        # Remove the score limit from text
        text = re.sub(r'スコア[\d０-９]+以下', '', text).strip()
    
    # Check for cost limit condition (e.g., "コスト4以下")
    cost_limit = _extract_limit(text, 'コスト')
    if cost_limit is not None:
        result['cost_limit'] = cost_limit
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
    text = _strip_waitroom_source(text, result)
    
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
    
    # Check for parenthetical notes - strip them
    if '(' in text and ')' in text:
        # Keep the main action, strip parenthetical
        text = re.sub(r'\([^)]+\)', '', text).strip()

    # Check for heart-selection patterns where a group of hearts drives the effect.
    if 'のうち1色につき' in text and 'メンバーが持つ{{heart_' in text:
        result['choice'] = True
        result['actions'] = []
        result['condition'] = {
            'type': 'heart_selection',
            'operator': 'any',
            'target': 'self',
        }
        heart_types = extract_heart_types(text)
        if heart_types:
            result['heart_types'] = heart_types
        if 'スコアを+１する' in text or 'スコアを+1する' in text:
            result['actions'].append({'action': 'add_score', 'amount': 1})
        else:
            action = parse_effect_backwards(text)
            if action and 'raw_text' not in action:
                result['actions'].append(action)
            else:
                result['actions'].append({'raw_text': text})
        return result

    # Check for bullet point choice pattern with conditions BEFORE "以下から1つを選ぶ"
    # This should happen before condition marker check
    if '以下から1つを選ぶ' in text and '・' in text:
        # Check if there's a condition before the choice marker
        condition_markers = ['場合', 'とき', 'かぎり', 'なら']
        has_condition = False
        for marker in condition_markers:
            if marker in text and text.index(marker) < text.index('以下から1つを選ぶ'):
                # Split on condition marker
                parts = text.split(marker, 1)
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
                    bullet_options = _merge_subject_stub(choice_part.split('・'))
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
                                        parts = option.split(marker, 1)
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
            bullet_options = _merge_subject_stub(choice_text.split('・'))
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
                                parts = option.split(marker, 1)
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
            action_parts = _merge_subject_stub(text.rstrip('。').split('。'))
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
            action_parts = _merge_subject_stub(text.rstrip('。').split('。'))
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
                hearts = extract_heart_types(option)
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
            parts = text.split(marker, 1)
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
                    parts = _merge_subject_stub(action_part.split('、'))
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
                        action_parts = _merge_subject_stub(action_part.split('、'))
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
                # Extract action before duration
                action_part = strip_suffix_period(second_part.replace('ライブ終了時まで', '')).strip()
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
            if _is_duration_only_action(action1) and _is_parsed_action(action2):
                action2['duration'] = action1['duration']
                result['action'] = action2
                return result
            if _apply_target_only_action(action1, action2):
                result['actions'] = [action2]
                return result
            result['actions'] = [action1, action2]
            return result
        else:
            # Treat as single complex action
            action = parse_effect_backwards(strip_suffix_period(text))
            if action and 'raw_text' not in action:
                result['action'] = action
                return result
    
    # Simple action
    action = parse_effect_backwards(strip_suffix_period(text))
    if action and 'raw_text' not in action:
        action = _normalize_action_shape(action)
        if isinstance(action, dict) and set(action.keys()) == {'actions'}:
            return action
        merge_position_requirement(result, action)
        result['action'] = action
        return result
    
    # Fallback
    return {'raw_text': text}

