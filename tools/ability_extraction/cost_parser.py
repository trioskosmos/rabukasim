"""Cost parsing for ability extraction."""
import re
from dataclasses import dataclass
from typing import Any, Callable

try:
    from .parser_utils import (
        extract_count,
        extract_group_name,
        extract_int,
        extract_quoted_name,
        has_any,
        normalize_text,
        parse_optional_flag,
    )
except ImportError:
    from parser_utils import (
        extract_count,
        extract_group_name,
        extract_int,
        extract_quoted_name,
        has_any,
        normalize_text,
        parse_optional_flag,
    )


@dataclass(frozen=True)
class CostRule:
    """Ordered cost rule used by parse_cost.

    Rules are evaluated in ascending priority order. Keep specific rules before
    more general ones to avoid accidental matches.
    """

    name: str
    output_key: str
    priority: int
    matches: Callable[[str], bool]
    extract: Callable[[str], Any]
    notes: str = ""


ENERGY_ICON = '{icon_energy.png|E}'
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

    cleaned = {
        key: item
        for key, item in value.items()
        if item is not None
    }
    if cleaned.get('max') is False:
        del cleaned['max']
    return cleaned


def _extract_member_to_waitroom_cost(text):
    return {
        'target': 'this_member' if 'このメンバー' in text else 'member',
        'optional': parse_optional_flag(text, ['置いてもよい', 'でもよい']),
        'count': _extract_member_count(text),
        'exclude_member': extract_quoted_name(text) if '以外' in text else None,
        'group': extract_group_name(text),
    }


def _extract_member_to_wait_cost(text):
    max_count = _extract_max_people_count(text)
    return {
        'target': 'member' if 'このメンバー以外' in text else ('this_member' if 'このメンバー' in text else 'member'),
        'optional': parse_optional_flag(text, ['でもよい']),
        'count': _extract_member_count(text, default=max_count or 1),
        'max': max_count is not None,
        'group': extract_group_name(text),
        'exclude_member': True if 'このメンバー以外' in text else None,
    }


def _extract_reveal_cost(text):
    return {
        'source': 'hand',
        'optional': parse_optional_flag(text, ['でもよい', '公開してもよい']),
        'card_type': _extract_card_type(text),
        'group': extract_group_name(text),
        'count': 'all' if 'すべて' in text else (extract_count(text) or 'any'),
    }


def _extract_energy_to_member_cost(text):
    return {
        'count': extract_count(text) or 1,
        'source': 'energy_zone',
        'target': 'this_member',
    }


def _extract_energy_to_energy_deck_cost(text):
    return {
        'count': extract_count(text) or 1,
        'target': 'energy_deck',
    }


def _extract_waitroom_to_deck_bottom_cost(text):
    return {
        'count': extract_count(text) or 1,
        'card_type': _extract_card_type(text, default='card'),
        'optional': parse_optional_flag(text, ['でもよい', '置いてもよい']),
        'order': 'any' if '好きな順番' in text else None,
    }


def _extract_hand_to_deck_bottom_cost(text):
    return {
        'count': extract_count(text) or 1,
        'card_type': _extract_card_type(text, default='card'),
        'optional': parse_optional_flag(text, ['でもよい', '置いてもよい']),
        'source': 'hand',
    }


def _extract_discard_from_hand_cost(text):
    return {
        'count': extract_count(text) or 1,
        'optional': parse_optional_flag(text, ['置いてもよい', 'でもよい', '支払ってもよい']),
        'card_type': _extract_card_type(text),
        'group': extract_group_name(text),
    }


def _extract_discard_from_deck_cost(text):
    return {
        'count': extract_count(text) or 1,
        'optional': parse_optional_flag(text, ['でもよい', '支払ってもよい']),
    }


# Rules are evaluated in priority order. Keep specific destination/source rules
# above broad discard-style rules that could otherwise match the same text.
COST_RULES = (
    CostRule(
        name='energy',
        output_key='energy',
        priority=10,
        matches=lambda text: ENERGY_ICON in text,
        extract=lambda text: text.count(ENERGY_ICON),
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
            cost[rule.output_key] = _clean_extracted_cost(rule.extract(cost_text))

    position = _extract_position(cost_text)
    if position:
        cost['position'] = position

    return cost_text if not cost else cost
