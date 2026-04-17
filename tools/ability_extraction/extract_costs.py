"""Process abilities: parse costs/effects and standardize JSON structure."""

import json
import re
from dataclasses import dataclass
from typing import Any, Callable
from condition_parser import parse_condition
from effect_parser import (
    _extract_optional_payment,
    parse_generic_effect,
)
from parser_utils import (
    extract_count,
    extract_group_name,
    extract_int,
    extract_quoted_name,
    has_any,
    normalize_text,
    parse_optional_flag,
)

def walk_nodes(value, visit):
    """Depth-first walk over dict/list nodes and call visit for each dict."""
    if isinstance(value, dict):
        visit(value)
        for item in value.values():
            walk_nodes(item, visit)
    elif isinstance(value, list):
        for item in value:
            walk_nodes(item, visit)


# Cost parsing
@dataclass(frozen=True)
class CostRule:
    name: str
    output_key: str
    priority: int
    matches: Callable[[str], bool]
    extract: Callable[[str], Any]
    notes: str = ""

ENERGY_ICON = '{{icon_energy.png|E}}'
MEMBER_COUNT_PATTERN = re.compile(r'メンバー(\d+)人')
MAX_PEOPLE_PATTERN = re.compile(r'(\d+)人まで')


def _extract_cost_text(text):
    if '：' not in text and ':' not in text:
        return None
    delimiter = '：' if '：' in text else ':'
    cost_text = normalize_text(text.split(delimiter, 1)[0])
    return cost_text or None


def _extract_card_type(text, *, default=None):
    if 'メンバーカード' in text:
        return 'member_card'
    if 'ライブカード' in text:
        return 'live_card'
    return default


def _extract_position(text):
    if 'センター' in text:
        return 'center'
    if '左サイド' in text:
        return 'left_side'
    if '右サイド' in text:
        return 'right_side'
    return None


def _extract_member_count(text, default=1):
    return extract_int(MEMBER_COUNT_PATTERN, text, default=default)


def _extract_max_people_count(text):
    return extract_int(MAX_PEOPLE_PATTERN, text)


def _clean_extracted_cost(value):
    if not isinstance(value, dict):
        return value
    cleaned = {key: item for key, item in value.items() if item is not None}
    if cleaned.get('max') is False:
        del cleaned['max']
    return cleaned


def _annotate_text(value, text):
    if not text or value is None:
        return value
    if isinstance(value, dict):
        value.setdefault('text', text)
        for item in value.values():
            _annotate_text(item, text)
    elif isinstance(value, list):
        for item in value:
            _annotate_text(item, text)
    return value


def _extract_member_to_waitroom_cost(text):
    return {
        'type': 'move_cards',
        'source': 'stage',
        'destination': 'waitroom',
        'target': 'this_member' if 'このメンバー' in text else 'member',
        'optional': parse_optional_flag(text, ['置いてもよい', 'でもよい']),
        'count': _extract_member_count(text),
        'exclude_member': extract_quoted_name(text) if '以外' in text else None,
        'group': extract_group_name(text),
    }


def _extract_member_to_wait_cost(text):
    max_count = _extract_max_people_count(text)
    return {
        'type': 'move_cards',
        'source': 'stage',
        'destination': 'wait',
        'target': 'member' if 'このメンバー以外' in text else ('this_member' if 'このメンバー' in text else 'member'),
        'optional': parse_optional_flag(text, ['でもよい', 'ウェイトにしてもよい']),
        'count': _extract_member_count(text, default=max_count or 1),
        'max': max_count is not None,
        'group': extract_group_name(text),
        'exclude_member': True if 'このメンバー以外' in text else None,
    }


def _extract_reveal_cost(text):
    return {
        'type': 'reveal_cards',
        'source': 'hand',
        'optional': parse_optional_flag(text, ['でもよい', '公開してもよい']),
        'card_type': _extract_card_type(text),
        'group': extract_group_name(text),
        'count': 'all' if 'すべて' in text else (extract_count(text) or 'any'),
    }


