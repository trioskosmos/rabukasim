"""Entrypoint and compatibility wrapper for ability cost/effect extraction."""

import json
import re

try:
    from .condition_parser import parse_condition
    from .cost_parser import parse_cost
    from .effect_parser import (
        _extract_optional_payment,
        parse_complex_effect,
        parse_compound_effect,
        parse_conditional_effect,
        parse_effect_backwards,
        parse_effect_context_backwards,
        parse_generic_effect,
        split_commas_smartly,
    )
    from .tree_utils import apply_tree_field, prune_empty_raw_nodes, walk_nodes
except ImportError:
    from condition_parser import parse_condition
    from cost_parser import parse_cost
    from effect_parser import (
        _extract_optional_payment,
        parse_complex_effect,
        parse_compound_effect,
        parse_conditional_effect,
        parse_effect_backwards,
        parse_effect_context_backwards,
        parse_generic_effect,
        split_commas_smartly,
    )
    from tree_utils import apply_tree_field, prune_empty_raw_nodes, walk_nodes

__all__ = [
    'main',
    'parse_compound_effect',
    'parse_complex_effect',
    'parse_condition',
    'parse_conditional_effect',
    'parse_cost',
    'parse_effect_backwards',
    'parse_effect_context_backwards',
    'parse_generic_effect',
    'process_abilities',
    'split_commas_smartly',
]


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


def _fix_condition_types(value):
    """Post-process to fix conditions that have exclude_this_member but no type."""
    def visit(node):
        condition = node.get('condition')
        if isinstance(condition, dict) and condition.get('exclude_this_member') and 'type' not in condition:
            condition['type'] = 'member_exclusion'

    walk_nodes(value, visit)
    return value


def _flatten_action_wrappers(value):
    if isinstance(value, dict):
        for key, item in list(value.items()):
            value[key] = _flatten_action_wrappers(item)

        nested_action = value.get('action')
        if isinstance(nested_action, dict) and 'actions' in nested_action:
            del value['action']
            for key, item in nested_action.items():
                if key == 'actions' or key not in value:
                    value[key] = item
        return value

    if isinstance(value, list):
        return [_flatten_action_wrappers(item) for item in value]

    return value


def _extract_use_limit(ability):
    use_limit = ability.get('use_limit')
    if use_limit:
        return use_limit

    full_text = ability.get('full_text', '')
    if '{{turn1.png|\u30bf\u30fc\u30f31\u56de}}' in full_text or '\u30bf\u30fc\u30f31\u56de' in full_text:
        return 'turn1'
    return None


def _extract_position_requirement(ability):
    full_text = ability.get('full_text', '')
    costless_text = ability.get('costless_text', '')

    if '{{center.png|\u30bb\u30f3\u30bf\u30fc}}' in full_text or '{{center.png|\u30bb\u30f3\u30bf\u30fc}}' in costless_text:
        return 'center'
    if '\u3010\u5de6\u30b5\u30a4\u30c9\u3011' in full_text or '\u3010\u5de6\u30b5\u30a4\u30c9\u3011' in costless_text:
        return 'left_side'
    if '\u3010\u53f3\u30b5\u30a4\u30c9\u3011' in full_text or '\u3010\u53f3\u30b5\u30a4\u30c9\u3011' in costless_text:
        return 'right_side'
    if '\u30bb\u30f3\u30bf\u30fc\u30a8\u30ea\u30a2\u306b\u767b\u5834\u3057\u3066\u3044\u308b\u5834\u5408\u306e\u307f\u8d77\u52d5\u3067\u304d\u308b' in full_text:
        return 'center'
    return None


def _extract_parenthetical_notes(ability):
    full_text = ability.get('full_text', '')
    if '\uff08' not in full_text and '(' not in full_text:
        return None
    notes = re.findall(r'\uff08[^\uff09]+\uff09|\([^)]*\)', full_text)
    return notes or None


def main():

    """Load input data, process abilities, and write the updated JSON."""
    with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as handle:
        data = json.load(handle)

    with open('tools/ability_extraction/variable_config.json', 'r', encoding='utf-8') as handle:
        json.load(handle)

    updated = process_abilities(data)
    for field_name, value_factory in (
        ('trigger', lambda ability: ability.get('triggers')),
        ('use_limit', _extract_use_limit),
        ('position_requirement', _extract_position_requirement),
        ('notes', _extract_parenthetical_notes),
    ):
        apply_tree_field(updated, field_name, value_factory)
    _fix_condition_types(updated)
    _flatten_action_wrappers(updated)
    prune_empty_raw_nodes(updated)

    with open('data/abilities_extracted_from_cards.json', 'w', encoding='utf-8') as handle:
        json.dump(updated, handle, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
