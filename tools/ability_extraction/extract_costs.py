"""Entrypoint and compatibility wrapper for ability cost/effect extraction."""

import json
import re

try:
    from .condition_parser import parse_condition
    from .cost_parser import parse_cost
    from .effect_parser import (
        parse_complex_effect,
        parse_compound_effect,
        parse_conditional_effect,
        parse_effect_backwards,
        parse_effect_context_backwards,
        parse_generic_effect,
        split_commas_smartly,
    )
except ImportError:
    from condition_parser import parse_condition
    from cost_parser import parse_cost
    from effect_parser import (
        parse_complex_effect,
        parse_compound_effect,
        parse_conditional_effect,
        parse_effect_backwards,
        parse_effect_context_backwards,
        parse_generic_effect,
        split_commas_smartly,
    )

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

        costless_text = triggerless_text
        if '：' in costless_text:
            costless_text = costless_text.split('：', 1)[1].strip()
        elif ':' in costless_text:
            costless_text = costless_text.split(':', 1)[1].strip()
        ability['costless_text'] = costless_text
        ability['effect'] = parse_generic_effect(costless_text) if costless_text else None

    return data


def main():
    """Load input data, process abilities, and write the updated JSON."""
    with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as handle:
        data = json.load(handle)

    with open('tools/ability_extraction/variable_config.json', 'r', encoding='utf-8') as handle:
        json.load(handle)

    updated = process_abilities(data)

    with open('data/abilities_extracted_from_cards.json', 'w', encoding='utf-8') as handle:
        json.dump(updated, handle, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
