#!/usr/bin/env python3
"""
Extract effect information from costless_text using pattern-based approach.
Reads from: data/abilities_extracted_from_cards.json
Writes to: data/abilities_extracted_from_cards.json (adds 'effect' field)
"""

import json
import re

with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

with open('tools/ability_extraction/variable_config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

def parse_effect(text):
    """Parse effect from costless_text using pattern-based loop approach."""
    if not text:
        return None
    
    effect = {}
    effect_patterns = [
        {
            'name': 'draw',
            'required_phrases': ['カードを', '引く'],
            'check': lambda t: 'カードを' in t and '引く' in t,
            'extract': lambda t: {
                'count': int(re.search(r'(\d+)枚', t).group(1)) if re.search(r'(\d+)枚', t) else 1,
                'dynamic': '置いた枚数分' in t
            },
            'output_key': 'draw'
        },
        {
            'name': 'add_to_hand',
            'required_phrases': ['手札に加える'],
            'check': lambda t: '手札に加える' in t,
            'extract': lambda t: {
                'source': 'waitroom' if '控え室' in t else ('deck' if 'デッキ' in t else None),
                'card_type': 'live_card' if 'ライブカード' in t else ('member_card' if 'メンバーカード' in t else None),
                'group': re.search(r"『(.+?)』", t).group(1) if re.search(r"『(.+?)』", t) else None,
                'count': int(re.search(r'(\d+)枚', t).group(1)) if re.search(r'(\d+)枚', t) else 1,
                'max': bool(re.search(r'(\d+)枚まで', t)),
                'cost_limit': int(re.search(r'コスト(\d+)以下', t).group(1)) if re.search(r'コスト(\d+)以下', t) else None,
                'special_condition': re.search(r"{{[^}]+}}を持つ", t).group(0) if re.search(r"{{[^}]+}}を持つ", t) else None
            },
            'output_key': 'add_to_hand'
        },
        {
            'name': 'activate_energy',
            'required_phrases': ['アクティブにする'],
            'check': lambda t: 'アクティブにする' in t,
            'extract': lambda t: {
                'target': 'energy' if 'エネルギー' in t else ('member' if 'メンバー' in t else None),
                'group': re.search(r"『(.+?)』", t).group(1) if re.search(r"『(.+?)』", t) else None,
                'count': int(re.search(r'(\d+)枚', t).group(1)) if re.search(r'(\d+)枚', t) else 1,
                'max': bool(re.search(r'(\d+)枚まで', t)),
                'all': bool(re.search(r'すべて', t))
            },
            'output_key': 'activate_energy'
        },
        {
            'name': 'wait',
            'required_phrases': ['ウェイトにする'],
            'check': lambda t: 'ウェイトにする' in t,
            'extract': lambda t: {
                'target': 'opponent' if '相手' in t else None,
                'count': int(re.search(r'(\d+)人', t).group(1)) if re.search(r'(\d+)人', t) else 1,
                'max': bool(re.search(r'(\d+)人まで', t)),
                'cost_limit': int(re.search(r'コスト(\d+)以下', t).group(1)) if re.search(r'コスト(\d+)以下', t) else None,
                'condition': re.search(r"元々持つ{{[^}]+}}の数が(\d+)つ以下", t).group(0) if re.search(r"元々持つ{{[^}]+}}の数が(\d+)つ以下", t) else None
            },
            'output_key': 'wait'
        },
        {
            'name': 'discard',
            'required_phrases': ['控え室に置く'],
            'check': lambda t: '控え室に置く' in t and '手札' not in t,  # Exclude hand discard
            'extract': lambda t: {
                'source': 'deck' if 'デッキ' in t else None,
                'count': int(re.search(r'(\d+)枚', t).group(1)) if re.search(r'(\d+)枚', t) else 1
            },
            'output_key': 'discard'
        },
        {
            'name': 'move_to_deck',
            'required_phrases': ['デッキ', '置く'],
            'check': lambda t: 'デッキ' in t and ('置く' in t or '戻す' in t) and '手札' not in t,
            'extract': lambda t: {
                'source': 'waitroom' if '控え室' in t else None,
                'destination': 'deck_top' if '一番上' in t else ('deck_bottom' if '一番下' in t else None),
                'card_type': 'member_card' if 'メンバーカード' in t else None,
                'count': int(re.search(r'(\d+)枚', t).group(1)) if re.search(r'(\d+)枚', t) else 1,
                'max': bool(re.search(r'(\d+)枚まで', t)),
                'order': 'any' if '好きな順番' in t else None
            },
            'output_key': 'move_to_deck'
        },
        {
            'name': 'gain_resource',
            'required_phrases': ['を得る', '+１する', '+２する', 'を加算する'],
            'check': lambda t: any(p in t for p in ['を得る', '+１する', '+２する', 'を加算する']),
            'extract': lambda t: {
                'resource': re.search(r"{{[^}]+}}", t).group(0) if re.search(r"{{[^}]+}}", t) else 'blade',
                'count': len(re.findall(r"{{[^}]+}}", t)) if re.findall(r"{{[^}]+}}", t) else 1,
                'position': 'center' if 'センター' in t else ('left_side' if '左サイド' in t else ('right_side' if '右サイド' in t else None)),
                'target': 'live_score' if 'ライブの合計スコア' in t else None
            },
            'output_key': 'gain_resource'
        }
    ]
    
    for pattern in effect_patterns:
        if pattern['check'](text):
            extracted = pattern['extract'](text)
            if isinstance(extracted, dict):
                extracted = {k: v for k, v in extracted.items() if v is not None}
            effect[pattern['output_key']] = extracted
    
    return effect if effect else None

for ab in data['unique_abilities']:
    ab['effect'] = parse_effect(ab.get('costless_text', ''))

with open('data/abilities_extracted_from_cards.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Extracted effects for {len(data['unique_abilities'])} abilities")
