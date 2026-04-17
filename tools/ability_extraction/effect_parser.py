"""Effect parsing for ability extraction."""
import re
from condition_parser import parse_condition, _extract_target as _extract_condition_target
from parser_utils import (
    annotate_tree,
    extract_all_quoted_names,
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


def _is_only_action(action, keys, allow_subset=False):
    """Check if action dict contains only the specified keys."""
    if not isinstance(action, dict):
        return False
    action_keys = set(action.keys())
    if allow_subset:
        return action_keys <= set(keys)
    return action_keys == set(keys)


def _is_target_only_action(action):
    return _is_only_action(action, {'target'})


def _is_duration_only_action(action):
    return _is_only_action(action, {'duration'})


def _is_multiplier_only_action(action):
    """Check if action is only a multiplier modifier."""
    return _is_only_action(action, {'multiplier', 'per_unit', 'unit_type', 'target'}, allow_subset=True)


def _is_timing_only_action(action):
    """Check if action is only a timing modifier."""
    return _is_only_action(action, {'timing'})


def _apply_target_only_action(action, target_action):
    if _is_target_only_action(action) and isinstance(target_action, dict) and 'target' not in target_action:
        target_action['target'] = action['target']
        return True
    return False


def _merge_modifier_actions(actions):
    """Merge modifier-only actions (duration, multiplier, timing, target) with their target actions."""
    if not actions or not isinstance(actions, list):
        return actions
    
    merged = []
    i = 0
    while i < len(actions):
        current = actions[i]
        
        # Skip raw_text actions
        if not isinstance(current, dict) or 'raw_text' in current:
            merged.append(current)
            i += 1
            continue
        
        # Check if this is a modifier-only action
        is_modifier = (
            _is_duration_only_action(current) or
            _is_multiplier_only_action(current) or
            _is_timing_only_action(current) or
            _is_target_only_action(current)
        )
        
        if is_modifier:
            # Find the next actual action to merge with
            j = i + 1
            while j < len(actions):
                next_action = actions[j]
                if isinstance(next_action, dict) and 'raw_text' not in next_action and 'action' in next_action:
                    # Merge modifier into this action
                    if _is_duration_only_action(current):
                        next_action['duration'] = current['duration']
                    elif _is_multiplier_only_action(current):
                        next_action.update({k: v for k, v in current.items()})
                    elif _is_timing_only_action(current):
                        next_action['timing'] = current['timing']
                    elif _is_target_only_action(current):
                        if 'target' not in next_action:
                            next_action['target'] = current['target']
                    # Skip the modifier and continue with the merged action
                    i = j
                    break
                elif isinstance(next_action, dict) and 'raw_text' not in next_action and 'actions' in next_action:
                    # Merge modifier into the first action of nested actions
                    nested_actions = next_action['actions']
                    if nested_actions and isinstance(nested_actions, list) and len(nested_actions) > 0:
                        first_nested = nested_actions[0]
                        if isinstance(first_nested, dict) and 'action' in first_nested:
                            if _is_duration_only_action(current):
                                first_nested['duration'] = current['duration']
                            elif _is_multiplier_only_action(current):
                                first_nested.update({k: v for k, v in current.items()})
                            elif _is_timing_only_action(current):
                                first_nested['timing'] = current['timing']
                            elif _is_target_only_action(current):
                                if 'target' not in first_nested:
                                    first_nested['target'] = current['target']
                    i = j
                    break
                else:
                    # Can't merge, keep both
                    merged.append(current)
                    i = j
                    break
            else:
                # No action found to merge with, keep modifier
                merged.append(current)
                i += 1
        else:
            # This is a regular action, keep it
            merged.append(current)
            i += 1
    
    return merged


def _attach_player_choice(result, text):
    if not text.startswith('自分か相手を選ぶ'):
        return text
    result['choice'] = True
    result['options'] = ['self', 'opponent']
    return text.replace('自分か相手を選ぶ。', '', 1).replace('自分か相手を選ぶ', '', 1).strip()


def _extract_optional_payment(text):
    def _create_discard_payment():
        return {
            'action': 'discard_to_waitroom',
            'source': 'hand',
            'count': 1,
            'optional': True,
            'text': '手札を1枚控え室に置いてもよい',
        }
    
    def _create_deck_top_payment():
        return {
            'action': 'may_place_card',
            'target': 'self',
            'source': 'deck_top',
            'destination': 'waitroom',
            'optional': True,
            'text': '自分のデッキの一番上のカードを控え室に置いてもよい',
        }
    
    if '支払ってもよい' not in text and '支払った' not in text:
        if text.startswith('手札を1枚控え室に置いてもよい'):
            if '：' in text:
                return _create_discard_payment(), text.split('：', 1)[1].strip()
            return _create_discard_payment(), text
        if text.startswith('自分のデッキの一番上のカードを控え室に置いてもよい'):
            if '：' in text:
                return _create_deck_top_payment(), text.split('：', 1)[1].strip()
            return _create_deck_top_payment(), text
        return None, text

    prefix, suffix = (text.split('：', 1) + [''])[:2]
    if '支払ってもよい' not in prefix and '支払った' not in prefix:
        if prefix.startswith('手札を1枚控え室に置いてもよい'):
            return _create_discard_payment(), suffix.strip() if suffix else text
        if prefix.startswith('自分のデッキの一番上のカードを控え室に置いてもよい'):
            return _create_deck_top_payment(), suffix.strip() if suffix else text
        return None, text

    payment = {'optional': '支払ってもよい' in prefix, 'text': prefix.strip()}
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
    return {'raw_text': text, 'text': text}


def _note_action(text):
    return {'action': 'note', 'text': text}


def _infer_card_type(text, default='card'):
    """Infer card type from text."""
    if 'メンバーカード' in text:
        return 'member_card'
    elif 'ライブカード' in text:
        return 'live_card'
    elif 'エネルギーカード' in text or 'エネルギー' in text:
        return 'energy_card'
    elif 'カード' in text:
        return 'card'
    return default


def _infer_target(text):
    """Infer target from text."""
    if '相手' in text or text.startswith('自身のステージ'):
        return 'opponent'
    elif '自分' in text or 'このメンバー' in text:
        return 'self'
    return None


def _normalize_parsed_tree(value):
    """Fill obvious defaults on parsed nodes without changing the shape."""
    if isinstance(value, dict):
        action = value.get('action')
        text = value.get('text', '')
        if action == 'gain_resource':
            if 'resource' not in value:
                if 'ブレード' in text:
                    value['resource'] = 'blade'
                elif 'ハート' in text or value.get('heart_types'):
                    value['resource'] = 'heart'
                elif 'エネルギー' in text:
                    value['resource'] = 'energy'
            if 'resource_count' not in value and 'count' in value:
                value['resource_count'] = value['count']
        elif action == 'add_to_hand':
            if 'card_type' not in value:
                value['card_type'] = _infer_card_type(text)
            if 'group' not in value:
                group_match = re.search(r'『(.+?)』', text)
                if group_match:
                    value['group'] = group_match.group(1)
        elif action == 'draw_cards' and 'count' not in value:
            value['count'] = 1
        elif action == 'look_at_cards' and 'count' not in value:
            count_match = re.search(r'カードを(\d+)枚', text)
            value['count'] = int(count_match.group(1)) if count_match else 1
        elif action == 'place_card' and 'card_type' not in value:
            value['card_type'] = _infer_card_type(text)
        elif action == 'deploy_to_stage':
            if 'target' not in value:
                value['target'] = _infer_target(text) or 'self'
            if 'card_type' not in value:
                value['card_type'] = _infer_card_type(text, default='member_card')
        elif action == 'member_to_wait':
            if 'target' not in value:
                value['target'] = _infer_target(text)
            if 'source' not in value:
                value['source'] = 'stage'
        for item in value.values():
            _normalize_parsed_tree(item)
    elif isinstance(value, list):
        for item in value:
            _normalize_parsed_tree(item)
    return value


def _annotate_return(fn):
    def wrapper(text, *args, **kwargs):
        return _normalize_parsed_tree(annotate_tree(fn(text, *args, **kwargs), text))
    return wrapper


def _select_member_action(text, *, target=None):
    result = {'action': 'select_member', 'text': text}
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
    if 'すべてのメンバー' in text:
        result['all'] = True
    if '相手の' in text:
        result['target'] = 'opponent'
    elif '自分の' in text and target is None:
        result['target'] = 'self'
    if '自分のステージ' in text and 'source' not in result:
        result['source'] = 'stage'
    elif '相手のステージ' in text and 'source' not in result:
        result['source'] = 'stage'
    return result


def _move_member_action(text):
    result = {'action': 'move_member', 'text': text}
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
    # Only treat text as a parenthetical note if the ENTIRE text is wrapped in parentheses
    # Not just if it ends with a parenthetical note
    if stripped.startswith(('(', '（')) and stripped.endswith((')', '）')):
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
        if isinstance(action, dict) and 'actions' in action and 'action' not in action:
            result['actions'] = action['actions']
            for item_key, item_value in action.items():
                if item_key != 'actions' and item_key not in result:
                    result[item_key] = item_value
        else:
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
    if _is_parsed_action(action) and isinstance(action, dict) and 'actions' in action and 'action' not in action:
        actions.extend(action['actions'])
        return actions[-1] if actions else None
    actions.append(action if _is_parsed_action(action) else _raw_text(text))
    return actions[-1]


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
    result['text'] = ability_text
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


def _split_leading_condition_clause(text):
    """Split a sentence that starts with a condition clause into condition and action parts."""
    text = text.strip()
    best_idx = None
    best_marker = None
    for marker in ('場合', 'とき', 'かぎり', 'なら'):
        idx = text.find(marker)
        if idx <= 0:
            continue
        suffix = text[idx + len(marker):].lstrip()
        if not suffix.startswith('、'):
            continue
        if best_idx is None or idx < best_idx:
            best_idx = idx
            best_marker = marker
    if best_idx is None:
        return None, None
    condition_part = text[:best_idx + len(best_marker)].strip()
    action_part = text[best_idx + len(best_marker):].lstrip().lstrip('、').strip()
    return condition_part, action_part


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


@_annotate_return
def parse_effect_backwards(text):
    """Parse text backwards to extract action and variables."""
    result = {}
    text = text.strip()
    text = _attach_player_choice(result, text)
    payment, text = _extract_optional_payment(text)
    if payment:
        result['payment'] = payment

    # Check for choose heart color pattern BEFORE condition split to preserve full context
    if '好きなハートの色を1つ指定する' in text and 'そのハートを1つ得る' in text:
        # Check for duration
        duration = None
        if 'ライブ終了時まで、' in text:
            duration = 'until_end_of_live'
            text = text.replace('ライブ終了時まで、', '').strip()
        elif 'ライブ終了時まで' in text:
            duration = 'until_end_of_live'
            text = text.replace('ライブ終了時まで', '').strip()
        
        result['actions'] = [
            {
                'action': 'choose_heart_color',
                'choice': True,
                'count': 1,
                'text': '好きなハートの色を1つ指定する',
            },
            {
                'action': 'gain_resource',
                'resource': 'heart',
                'resource_count': 1,
                'count': 1,
                'source': 'chosen_heart',
                'text': 'そのハートを1つ得る',
            },
        ]
        # Add duration to the gain_resource action if present
        if duration:
            result['actions'][1]['duration'] = duration
            result['duration'] = duration
        return result

    condition_part, action_part = _split_leading_condition_clause(text)
    if condition_part and action_part:
        condition = parse_condition(condition_part)
        if condition:
            result['condition'] = condition
        action = parse_effect_backwards(action_part)
        if _is_parsed_action(action):
            result['action'] = action
        else:
            result['action'] = _raw_text(action_part)
        return result
    
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

    if 'エネルギーデッキから' in text and 'エネルギーカード' in text and 'ウェイト状態で置く' in text:
        result['action'] = 'place_card'
        result['card_type'] = 'energy_card'
        result['state'] = 'wait'
        result['source'] = 'energy_deck'
        count_match = re.search(r'([\d０-９]+)枚', text)
        if count_match:
            result['count'] = _normalized_int(count_match.group(1))
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
    
    # Check for "デッキの上に置く" (place on deck) pattern
    if 'デッキの上に置く' in text:
        result['action'] = 'place_on_deck'
        result['destination'] = 'deck_top'
        if '好きな枚数' in text:
            result['up_to'] = True
        if '好きな順番' in text:
            result['order'] = 'any'
        return result

    # Check for "デッキの一番下に置く" (place on bottom of deck) pattern
    if 'デッキの一番下に置く' in text or 'デッキの下に置く' in text:
        result['action'] = 'place_card'
        result['destination'] = 'deck_bottom'
        if '好きな枚数' in text:
            result['up_to'] = True
        if '好きな順番' in text:
            result['order'] = 'any'
        if 'メンバーカード' in text:
            result['card_type'] = 'member_card'
        elif 'ライブカード' in text:
            result['card_type'] = 'live_card'
        elif 'エネルギーカード' in text:
            result['card_type'] = 'energy_card'
        count_match = re.search(r'([\d０-９]+)枚', text)
        if count_match:
            result['count'] = _normalized_int(count_match.group(1))
        elif '1枚' in text:
            result['count'] = 1
        if 'そのプレイヤー' in text:
            result['target'] = 'selected_player'
        elif '相手' in text:
            result['target'] = 'opponent'
        elif '自分' in text:
            result['target'] = 'self'
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

    # Strip trailing parenthetical notes BEFORE period removal
    # (e.g., "（この能力はセンターエリアにいる場合のみ発動する。）")
    if text.endswith(('。）', '.)', ')')):
        # Find the last opening parenthesis
        last_open_paren = max(text.rfind('（'), text.rfind('('))
        if last_open_paren > 0:
            # Check if it's a trailing parenthetical note (space before it, or starts with common note patterns)
            paren_content = text[last_open_paren:]
            if paren_content.startswith(('（この能力は', '（この効果は', '（ウェイト状態のメンバーが持つ')) or text[last_open_paren - 1] in '。 ':
                text = text[:last_open_paren].strip()

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

    if 'これにより控え室に置いたカードと同じ枚数' in text and '手札に加える' in text:
        result['action'] = 'add_to_hand'
        result['count'] = 'discarded_count'
        result['source'] = 'waitroom'
        if 'ライブカード' in text:
            result['card_type'] = 'live_card'
        elif 'メンバーカード' in text:
            result['card_type'] = 'member_card'
        else:
            result['card_type'] = 'card'
        return result

    if 'そのライブカードを手札に加える' in text:
        result['action'] = 'add_to_hand'
        result['count'] = 1
        result['card_type'] = 'live_card'
        result['source'] = 'waitroom'
        result['target'] = 'self'
        return result

    if 'そのメンバーカードを手札に加える' in text:
        result['action'] = 'add_to_hand'
        result['count'] = 1
        result['card_type'] = 'member_card'
        result['source'] = 'waitroom'
        result['target'] = 'self'
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
            'type': 'cost_total_equal',
            'reference': cost_total_match.group(1),  # "それらのカード" or "公開したカード"
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

    # High-priority full pattern: choose a player, place a card on the bottom of that player's
    # deck, then draw. This must run before the generic "場合" splitter so "そうした場合" does
    # not get misread as a condition marker.
    if 'そのプレイヤーの控え室にあるライブカードを1枚' in text and 'そのプレイヤーのデッキの一番下に置く' in text and 'そうした場合' in text and 'カードを1枚引く' in text:
        first_part, second_part = text.split('そうした場合', 1)
        result['choice'] = True
        result['options'] = ['self', 'opponent']
        result['actions'] = [{
            'action': 'place_card',
            'source': 'waitroom',
            'target': 'selected_player',
            'destination': 'deck_bottom',
            'card_type': 'live_card',
            'count': 1,
            'text': first_part.strip('。 、'),
        }]
        second_action = parse_effect_backwards(second_part.strip('。 、'))
        if _is_parsed_action(second_action):
            result['actions'].append(second_action)
        else:
            result['actions'].append(_raw_text(second_part.strip('。 、')))
        return result

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
    
    # Check for opponent tap action with source state (e.g., "自身のステージにいるアクティブ状態のメンバー1人をウェイトにする")
    if 'アクティブ状態のメンバー' in text and 'ウェイトにする' in text:
        result['action'] = 'member_to_wait'
        result['source_state'] = 'active'
        result['source'] = 'stage'
        # Extract count
        count_match = re.search(r'(\d+)人', text)
        if count_match:
            result['count'] = int(count_match.group(1))
        else:
            result['count'] = 1
        result['destination'] = 'wait'
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
    
    # Try to match action patterns anywhere in the text (not just exact match)
    # This handles cases like "自身のステージにいるアクティブ状態のメンバー1人をウェイトにする。"
    # where the action is embedded in extra context
    matched_action = None
    for pattern, action_type in action_patterns.items():
        if action_type != 'note' and pattern in text:
            matched_action = action_type
            # Prefer longer, more specific patterns
            if len(pattern) > 3:  # Avoid matching very short patterns like "する"
                break
    
    if matched_action:
        result['action'] = matched_action
    
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
        if 'このメンバー' not in text and ('自分のステージ' in text or '相手のステージ' in text):
            selection_text = text.split('アクティブ', 1)[0].rstrip('、。')
            select_action = _select_member_action(selection_text)
            activate_action = {'action': 'activate_member', 'text': text}
            if 'ウェイト状態' in text:
                activate_action['source_state'] = 'wait'
            elif 'アクティブ状態' in text:
                activate_action['source_state'] = 'active'
            if '自分のステージ' in text:
                activate_action['source'] = 'stage'
                activate_action['target'] = 'self'
            elif '相手のステージ' in text:
                activate_action['source'] = 'stage'
                activate_action['target'] = 'opponent'
            count_match = re.search(r'([\d０-９]+)人', text)
            if count_match:
                count_value = _normalized_int(count_match.group(1))
                select_action['count'] = count_value
                activate_action['count'] = count_value
            if 'もよい' in text:
                activate_action['may'] = True
            result['actions'] = [select_action, activate_action]
            return result
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
    
    # Check for generic score patterns (+xする) - handle both half-width and full-width digits
    score_match = re.search(r'\+([０-９\d]+)する', text)
    if score_match:
        if 'コストを' in text or 'コスト' in text:
            result['action'] = 'modify_cost'
        else:
            result['action'] = 'add_score'
        result['amount'] = int(score_match.group(1).translate(str.maketrans("０１２３４５６７８９", "0123456789")))
        # Check if it's a live score bonus
        if 'ライブのスコア' in text or 'ライブスコア' in text:
            result['target'] = 'live_score'
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

    if text.startswith('手札を1枚控え室に置いてもよい'):
        result['action'] = 'discard_to_waitroom'
        result['count'] = 1
        result['source'] = 'hand'
        result['optional'] = True
        return result

    if 'このメンバーをウェイトにし' in text or 'このメンバーをウェイトにする' in text:
        result['action'] = 'member_to_wait'
        result['target'] = _infer_target(text) or 'self'
        result['source'] = 'stage'
        if 'このメンバー以外' in text:
            result['target'] = 'selected_member'
        return result

    if 'ライブの合計スコアを－' in text or 'ライブの合計スコアを-' in text:
        result['action'] = 'reduce_score'
        match = re.search(r'ライブの合計スコアを[－-]([\d０-９]+)する', text)
        if match:
            result['amount'] = _normalized_int(match.group(1))
        else:
            result['amount'] = 1
        return result

    if '自分のメインフェイズの間' in text and 'いずれかの領域から控え室に置かれるたび' in text and '支払ってもよい' in text:
        result['action'] = 'pay_energy'
        result['resource'] = 'energy'
        result['count'] = 1
        result['optional'] = True
        result['timing'] = 'main_phase'
        result['condition'] = {
            'type': 'card_move_trigger',
            'location': 'waitroom',
            'trigger': 'discard_or_move',
            'target': 'self',
        }
        return result

    if '手札の「' in text and '控え室に置いてもよい' in text:
        result['action'] = 'may_discard_to_waitroom'
        result['optional'] = True
        result['source'] = 'hand'
        names = extract_all_quoted_names(text)
        if names:
            result['card_names'] = names
        count_match = re.search(r'好きな枚数|([\d０-９]+)枚', text)
        if count_match and count_match.group(1):
            result['count'] = _normalized_int(count_match.group(1))
        return result

    if text.startswith('手札の「') and '」を' in text:
        names = extract_all_quoted_names(text)
        if names:
            result['action'] = 'select_card'
            result['source'] = 'hand'
            result['card_names'] = names
            if '好きな枚数' in text:
                result['up_to'] = True
            return result

    if '自分のステージのメンバー1人は' in text:
        result['target'] = 'selected_member'
        text = text.replace('自分のステージのメンバー1人は', '').strip('、')
        if not text:
            return result

    if 'これにより控え室に置いたカードと同じグループ名を持つメンバー1人は' in text:
        result['target'] = 'selected_member'
        result['reference'] = 'discarded_card_group'
        text = text.replace('これにより控え室に置いたカードと同じグループ名を持つメンバー1人は', '').strip('、')
        if not text:
            return result

    if '下に置かれているエネルギーカードはエネルギーデッキに戻す' in text:
        result['action'] = 'return_energy_card'
        result['source'] = 'under_member'
        result['card_type'] = 'energy_card'
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
    
    # Check for area selection pattern (若菜四季 case)
    if '登場したエリアとは別の自分のエリア1つを選ぶ' in text or 'いるエリアとは別の自分のエリア1つを選ぶ' in text:
        result['action'] = 'select_area'
        result['source'] = 'stage'
        result['exclude'] = 'deployed_area'
        result['count'] = 1
        result['target'] = 'self'
        return result

    if 'エネルギーカード' in text and ('ウェイト状態で置く' in text or 'アクティブ状態で置く' in text or 'ウェイト状態で' in text or 'アクティブ状態で' in text):
        state = 'wait' if 'ウェイト状態' in text else 'active'
        result['action'] = 'place_card'
        result['card_type'] = 'energy_card'
        result['state'] = state
        if 'エネルギーデッキ' in text:
            result['source'] = 'energy_deck'
        count_match = re.search(r'([\d０-９]+)枚', text)
        if count_match:
            result['count'] = _normalized_int(count_match.group(1))
        return result
    
    # Check for card selection by name pattern (鬼塚冬毬 case)
    if 'カード名が異なる' in text and 'ライブカード' in text:
        result['action'] = 'select_card'
        result['source'] = 'waitroom' if '控え室' in text else None
        result['card_type'] = 'live_card'
        result['selection_criteria'] = 'different_names'
        count_match = re.search(r'(\d+)\s*枚選ぶ', text)
        result['count'] = int(count_match.group(1)) if count_match else 1
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

    # Check for explicit energy reduction pattern (e.g., "{{icon_energy.png|E}}減る")
    if '{{icon_energy.png|E}}' in text and '減る' in text:
        result['action'] = 'reduce_cost'
        result['resource'] = 'energy'
        result['amount'] = text.count('{{icon_energy.png|E}}') or 1
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

    if result.get('action') == 'member_to_wait':
        # Pattern: 元々持つ{{icon_blade.png|ブレード}}の数がちょうど4つ
        original_blade_match = re.search(r'元々持つ.*?ブレード.*?ちょうど(\d+)つ', text)
        if original_blade_match:
            result['original_blade_count'] = _normalized_int(original_blade_match.group(1))
            result['original_blade_operator'] = '=='
        # Pattern: 元々持つ{{icon_blade.png|ブレード}}の数が3つ以下
        original_blade_match = re.search(r'元々持つ.*?ブレード.*?(\d+)つ以下', text)
        if original_blade_match:
            result['original_blade_count'] = _normalized_int(original_blade_match.group(1))
            result['original_blade_operator'] = '<='
        # Pattern: 元々持つ{{icon_blade.png|ブレード}}の数が4つ以上
        original_blade_match = re.search(r'元々持つ.*?ブレード.*?(\d+)つ以上', text)
        if original_blade_match:
            result['original_blade_count'] = _normalized_int(original_blade_match.group(1))
            result['original_blade_operator'] = '>='

    # Extract heart type for gain_resource actions
    if result.get('action') == 'gain_resource':
        if '{{icon_all.png|ハート}}' in text:
            result['heart_type'] = 'all'
        elif '{{icon_any.png|ハート}}' in text:
            result['heart_type'] = 'any'
        elif '{{heart_' in text:
            heart_types = extract_heart_types(text)
            if heart_types:
                result['heart_types'] = heart_types

    # Global opponent targeting check - ensure all actions targeting opponent have target field
    if 'target' not in result:
        if '相手のステージ' in text or '相手の' in text:
            result['target'] = 'opponent'
        elif '自分のステージ' in text or '自分の' in text:
            result['target'] = 'self'

    if not result:
        result['raw_text'] = text
    
    return result

def parse_effect_context_backwards(context):
    """Parse context backwards to extract variables using utility functions."""
    variables = {}
    # ... (rest of the code remains the same)
    
    # Extract target (self/opponent/both)
    target = _extract_condition_target(context)
    if target:
        variables['target'] = target
    
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
    if ('自分の' in context and '相手の' in context) or '自分と相手' in context or '自分と相手の' in context:
        variables['target'] = 'both'
    elif 'そのプレイヤー' in context:
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

@_annotate_return
def parse_conditional_effect(text):
    """Parse conditional effect with condition marker."""
    result = {}
    text = text.strip()

    # Specific "choose a player, put a card on the bottom of that player's deck, then draw"
    # pattern. This needs to be handled before the generic conditional split so
    # "そうした場合" doesn't get treated as a standalone condition fragment.
    if (
        '自分か相手を選ぶ' in text
        and 'そのプレイヤーの控え室にあるライブカードを1枚' in text
        and 'そのプレイヤーのデッキの一番下に置く' in text
        and 'そうした場合' in text
        and 'カードを1枚引く' in text
    ):
        choice_text = text
        if '自分か相手を選ぶ' in choice_text and '：' in choice_text and choice_text.index('：') < choice_text.index('自分か相手を選ぶ'):
            choice_text = choice_text.split('：', 1)[1].strip()
        choice_text = choice_text.replace('自分か相手を選ぶ。', '', 1).replace('自分か相手を選ぶ', '', 1).strip()
        first_part, second_part = choice_text.split('そうした場合', 1)
        result['choice'] = True
        result['options'] = ['self', 'opponent']
        result['actions'] = [
            {
                'action': 'place_card',
                'source': 'waitroom',
                'target': 'selected_player',
                'destination': 'deck_bottom',
                'card_type': 'live_card',
                'count': 1,
                'text': first_part.strip('。 、'),
            }
        ]
        second_action = parse_effect_backwards(second_part.strip('。 、'))
        if _is_parsed_action(second_action):
            result['actions'].append(second_action)
        else:
            result['actions'].append(_raw_text(second_part.strip('。 、')))
        return result

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
            inferred_first = {}
            if isinstance(first_action, dict):
                inferred_first.update({k: v for k, v in first_action.items() if k != 'raw_text'})
            if 'デッキの一番下に置く' in first_part or 'デッキの下に置く' in first_part:
                inferred_first.setdefault('action', 'place_card')
                inferred_first.setdefault('destination', 'deck_bottom')
                if 'ライブカード' in first_part:
                    inferred_first.setdefault('card_type', 'live_card')
                elif 'メンバーカード' in first_part:
                    inferred_first.setdefault('card_type', 'member_card')
                elif 'エネルギーカード' in first_part:
                    inferred_first.setdefault('card_type', 'energy_card')
                if '1枚' in first_part and 'count' not in inferred_first:
                    inferred_first['count'] = 1
                if 'そのプレイヤー' in first_part:
                    inferred_first.setdefault('target', 'selected_player')
                elif '相手' in first_part:
                    inferred_first.setdefault('target', 'opponent')
                elif '自分' in first_part:
                    inferred_first.setdefault('target', 'self')
                if 'source' not in inferred_first and '控え室' in first_part:
                    inferred_first['source'] = 'waitroom'
                result['actions'].append(inferred_first if inferred_first else _raw_text(first_part.strip('。 、')))
            else:
                result['actions'].append(_raw_text(first_part.strip('。 、')))
        second_action = parse_effect_backwards(second_part.strip('。 、'))
        if _is_parsed_action(second_action):
            if (
                isinstance(first_action, dict)
                and first_action.get('target') == 'selected_player'
                and second_action.get('action') in {'may_place_card', 'place_card', 'discard_to_waitroom'}
                and 'target' not in second_action
                and ('そのカード' in second_part or 'そのプレイヤー' in second_part)
            ):
                second_action['target'] = 'selected_player'
                if second_action.get('action') in {'may_place_card', 'place_card'} and 'source' not in second_action:
                    second_action['source'] = 'looked_at_cards'
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
        if marker == '場合' and 'そうした場合' in text:
            continue
        if marker in text:
            parts = text.split(marker, 1)
            if len(parts) != 2:
                continue

            condition_part = parts[0].strip()
            action_part = parts[1].strip().lstrip('、')

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


@_annotate_return
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
    leading_context = {}
    if first_part != original_first_part:
        if 'source' in result:
            leading_context['source'] = result.pop('source')
        if 'location' in result:
            leading_context['location'] = result.pop('location')
        if not first_part:
            parsed_second = parse_effect_backwards(second_part)
            if _is_parsed_action(parsed_second):
                parsed_second.update(leading_context)
                result['actions'].append(parsed_second)
            else:
                raw_second = _raw_text(second_part)
                raw_second.update(leading_context)
                result['actions'].append(raw_second)
            return result
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

@_annotate_return
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

@_annotate_return
def parse_generic_effect(text):
    """Parse generic effect when no specific pattern matches."""
    result = {}
    
    # Remove leading/trailing whitespace
    text = text.strip()
    original_text = text

    # Check for multi-branch cost total pattern BEFORE period split
    # This pattern spans multiple sentences and needs to be handled as a unit
    cost_total_match = re.search(r'(それらのカード|公開したカード|それら)のコストの合計', text)
    if cost_total_match:
        # Extract all cost-value branches
        branches = []
        # Pattern for single value: "Xの場合、Y" or "合計がXの場合、Y"
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
            result['condition'] = {
                'type': 'cost_total_equal',
                'reference': cost_total_match.group(1),
            }
            result['cost_reference'] = True
            result['branches'] = branches
            result['text'] = text
            return result

    # Specific "choose a player, place a live card from that player's waitroom on the bottom
    # of that player's deck, then draw" pattern.
    if (
        '自分か相手を選ぶ' in text
        and 'そのプレイヤーの控え室にあるライブカードを1枚' in text
        and 'そのプレイヤーのデッキの一番下に置く' in text
        and 'そうした場合' in text
        and 'カードを1枚引く' in text
    ):
        choice_text = text.replace('自分か相手を選ぶ。', '', 1).replace('自分か相手を選ぶ', '', 1).strip()
        first_part, second_part = choice_text.split('そうした場合', 1)
        result['choice'] = True
        result['options'] = ['self', 'opponent']
        result['actions'] = [{
            'action': 'place_card',
            'source': 'waitroom',
            'target': 'selected_player',
            'destination': 'deck_bottom',
            'card_type': 'live_card',
            'count': 1,
            'text': first_part.strip('。 、'),
        }]
        second_action = parse_effect_backwards(second_part.strip('。 、'))
        if _is_parsed_action(second_action):
            result['actions'].append(second_action)
        else:
            result['actions'].append(_raw_text(second_part.strip('。 、')))
        result['text'] = text
        return result

    sentence_parts = [sentence.strip() for sentence in text.split('。') if sentence.strip()]
    if len(sentence_parts) >= 2:
        leading_condition_markers = ('場合', 'とき', 'かぎり', 'なら')
        if (
            any(marker in sentence_parts[0] for marker in leading_condition_markers)
            and any(marker in sentence_parts[1] for marker in leading_condition_markers)
            and 'そうした場合' not in text
        ):
            parsed_sentences = []
            for sentence in sentence_parts[:2]:
                parsed = parse_effect_backwards(sentence)
                if _is_parsed_action(parsed):
                    parsed_sentences.append(parsed)
            if len(parsed_sentences) >= 2:
                result['actions'] = parsed_sentences
                result['text'] = text
                return result

    if '無効にしてもよい' in text and 'これにより無効にした場合' in text:
        sentences = text.split('。')
        sentences = [s.strip() for s in sentences if s.strip()]
        if len(sentences) >= 2:
            first_sentence = sentences[0]
            second_sentence = sentences[1]
            result['actions'] = []
            invalidate_action = {
                'action': 'invalidate_ability',
                'target': 'selected_member',
                'optional': True,
                'duration': 'until_end_of_live' if 'ライブ終了時まで' in first_sentence else None,
                'ability_scope': 'live_start' if 'ライブ開始時' in first_sentence else None,
                'source': 'stage' if '自分のステージ' in first_sentence else None,
                'count': 1,
            }
            group = extract_group_name(first_sentence)
            if group:
                invalidate_action['group'] = group
            result['actions'].append({key: value for key, value in invalidate_action.items() if value is not None})
            conditional_text = second_sentence.replace('これにより無効にした場合', '').replace('これにより無効にした', '').strip()
            conditional_action = parse_effect_backwards(conditional_text)
            if _is_parsed_action(conditional_action):
                conditional_action['conditional'] = True
                result['actions'].append(conditional_action)
            else:
                conditional_raw = _raw_text(conditional_text)
                conditional_raw['conditional'] = True
                result['actions'].append(conditional_raw)
            return result

    if 'これによりライブカードを控え室に置いた場合' in text and 'ライブ終了時まで、{{icon_blade.png|ブレード}}を得る' in text:
        sentences = [sentence.strip() for sentence in text.split('。') if sentence.strip()]
        if len(sentences) >= 2:
            result['actions'] = []
            gain_action = parse_effect_backwards(sentences[0])
            if _is_parsed_action(gain_action):
                result['actions'].append(gain_action)
            else:
                result['actions'].append(_raw_text(sentences[0]))

            follow_up = sentences[1]
            follow_match = re.search(r'これによりライブカードを控え室に置いた場合、?(.+)', follow_up)
            follow_text = follow_match.group(1).strip() if follow_match else follow_up
            draw_action = parse_effect_backwards(follow_text)
            if _is_parsed_action(draw_action):
                draw_action['conditional'] = True
                draw_action['condition'] = {
                    'type': 'discarded_card',
                    'value': 'live_card',
                    'location': 'waitroom',
                    'target': 'self',
                    'text': 'これによりライブカードを控え室に置いた場合',
                }
                result['actions'].append(draw_action)
            else:
                result['actions'].append(
                    {
                        'raw_text': follow_text,
                        'conditional': True,
                        'condition': {
                            'type': 'discarded_card',
                            'value': 'live_card',
                            'location': 'waitroom',
                            'target': 'self',
                            'text': 'これによりライブカードを控え室に置いた場合',
                        },
                    }
                )
            return result

    # Check for relative-cost adjustment + follow-up reward pattern.
    # Example: "自分のステージにいる『DOLLCHESTRA』のメンバー1人を選ぶ。ライブ終了時まで、このメンバーのコストは、
    # 選んだメンバーが元々持つコストより1低い値に等しくなる。これによりこのカードのコストが10以上になった場合、
    # ライブ終了時まで、{{heart_05.png|heart05}}を得る。"
    if '選んだメンバーが元々持つコストより' in text and 'このカードのコストが' in text and 'ライブ終了時まで、{{heart_' in text:
        sentences = [sentence.strip() for sentence in text.split('。') if sentence.strip()]
        if len(sentences) >= 3:
            result['actions'] = []

            select_match = re.search(r'自分のステージにいる(.+?)メンバー1人を選ぶ', sentences[0])
            select_text = sentences[0]
            if select_match:
                select_action = _select_member_action(select_text, target='self')
                if select_action.get('group') is None:
                    group = extract_group_name(select_text)
                    if group:
                        select_action['group'] = group
                result['actions'].append(select_action)
            else:
                select_action = parse_effect_backwards(select_text)
                if _is_parsed_action(select_action):
                    result['actions'].append(select_action)
                else:
                    result['actions'].append(_raw_text(select_text))

            modify_match = re.search(
                r'このメンバーのコストは、?選んだメンバーが元々持つコストより([\d０-９]+)低い値に等しくなる',
                sentences[1],
            )
            if modify_match:
                result['actions'].append(
                    {
                        'action': 'modify_cost',
                        'target': 'this_member',
                        'source': 'selected_member_original_cost',
                        'reference': 'selected_member',
                        'reference_mode': 'relative_cost',
                        'operator': '-',
                        'amount': _normalized_int(modify_match.group(1)),
                        'duration': 'until_end_of_live',
                        'text': sentences[1],
                    }
                )
            else:
                modify_action = parse_effect_backwards(sentences[1])
                if _is_parsed_action(modify_action):
                    result['actions'].append(modify_action)
                else:
                    result['actions'].append(_raw_text(sentences[1]))

            reward_text = sentences[2]
            reward_match = re.search(r'これによりこのカードのコストが([\d０-９]+)以上になった場合、?(.+)', reward_text)
            if reward_match:
                reward_condition_text = reward_match.group(0).split('、', 1)[0].rstrip('。').strip()
                reward_effect_text = reward_match.group(2).rstrip('。').strip()
                reward_condition = {
                    'type': 'cost_at_least',
                    'target': 'this_card',
                    'value': _normalized_int(reward_match.group(1)),
                    'compares': 'card_cost',
                    'text': reward_condition_text,
                }
                reward_action = parse_effect_backwards(reward_effect_text)
                if _is_parsed_action(reward_action):
                    reward_action['conditional'] = True
                    reward_action['condition'] = reward_condition
                    reward_action['text'] = reward_effect_text
                    result['actions'].append(reward_action)
                else:
                    result['actions'].append(
                        {
                            'raw_text': reward_effect_text,
                            'conditional': True,
                            'condition': reward_condition,
                            'text': reward_effect_text,
                        }
                    )
            else:
                reward_action = parse_effect_backwards(reward_text)
                if _is_parsed_action(reward_action):
                    result['actions'].append(reward_action)
                else:
                    result['actions'].append(_raw_text(reward_text))
            return result

    # Check for "その中から...デッキの上に置き、残りを控え室に置く" pattern
    # This is a complex multi-step action: look at cards, place some on deck, discard rest
    if 'その中から' in text and '手札に加え' in text and '残りを控え室に置く' in text:
        result['actions'] = []
        look_match = re.search(r'カードを([\d０-９]+)枚見る', text)
        if look_match:
            result['actions'].append({
                'action': 'look_at_cards',
                'count': _normalized_int(look_match.group(1)),
                'source': 'deck_top',
            })
        add_match = re.search(r'([\d０-９]+)枚まで公開して手札に加え', text)
        add_count = _normalized_int(add_match.group(1)) if add_match else 1
        add_action = {
            'action': 'add_to_hand',
            'count': add_count,
            'source': 'looked_at_cards',
            'may': 'もよい' in text or '公開して手札に加えてもよい' in text,
            'reveal': True,
        }
        if 'メンバーカード' in text:
            add_action['card_type'] = 'member_card'
        elif 'ライブカード' in text:
            add_action['card_type'] = 'live_card'
        else:
            add_action['card_type'] = 'card'
        heart_types = extract_heart_types(text)
        if heart_types:
            add_action['selection'] = {
                'heart_types': heart_types,
                'operator': 'or',
            }
        result['actions'].append(add_action)
        result['actions'].append({
            'action': 'discard_to_waitroom',
            'source': 'looked_at_cards',
        })
        return result

    if 'その中から' in text and 'メンバーカード' in text and '公開して手札に加えてもよい' in text:
        result['actions'] = []
        look_match = re.search(r'カードを([\d０-９]+)枚見る', text)
        if look_match:
            result['actions'].append({
                'action': 'look_at_cards',
                'count': _normalized_int(look_match.group(1)),
                'source': 'deck_top',
            })
        add_match = re.search(r'(?:{0})?([\d０-９]+)枚まで公開して手札に加えてもよい'.format(''), text)
        add_count = _normalized_int(add_match.group(1)) if add_match else 3
        add_action = {
            'action': 'add_to_hand',
            'count': add_count,
            'source': 'looked_at_cards',
            'may': True,
            'reveal': True,
            'card_type': 'member_card',
        }
        heart_types = extract_heart_types(text)
        if heart_types:
            add_action['selection'] = {
                'heart_types': heart_types,
                'operator': 'or',
            }
        result['actions'].append(add_action)
        result['actions'].append({
            'action': 'discard_to_waitroom',
            'source': 'looked_at_cards',
        })
        return result

    if 'その中から' in text and 'デッキの上に置き' in text and '残りを控え室に置く' in text:
        result['actions'] = []
        # Extract look_at_cards count if present in the same text
        look_match = re.search(r'カードを(\d+)枚見る', text)
        if look_match:
            result['actions'].append({
                'action': 'look_at_cards',
                'count': int(look_match.group(1)),
                'source': 'deck_top'
                ,
                'text': text.split('。', 1)[0].strip()
            })
        result['actions'].append({
            'action': 'select_from_looked_at_cards',
            'source': 'looked_at_cards',
            'selection': {
                'up_to': True,
                'order': 'any',
            },
            'text': 'その中から好きな枚数を好きな順番で'
        })
        result['actions'].append({
            'action': 'place_on_deck',
            'destination': 'deck_top',
            'source': 'selected_cards',
            'text': 'デッキの上に置き'
        })
        result['actions'].append({
            'action': 'discard_to_waitroom',
            'source': 'remaining_looked_at_cards',
            'text': '残りを控え室に置く'
        })
        return result

    # Check for "その後" sequential action pattern across period-separated sentences
    if 'その後' in text and '。' in text:
        # Split by period to get sentences
        sentences = text.split('。')
        sentences = [s.strip() for s in sentences if s.strip()]
        if len(sentences) >= 2:
            # Check if second sentence starts with "その後"
            if sentences[1].startswith('その後'):
                # Check for area selection pattern (若菜四季 case)
                if '登場したエリアとは別の自分のエリア1つを選ぶ' in sentences[1]:
                    result['actions'] = []
                    # Parse first sentence
                    first_action = parse_effect_backwards(sentences[0])
                    if _is_parsed_action(first_action):
                        result['actions'].append(first_action)
                    else:
                        result['actions'].append(_raw_text(sentences[0]))
                    
                    # Parse area selection and movement
                    second_text = sentences[1].replace('その後', '').strip()
                    # Split on period to separate area selection from movement
                    if '。' in second_text:
                        area_part, move_part = second_text.split('。', 1)
                        result['actions'].append({
                            'action': 'select_area',
                            'source': 'stage',
                            'exclude': 'deployed_area',
                            'count': 1,
                            'target': 'self'
                        })
                        move_action = parse_effect_backwards(move_part.strip())
                        if _is_parsed_action(move_action):
                            result['actions'].append(move_action)
                        else:
                            result['actions'].append(_raw_text(move_part.strip()))
                    else:
                        # Treat as single complex action
                        second_action = parse_effect_backwards(second_text)
                        if _is_parsed_action(second_action):
                            result['actions'].append(second_action)
                        else:
                            result['actions'].append(_raw_text(second_text))
                    return result
                
                # Default "その後" handling
                result['actions'] = []
                # Parse first sentence
                first_action = parse_effect_backwards(sentences[0])
                if _is_parsed_action(first_action):
                    result['actions'].append(first_action)
                else:
                    result['actions'].append(_raw_text(sentences[0]))
                # Parse second sentence (remove "その後" prefix)
                second_text = sentences[1].replace('その後', '').strip()
                second_action = parse_effect_backwards(second_text)
                if _is_parsed_action(second_action):
                    result['actions'].append(second_action)
                else:
                    result['actions'].append(_raw_text(second_text))
                return result


    # Check for complex trigger with payment pattern (e.g., "～たび、{{icon_energy.png|E}}支払ってもよい。そうした場合、～")
    if 'たび、{{icon_energy' in text and '支払ってもよい。そうした場合' in text:
        result['actions'] = []
        # Split on period to separate trigger/payment from conditional action
        sentences = text.split('。')
        sentences = [s.strip() for s in sentences if s.strip()]
        if len(sentences) >= 2:
            # Parse trigger and payment (first sentence)
            first_sentence = sentences[0]
            # Extract trigger condition
            trigger_match = re.search(r'(自分のメインフェイズの間、)?自分のカードが(\d+)枚以上いずれかの領域から控え室に置かれる', first_sentence)
            if trigger_match:
                trigger_condition_text = first_sentence.replace('自分のメインフェイズの間、', '').strip()
                trigger_condition = parse_condition(trigger_condition_text)
                if not trigger_condition or trigger_condition.get('type') == 'raw':
                    trigger_condition = trigger_condition_text
                trigger_action = {
                    'action': 'whenever_trigger',
                    'condition': trigger_condition
                }
                if trigger_match.group(1):
                    trigger_action['timing'] = '自分のメインフェイズの間'
                result['actions'].append(trigger_action)
            
            # Extract optional energy payment
            payment_match = re.search(r'{{icon_energy\.png\|E}}支払ってもよい', first_sentence)
            if payment_match:
                result['actions'].append({
                    'action': 'pay_energy',
                    'optional': True,
                    'count': 1
                })
            
            # Parse conditional action (second sentence, remove "そうした場合" prefix)
            conditional_text = sentences[1].replace('そうした場合', '').strip()
            conditional_action = parse_effect_backwards(conditional_text)
            if _is_parsed_action(conditional_action):
                conditional_action['conditional'] = True
                result['actions'].append(conditional_action)
            else:
                conditional_raw = _raw_text(conditional_text)
                conditional_raw['conditional'] = True
                result['actions'].append(conditional_raw)
            return result

    # Check for card selection by name with opponent selection pattern (e.g., "～カード名が異なるライブカードを2枚選ぶ。そうした場合、相手はそれらのカードのうち1枚を選ぶ。これにより相手に選ばれたカードを～")
    if ('カード名が異なる' in text or 'カード名の異なる' in text or '、カード名が異なる' in text or '、カード名の異なる' in text) and '選ぶ' in text and 'そうした場合、相手' in text:
        result['actions'] = []
        # Split on period to separate selection from opponent selection
        sentences = text.split('。')
        sentences = [s.strip() for s in sentences if s.strip()]
        if len(sentences) >= 2:
            # Parse card selection (first sentence)
            first_sentence = sentences[0]
            select_match = re.search(r'(自分の控え室にある)?カード名(?:が|の)異なる(ライブカード|メンバーカード)を(\d+)\s*枚選ぶ', first_sentence)
            if select_match:
                source = 'waitroom' if '控え室' in first_sentence else None
                card_type = 'live_card' if 'ライブカード' in select_match.group(2) else ('member_card' if 'メンバーカード' in select_match.group(2) else None)
                result['actions'].append({
                    'action': 'select_card',
                    'source': source,
                    'card_type': card_type,
                    'count': int(select_match.group(3)),
                    'selection_criteria': 'different_names'
                })
            else:
                fallback_select = _raw_text(first_sentence)
                fallback_select['action'] = 'select_card'
                result['actions'].append(fallback_select)
            
            # Parse opponent selection (second sentence)
            second_sentence = sentences[1]
            opponent_select_part = second_sentence.split('。')[0] if '。' in second_sentence else second_sentence
            result['actions'].append({
                'action': 'opponent_selects',
                'from': 'selected_cards',
                'count': 1,
                'target': 'opponent'
            })
            
            # Parse final action (third sentence if exists)
            if len(sentences) >= 3:
                final_part = sentences[2]
                final_action = parse_effect_backwards(final_part)
                if _is_parsed_action(final_action):
                    final_action['source'] = 'opponent_selected_card'
                    final_action['target'] = 'self'
                    final_action['count'] = 1
                    final_action.setdefault('card_type', card_type or 'card')
                    result['actions'].append(final_action)
                else:
                    fallback_final = _raw_text(final_part)
                    fallback_final['action'] = 'add_to_hand'
                    fallback_final['source'] = 'opponent_selected_card'
                    fallback_final['target'] = 'self'
                    fallback_final['count'] = 1
                    fallback_final['card_type'] = card_type or 'card'
                    result['actions'].append(fallback_final)
            return result

    # Check for card selection with variable payment pattern (e.g., "～ライブカードを1枚選び、そのカードのスコアに等しい数の{{icon_energy.png|E}}を支払ってもよい。そうした場合、～")
    if '選び、そのカードのスコアに等しい数の' in text and '支払ってもよい。そうした場合' in text:
        result['actions'] = []
        # Split on period to separate selection/payment from conditional action
        sentences = text.split('。')
        sentences = [s.strip() for s in sentences if s.strip()]
        if len(sentences) >= 2:
            # Parse selection and payment (first sentence)
            first_sentence = sentences[0]
            # Extract card selection
            select_match = re.search(r'(自分の控え室にある|自分の)?(ライブカード|メンバーカード)を(\d+)枚選び', first_sentence)
            if select_match:
                source = 'waitroom' if '控え室' in first_sentence else None
                card_type = 'live_card' if 'ライブカード' in select_match.group(2) else ('member_card' if 'メンバーカード' in select_match.group(2) else None)
                result['actions'].append({
                    'action': 'select_card',
                    'source': source,
                    'card_type': card_type,
                    'count': int(select_match.group(3))
                })
            else:
                result['actions'].append(_raw_text(first_sentence))
            
            # Extract variable payment
            payment_match = re.search(r'そのカードのスコアに等しい数の{{icon_energy\.png\|E}}を支払ってもよい', first_sentence)
            if payment_match:
                result['actions'].append({
                    'action': 'pay_energy',
                    'optional': True,
                    'amount': 'selected_card_score'
                })
            
            # Parse conditional action (second sentence, remove "そうした場合" prefix)
            conditional_text = sentences[1].replace('そうした場合', '').strip()
            conditional_action = parse_effect_backwards(conditional_text)
            if _is_parsed_action(conditional_action):
                conditional_action['conditional'] = True
                if conditional_action.get('action') == 'add_to_hand' and 'count' not in conditional_action:
                    conditional_action['count'] = 1
                if conditional_action.get('action') == 'add_to_hand' and 'card_type' not in conditional_action:
                    conditional_action['card_type'] = card_type or 'live_card'
                result['actions'].append(conditional_action)
            else:
                conditional_raw = _raw_text(conditional_text)
                conditional_raw['conditional'] = True
                conditional_raw['count'] = 1
                conditional_raw['card_type'] = card_type or 'live_card'
                result['actions'].append(conditional_raw)
            return result

    # Check for optional draw with conditional follow-up pattern (e.g., "カードを1枚引いてもよい。そうした場合、～")
    if '引いてもよい。そうした場合' in text:
        result['actions'] = []
        # Split on period to separate optional draw from conditional action
        sentences = text.split('。')
        sentences = [s.strip() for s in sentences if s.strip()]
        if len(sentences) >= 2:
            # Parse optional draw (first sentence)
            draw_match = re.search(r'カードを(\d+)枚引いてもよい', sentences[0])
            if draw_match:
                result['actions'].append({
                    'action': 'draw_cards',
                    'count': int(draw_match.group(1)),
                    'optional': True
                })
            else:
                result['actions'].append(_raw_text(sentences[0]))
            # Parse conditional action (second sentence, remove "そうした場合" prefix)
            conditional_text = sentences[1].replace('そうした場合', '').strip()
            conditional_action = parse_effect_backwards(conditional_text)
            if _is_parsed_action(conditional_action):
                conditional_action['conditional'] = True
                result['actions'].append(conditional_action)
            else:
                conditional_raw = _raw_text(conditional_text)
                conditional_raw['conditional'] = True
                result['actions'].append(conditional_raw)
            return result

    # Check for opponent's optional action pattern (e.g., "相手は～してもよい。そうしなかった場合、～")
    if '相手は' in text and 'してもよい' in text and ('そうしなかった場合' in text or 'そうしなかった' in text):
        result['actions'] = []
        # Split on period to separate opponent's action from conditional effect
        sentences = text.split('。')
        sentences = [s.strip() for s in sentences if s.strip()]
        if len(sentences) >= 2:
            # Parse opponent's optional action (first sentence)
            opponent_action = parse_effect_backwards(sentences[0])
            if _is_parsed_action(opponent_action):
                opponent_action['target'] = 'opponent'
                opponent_action['optional'] = True
                result['actions'].append(opponent_action)
            else:
                opponent_raw = _raw_text(sentences[0])
                opponent_raw['target'] = 'opponent'
                opponent_raw['optional'] = True
                result['actions'].append(opponent_raw)
            # Parse conditional effect (second sentence, remove "そうしなかった場合" prefix)
            conditional_text = sentences[1].replace('そうしなかった場合', '').replace('そうしなかった', '').strip()
            # Check for duration prefix
            if conditional_text.startswith('、'):
                conditional_text = conditional_text[1:].strip()
            if conditional_text.startswith('ライブ終了時まで、'):
                result['duration'] = 'until_end_of_live'
                conditional_text = conditional_text.replace('ライブ終了時まで、', '').strip()
            conditional_action = parse_effect_backwards(conditional_text)
            if _is_parsed_action(conditional_action):
                conditional_action['conditional'] = True
                conditional_action['condition'] = 'opponent_did_not_act'
                result['actions'].append(conditional_action)
            else:
                conditional_raw = _raw_text(conditional_text)
                conditional_raw['conditional'] = True
                conditional_raw['condition'] = 'opponent_did_not_act'
                result['actions'].append(conditional_raw)
            return result

    # Check for opponent's optional action pattern without "場合" (e.g., "相手は～してもよい。そうしなかった、～")
    if '相手は' in text and 'してもよい' in text and 'そうしなかった、' in text:
        result['actions'] = []
        # Split on period to separate opponent's action from conditional effect
        sentences = text.split('。')
        sentences = [s.strip() for s in sentences if s.strip()]
        if len(sentences) >= 2:
            # Parse opponent's optional action (first sentence)
            opponent_action = parse_effect_backwards(sentences[0])
            if _is_parsed_action(opponent_action):
                opponent_action['target'] = 'opponent'
                opponent_action['optional'] = True
                result['actions'].append(opponent_action)
            else:
                opponent_raw = _raw_text(sentences[0])
                opponent_raw['target'] = 'opponent'
                opponent_raw['optional'] = True
                result['actions'].append(opponent_raw)
            # Parse conditional effect (second sentence, remove "そうしなかった、" prefix)
            conditional_text = sentences[1].replace('そうしなかった、', '').strip()
            # Check for duration prefix
            if conditional_text.startswith('ライブ終了時まで、'):
                result['duration'] = 'until_end_of_live'
                conditional_text = conditional_text.replace('ライブ終了時まで、', '').strip()
            conditional_action = parse_effect_backwards(conditional_text)
            if _is_parsed_action(conditional_action):
                conditional_action['conditional'] = True
                conditional_action['condition'] = 'opponent_did_not_act'
                result['actions'].append(conditional_action)
            else:
                conditional_raw = _raw_text(conditional_text)
                conditional_raw['conditional'] = True
                conditional_raw['condition'] = 'opponent_did_not_act'
                result['actions'].append(conditional_raw)
            return result

    # Check for "そうした場合" conditional follow-up action pattern
    if 'そうした場合' in text and '。' in text:
        # Split by period to get sentences
        sentences = text.split('。')
        sentences = [s.strip() for s in sentences if s.strip()]
        if len(sentences) >= 2:
            # Check if second sentence starts with "そうした場合"
            if sentences[1].startswith('そうした場合'):
                result['actions'] = []
                # Parse first sentence
                first_action = parse_effect_backwards(sentences[0])
                if _is_parsed_action(first_action):
                    result['actions'].append(first_action)
                else:
                    result['actions'].append(_raw_text(sentences[0]))
                # Parse second sentence (remove "そうした場合" prefix)
                second_text = sentences[1].replace('そうした場合', '').strip()
                second_action = parse_effect_backwards(second_text)
                if _is_parsed_action(second_action):
                    second_action['conditional'] = True
                    result['actions'].append(second_action)
                else:
                    conditional_raw = _raw_text(second_text)
                    conditional_raw['conditional'] = True
                    result['actions'].append(conditional_raw)
                # Merge modifier-only actions with their target actions
                result['actions'] = _merge_modifier_actions(result['actions'])
                return result

    # Check for heart cost modification pattern (e.g., "必要ハートは...のうち、選んだ1つにしてもよい")
    if '必要ハートは' in text and 'のうち、選んだ1つにしてもよい' in text:
        # Check if there's a condition before the heart cost modification
        if '場合' in text:
            # Split on '場合' to separate condition from action
            parts = text.split('場合', 1)
            if len(parts) == 2:
                condition_part = parts[0] + '場合'
                action_part = parts[1].strip()
                # Parse condition
                condition = parse_condition(condition_part)
                if condition and condition.get('type') != 'raw':
                    result['condition'] = condition
                # Parse action
                result['action'] = 'heart_cost_modifier'
                result['optional'] = True
                # Extract heart options
                heart_options = []
                heart_matches = re.findall(r'{{heart_(\d+)\.png\|heart\d+}}', action_part)
                if heart_matches:
                    # Group hearts into options (3 hearts per option based on pattern)
                    for i in range(0, len(heart_matches), 3):
                        if i + 3 <= len(heart_matches):
                            heart_options.append(heart_matches[i:i+3])
                result['heart_options'] = heart_options
                return result
        # Fallback: parse without condition
        result['action'] = 'heart_cost_modifier'
        result['optional'] = True
        # Extract heart options
        heart_options = []
        heart_matches = re.findall(r'{{heart_(\d+)\.png\|heart\d+}}', text)
        if heart_matches:
            # Group hearts into options (3 hearts per option based on pattern)
            for i in range(0, len(heart_matches), 3):
                if i + 3 <= len(heart_matches):
                    heart_options.append(heart_matches[i:i+3])
        result['heart_options'] = heart_options
        return result

    # Check for activation restriction pattern (e.g., "この能力は、このカードが控え室にある場合のみ起動できる")
    if 'この能力は' in text and '起動できる' in text:
        # Split on period to separate effect from activation restriction
        sentences = text.split('。')
        sentences = [s.strip() for s in sentences if s.strip()]
        if len(sentences) >= 2:
            # Parse the effect (first sentence)
            effect_action = parse_effect_backwards(sentences[0])
            if _is_parsed_action(effect_action):
                result['action'] = effect_action
            else:
                result['action'] = _raw_text(sentences[0])
            # Add activation restriction
            result['activation_restriction'] = 'only_this_card'
            return result

    # Check for opponent's optional action pattern (e.g., "相手は～してもよい。そうしなかった場合、～")
    if '相手は' in text and 'してもよい' in text and ('そうしなかった場合' in text or 'そうしなかった' in text):
        result['actions'] = []
        # Split on period to separate opponent's action from conditional effect
        sentences = text.split('。')
        sentences = [s.strip() for s in sentences if s.strip()]
        if len(sentences) >= 2:
            # Parse opponent's optional action (first sentence)
            opponent_action = parse_effect_backwards(sentences[0])
            if _is_parsed_action(opponent_action):
                opponent_action['target'] = 'opponent'
                opponent_action['optional'] = True
                result['actions'].append(opponent_action)
            else:
                opponent_raw = _raw_text(sentences[0])
                opponent_raw['target'] = 'opponent'
                opponent_raw['optional'] = True
                result['actions'].append(opponent_raw)
            # Parse conditional effect (second sentence, remove "そうしなかった場合" prefix)
            conditional_text = sentences[1].replace('そうしなかった場合', '').replace('そうしなかった', '').strip()
            conditional_action = parse_effect_backwards(conditional_text)
            if _is_parsed_action(conditional_action):
                conditional_action['conditional'] = True
                conditional_action['condition'] = 'opponent_did_not_act'
                result['actions'].append(conditional_action)
            else:
                conditional_raw = _raw_text(conditional_text)
                conditional_raw['conditional'] = True
                conditional_raw['condition'] = 'opponent_did_not_act'
                result['actions'].append(conditional_raw)
            return result

    # Check for cost-total conditional pattern (e.g., "それらのカードのコストの合計が、6の場合")
    # This handles effects that branch based on the total cost of cards placed in the cost
    cost_total_match = re.search(r'(それらのカード|公開したカード|それら)のコストの合計', text)
    if cost_total_match:
        result['condition'] = {
            'type': 'cost_total_equal',
            'reference': cost_total_match.group(1),  # "それらのカード" or "公開したカード"
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
                if (
                    action.get('action') in {'may_place_card', 'place_card', 'discard_to_waitroom'}
                    and 'そのカード' in action_part
                    and any(existing.get('target') == 'selected_player' for existing in result['actions'])
                ):
                    action['target'] = 'selected_player'
                    if action.get('action') in {'may_place_card', 'place_card'} and 'source' not in action:
                        action['source'] = 'looked_at_cards'
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
    
    # Check for "～かぎり" (as long as) condition pattern before action
    kagiri_match = re.search(r'(.+?)かぎり、(.+)', text)
    if kagiri_match:
        condition_text = kagiri_match.group(1).strip()
        action_text = kagiri_match.group(2).strip()
        _assign_condition(result, condition_text)
        text = action_text  # Continue parsing the action part
    
    # Check for cost reduction pattern (e.g., "コストは1減る", "手札にあるこのメンバーカードのコストは2減る")
    cost_reduction_match = re.search(r'コスト[はが](\d+)減る', text)
    if cost_reduction_match:
        result['action'] = {
            'action': 'reduce_cost',
            'amount': int(cost_reduction_match.group(1))
        }
        # Check if it's hand-based reduction
        if '手札' in text:
            result['source'] = 'hand'
        return result

    # Check for resource-specific reduction pattern (e.g., "{{icon_energy.png|E}}減る")
    if '{{icon_energy.png|E}}' in text and '減る' in text:
        energy_count = text.count('{{icon_energy.png|E}}') or 1
        result['action'] = {
            'action': 'reduce_cost',
            'resource': 'energy',
            'amount': energy_count,
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
        # Don't remove from text - let condition parser handle it
    
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
        # Check for score buff pattern with any numeric value
        score_match = re.search(r'スコアを\+([０-９\d]+)する', text)
        if score_match:
            amount = int(score_match.group(1).translate(str.maketrans("０１２３４５６７８９", "0123456789")))
            result['actions'].append({'action': 'add_score', 'amount': amount})
        elif 'スコアを+１する' in text or 'スコアを+1する' in text:
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
                        if (
                            len(result['actions']) >= 1
                            and result['actions'][-1].get('target') == 'selected_player'
                            and action.get('action') in {'may_place_card', 'place_card', 'discard_to_waitroom'}
                            and 'target' not in action
                            and ('そのカード' in action_part or 'そのプレイヤー' in action_part)
                        ):
                            action['target'] = 'selected_player'
                            if action.get('action') in {'may_place_card', 'place_card'} and 'source' not in action:
                                action['source'] = 'looked_at_cards'
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
                    'until_condition': f'{condition_text}なるまで'
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
                    'until_condition': f'{condition_text}なるまで'
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
            # Check if marker is inside parentheses (parenthetical note) - if so, skip
            # Find the position of the marker
            marker_pos = text.find(marker)
            # Check if there's an opening parenthesis before the marker without a closing parenthesis
            last_open_paren_before_marker = max(text.rfind('（', 0, marker_pos), text.rfind('(', 0, marker_pos))
            last_close_paren_before_marker = max(text.rfind('）', 0, marker_pos), text.rfind(')', 0, marker_pos))
            if last_open_paren_before_marker > last_close_paren_before_marker:
                # Marker is inside parentheses, skip this split
                continue
            
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
    
    # Check for area selection pattern in comma-separated actions
    if '登場したエリアとは別の自分のエリア1つを選ぶ' in text or 'いるエリアとは別の自分のエリア1つを選ぶ' in text or '、登場したエリアとは別の自分のエリア1つを選ぶ' in text:
        result['actions'] = []
        # Split on comma
        parts = text.rstrip('。').split('、')
        for part in parts:
            part = part.strip()
            if 'カードを1枚引く' in part:
                result['actions'].append({
                    'action': 'draw_cards',
                    'count': 1
                })
            elif '登場したエリアとは別の自分のエリア1つを選ぶ' in part:
                result['actions'].append({
                    'action': 'select_area',
                    'source': 'stage',
                    'exclude': 'deployed_area',
                    'count': 1,
                    'target': 'self'
                })
            elif 'このメンバーをそのエリアに移動する' in part:
                result['actions'].append({
                    'action': 'move_member',
                    'source': 'this_member',
                    'destination': 'selected_area'
                })
            elif '選んだエリアにメンバーがいる場合' in part or '選んだエリアにメンバーがいる' in part:
                # This is a condition for the movement
                result['actions'][-1]['condition'] = 'selected_area_occupied'
            else:
                action = parse_effect_backwards(part)
                if _is_parsed_action(action):
                    result['actions'].append(action)
                else:
                    result['actions'].append(_raw_text(part))
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
            # Merge modifier-only actions with their target actions
            result['actions'] = _merge_modifier_actions(result['actions'])
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