def _extract_energy_to_member_cost(text):
    return {
        'type': 'move_cards',
        'source': 'energy_zone',
        'destination': 'member_under',
        'target': 'this_member',
        'card_type': 'energy_card',
        'count': extract_count(text) or 1,
    }


def _extract_energy_to_energy_deck_cost(text):
    return {
        'type': 'move_cards',
        'source': 'energy_zone',
        'destination': 'energy_deck',
        'card_type': 'energy_card',
        'count': extract_count(text) or 1,
    }


def _extract_waitroom_to_deck_bottom_cost(text):
    return {
        'type': 'move_cards',
        'source': 'waitroom',
        'destination': 'deck_bottom',
        'count': extract_count(text) or 1,
        'card_type': _extract_card_type(text, default='card'),
        'optional': parse_optional_flag(text, ['でもよい', '置いてもよい']),
        'order': 'any' if '好きな順番' in text else None,
    }


def _extract_hand_to_deck_bottom_cost(text):
    return {
        'type': 'move_cards',
        'source': 'hand',
        'destination': 'deck_bottom',
        'count': extract_count(text) or 1,
        'card_type': _extract_card_type(text, default='card'),
        'optional': parse_optional_flag(text, ['でもよい', '置いてもよい']),
    }


def _extract_discard_from_hand_cost(text):
    return {
        'type': 'move_cards',
        'source': 'hand',
        'destination': 'waitroom',
        'count': extract_count(text) or 1,
        'optional': parse_optional_flag(text, ['置いてもよい', 'でもよい', '支払ってもよい']),
        'card_type': _extract_card_type(text),
        'group': extract_group_name(text),
    }


def _extract_discard_from_deck_cost(text):
    return {
        'type': 'move_cards',
        'source': 'deck',
        'destination': 'waitroom',
        'count': extract_count(text) or 1,
        'optional': parse_optional_flag(text, ['でもよい', '支払ってもよい']),
    }


COST_RULES = (
    CostRule(
        name='energy',
        output_key='energy',
        priority=10,
        matches=lambda text: ENERGY_ICON in text,
        extract=lambda text: {'type': 'pay_energy', 'energy': text.count(ENERGY_ICON)},
        notes='Counts explicit energy icons before any text-based cost parsing.',
    ),
    CostRule(
        name='member_to_waitroom',
        output_key='member_to_waitroom',
        priority=20,
        matches=lambda text: has_any(text, ['ステージから控え室に置']),
        extract=_extract_member_to_waitroom_cost,
        notes='Specific stage-to-waitroom movement should win over generic discard rules.',
    ),
    CostRule(
        name='member_to_wait',
        output_key='member_to_wait',
        priority=30,
        matches=lambda text: has_any(text, ['ウェイトにする', 'ウェイトにしてもよい']),
        extract=_extract_member_to_wait_cost,
    ),
    CostRule(
        name='reveal',
        output_key='reveal',
        priority=40,
        matches=lambda text: '手札' in text and has_any(text, ['公開する', '公開してもよい', '公開し']),
        extract=_extract_reveal_cost,
    ),
    CostRule(
        name='energy_to_member',
        output_key='energy_to_member',
        priority=50,
        matches=lambda text: 'エネルギー置き場' in text and 'このメンバーの下に置く' in text,
        extract=_extract_energy_to_member_cost,
    ),
    CostRule(
        name='energy_to_energy_deck',
        output_key='energy_to_energy_deck',
        priority=60,
        matches=lambda text: 'エネルギーデッキ' in text and '置く' in text,
        extract=_extract_energy_to_energy_deck_cost,
    ),
    CostRule(
        name='waitroom_to_deck_bottom',
        output_key='waitroom_to_deck_bottom',
        priority=70,
        matches=lambda text: '控え室' in text and has_any(text, ['デッキの一番下に置く', 'デッキの一番下に置いてもよい']),
        extract=_extract_waitroom_to_deck_bottom_cost,
    ),
    CostRule(
        name='hand_to_deck_bottom',
        output_key='hand_to_deck_bottom',
        priority=80,
        matches=lambda text: '手札' in text and has_any(text, ['デッキの一番下に置く', 'デッキの一番下に置いてもよい']),
        extract=_extract_hand_to_deck_bottom_cost,
    ),
    CostRule(
        name='discard_from_hand',
        output_key='discard_from_hand',
        priority=90,
        matches=lambda text: '手札' in text and has_any(text, ['控え室に置く', '控え室に置いてもよい']),
        extract=_extract_discard_from_hand_cost,
    ),
    CostRule(
        name='discard_from_deck',
        output_key='discard_from_deck',
        priority=100,
        matches=lambda text: 'デッキ' in text and '控え室に置く' in text,
        extract=_extract_discard_from_deck_cost,
    ),
)


def parse_cost(text):
    """Parse cost from triggerless text using ordered cost rules."""
    cost_text = _extract_cost_text(text)
    if not cost_text:
        return None

    cost = {}
    for rule in sorted(COST_RULES, key=lambda item: item.priority):
        if rule.matches(cost_text):
            extracted = _clean_extracted_cost(rule.extract(cost_text))
            cost.update(extracted)

    position = _extract_position(cost_text)
    if position:
        cost['position'] = position

    if not cost:
        return _annotate_text(cost_text, cost_text)
    cost['text'] = cost_text
    return _annotate_text(cost, cost_text)

def apply_tree_field(data, field_name, value_factory, *, tree_key='effect'):
    """Copy a computed field onto every dict node in each parsed tree."""
    for item in data.get('unique_abilities', []):
        tree = item.get(tree_key)
        if not tree:
            continue
        value = value_factory(item)
        if value is None:
            continue
        def visit(node):
            if field_name not in node:
                node[field_name] = value
        walk_nodes(tree, visit)
    return data

def prune_empty_raw_nodes(value):
    """Remove nodes that only carry an empty raw_text placeholder."""
    if isinstance(value, dict):
        keys_to_delete = []
        for key, item in value.items():
            if isinstance(item, dict) and item.get('raw_text') == '':
                keys_to_delete.append(key)
            else:
                prune_empty_raw_nodes(item)
        for key in keys_to_delete:
            del value[key]
    elif isinstance(value, list):
        items = []
        for item in value:
            if isinstance(item, dict) and item.get('raw_text') == '':
                continue
            prune_empty_raw_nodes(item)
            items.append(item)
        value[:] = items
    return value

def process_abilities(data):
    """Populate structured cost/effect fields for each unique ability."""
    for ability in data['unique_abilities']:
        triggerless_text = ability['triggerless_text']
        ability['cost'] = parse_cost(triggerless_text)
        ability['costless'] = ability['cost'] is None or (
            isinstance(ability['cost'], str) and ability['cost'] == triggerless_text
        )
        use_limitless_text = triggerless_text
        if ability.get('use_limit'):
            use_limitless_text = re.sub(r'\{\{[^}]+\}\}\s*', '', use_limitless_text)
        ability['use_limitless_text'] = use_limitless_text
        payment, remaining_text = _extract_optional_payment(use_limitless_text)
        if payment:
            ability['payment'] = payment
            costless_text = remaining_text
        else:
            costless_text = triggerless_text
            if '??' in costless_text:
                costless_text = costless_text.split('??', 1)[1].strip()
            elif ':' in costless_text:
                costless_text = costless_text.split(':', 1)[1].strip()
        ability['costless_text'] = costless_text
        ability['effect'] = parse_generic_effect(costless_text) if costless_text else None
    return data


def post_process(data):
    """Standardize JSON architecture and fix common issues."""
    def visit(node):
        # Fix condition types
        condition = node.get('condition')
        if isinstance(condition, dict) and condition.get('exclude_this_member') and 'type' not in condition:
            condition['type'] = 'member_exclusion'
        # Fix missing condition types
        if isinstance(condition, dict) and 'type' not in condition:
            text = condition.get('text', '')
            if 'ちょうど' in text or 'exactly' in text:
                condition['type'] = 'member_count_exact'
            elif '以上' in text or '以上の' in text:
                condition['type'] = 'member_count_at_least'
            elif '以下' in text or '以下の' in text:
                condition['type'] = 'member_count_at_most'
            elif 'いる' in text or 'present' in text:
                condition['type'] = 'card_presence'
            elif text:
                condition['type'] = 'custom'
        # Flatten nested actions
        nested_action = node.get('action')
        if isinstance(nested_action, dict):
            if 'actions' in nested_action:
                del node['action']
                for key, item in nested_action.items():
                    if key == 'actions' or key not in node:
                        node[key] = item
            elif 'action' in nested_action:
                del node['action']
                for key, item in nested_action.items():
                    if key not in node:
                        node[key] = item
    walk_nodes(data, visit)
    
    # Ability-level fixes
    for ability in data.get('unique_abilities', []):
        # Convert single action to array
        if isinstance(ability.get('effect'), dict):
            effect = ability['effect']
            if 'action' in effect:
                if isinstance(effect['action'], dict):
                    effect['actions'] = [effect['action']]
                elif isinstance(effect['action'], str):
                    effect['actions'] = [{'action': effect['action'], 'text': effect['action']}]
                del effect['action']
            # Remove redundant payment
            if ability.get('payment') and ability.get('cost'):
                del ability['payment']
            # Fix null triggers
            if ability.get('triggers') is None:
                match = re.search(r'\{\{[^}]+\|([^\}]+)\}\}', ability.get('full_text', ''))
                if match:
                    ability['triggers'] = match.group(1)
            # Remove excessive trigger duplication
            if isinstance(effect.get('actions'), list):
                trigger_count = 1 if 'trigger' in effect else 0
                for action in effect['actions']:
                    if isinstance(action, dict) and 'trigger' in action:
                        trigger_count += 1
                if trigger_count > 3:
                    for action in effect['actions']:
                        if isinstance(action, dict) and 'trigger' in action:
                            del action['trigger']
            # Remove non-action metadata
            if isinstance(effect.get('actions'), list):
                filtered = [a for a in effect['actions'] if isinstance(a, dict) and 'action' in a]
                if filtered:
                    effect['actions'] = filtered
                elif effect.get('actions'):  # Would be empty, add placeholder
                    effect['actions'] = [{'action': 'unknown', 'text': effect.get('text', ''), 'parsing_error': 'Action field missing'}]
    return data


def extract_metadata(ability):
    """Extract metadata fields from ability text."""
    full_text = ability.get('full_text', '')
    # Use limit
    use_limit = ability.get('use_limit')
    if not use_limit:
        if 'ターン1回' in full_text:
            use_limit = 'turn1'
    # Position requirement
    position = None
    if 'センター' in full_text or 'センター' in ability.get('costless_text', ''):
        position = 'center'
    elif '左サイド' in full_text or '左サイド' in ability.get('costless_text', ''):
        position = 'left_side'
    elif '右サイド' in full_text or '右サイド' in ability.get('costless_text', ''):
        position = 'right_side'
    # Notes
    notes = None
    if '（' in full_text or '(' in full_text:
        notes = re.findall(r'（[^）]+）|\([^)]*\)', full_text)
    return use_limit, position, notes


def main():
    """Load input data, process abilities, and write the updated JSON."""
    with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    data = process_abilities(data)
    
    # Apply metadata fields
    for ability in data['unique_abilities']:
        use_limit, position, notes = extract_metadata(ability)
        if use_limit:
            ability['use_limit'] = use_limit
        if position:
            ability['position_requirement'] = position
        if notes:
            ability['notes'] = notes
        
        # Apply trigger to effect tree
        trigger = ability.get('triggers')
        if trigger and ability.get('effect'):
            def set_trigger(node):
                if 'trigger' not in node:
                    node['trigger'] = trigger
            walk_nodes(ability['effect'], set_trigger)
    
    data = post_process(data)
    prune_empty_raw_nodes(data)
    
    with open('data/abilities_extracted_from_cards.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main()
