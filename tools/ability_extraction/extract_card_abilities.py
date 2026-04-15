#!/usr/bin/env python3
"""
Extract card abilities from cards.json.
Splits abilities by newline and extracts triggers.
Handles /-separated triggers as single ability with multiple triggers.
"""

import json
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict


# Game term patterns for expression parsing
CARD_TYPES = [
    'このメンバー', 'ライブカード', 'メンバーカード', 'カード', 
    'エネルギーカード', 'ライブ中のカード', '成功ライブカード',
    'エネルギーデッキ', 'エネルギー', 'ハート', 'ブレード'
]

ZONES = [
    'ステージ', '控え室', '手札', 'デッキ', 'ウェイト', 
    'エネルギー置き場', '成功ライブカード置き場', 'エリア'
]

PLAYERS = [
    '自分', '相手'
]

POSITIONS = [
    '【左サイド】', '【右サイド】', '【センター】', '【左】', '【右】', '【中央】',
    'センター', '左サイド', '右サイド'
]

TIMING_MODIFIERS = [
    '【ターン1回】', '［ターン1回］', 'ターン1回',
    'ターン2回', '2回', '毎ターン'
]

GROUP_NAMES = []  # Will be extracted dynamically from 『』 patterns

ENERGY_COSTS = []  # Will be extracted from {{icon_energy.png|E}} patterns

CHARACTER_NAMES = []  # Will be extracted from 「」 patterns

SCORE_MODIFIERS = []  # Will be extracted from +1/+2/+3 patterns


def split_cost_effect(text: str) -> tuple[str, str]:
    """
    Split ability text into cost and effect by ： colon.
    Returns: (cost, effect)
    """
    if '：' in text:
        parts = text.split('：', 1)
        return parts[0].strip(), parts[1].strip()
    return '', text


def extract_game_terms(text: str) -> dict:
    """
    Extract game terms from text and return as structured dict.
    """
    terms = {
        'card_types': [],
        'zones': [],
        'players': [],
        'numbers': [],
        'positions': [],
        'timing_modifiers': [],
        'group_names': [],
        'energy_costs': [],
        'character_names': [],
        'score_modifiers': [],
        'icon_patterns': []
    }
    
    # Extract all {{}} patterns as variables
    icon_pattern = re.compile(r'\{\{([^|]+)\|([^}]+)\}\}')
    icon_matches = icon_pattern.findall(text)
    for icon_file, icon_text in icon_matches:
        full_pattern = f"{{{{{icon_file}|{icon_text}}}}}"
        terms['icon_patterns'].append(full_pattern)
        # Also add the text content
        terms['icon_patterns'].append(icon_text)
    
    # Extract numbers
    number_pattern = re.compile(r'(\d+)枚')
    numbers = number_pattern.findall(text)
    terms['numbers'] = numbers
    
    # Extract score modifiers (+1, +2, +3, etc.)
    score_pattern = re.compile(r'\+([０-９]+)')
    score_matches = score_pattern.findall(text)
    terms['score_modifiers'] = score_matches
    
    # Extract card types
    for card_type in CARD_TYPES:
        if card_type in text:
            terms['card_types'].append(card_type)
    
    # Extract zones
    for zone in ZONES:
        if zone in text:
            terms['zones'].append(zone)
    
    # Extract players
    for player in PLAYERS:
        if player in text:
            terms['players'].append(player)
    
    # Extract positions
    for position in POSITIONS:
        if position in text:
            terms['positions'].append(position)
    
    # Extract timing modifiers
    for timing in TIMING_MODIFIERS:
        if timing in text:
            terms['timing_modifiers'].append(timing)
    
    # Extract group names from 『』 patterns
    group_pattern = re.compile(r'『([^』]+)』')
    group_matches = group_pattern.findall(text)
    terms['group_names'] = group_matches
    
    # Extract energy costs from {{icon_energy.png|E}} patterns
    energy_pattern = re.compile(r'\{\{icon_energy\.png\|E\}\}')
    energy_matches = energy_pattern.findall(text)
    if energy_matches:
        # Count the number of E icons
        energy_count = len(energy_matches)
        terms['energy_costs'].append(f"{energy_count}E")
    
    # Extract character names from 「」 patterns
    char_pattern = re.compile(r'「([^」]+)」')
    char_matches = char_pattern.findall(text)
    # Filter out score modifiers and other non-character patterns
    for char in char_matches:
        # Skip if it's just a number or score modifier
        if not re.match(r'^[０-９]+$', char) and not re.match(r'^\+', char):
            terms['character_names'].append(char)
    
    return terms


def compress_templates(template_list: list) -> list:
    """
    Compress templates using hierarchical variable matching.
    Groups templates that share structural patterns at different abstraction levels.
    """
    # Level 1: Exact match (current templates)
    # Level 2: Abstract specific values to generic types
    # Level 3: Abstract hierarchical relationships
    
    level_groups = {
        'level1': defaultdict(list),
        'level2': defaultdict(list),
        'level3': defaultdict(list)
    }
    
    for template_data in template_list:
        template = template_data['template']
        
        # Level 1: Original template
        level_groups['level1'][template].append(template_data)
        
        # Level 2: Abstract specific values to generic types
        structure = template
        structure = re.sub(r'\[number\]', '[N]', structure)
        structure = re.sub(r'\[card_type\]', '[CT]', structure)
        structure = re.sub(r'\[zone\]', '[Z]', structure)
        structure = re.sub(r'\[player\]', '[P]', structure)
        structure = re.sub(r'\[position\]', '[POS]', structure)
        structure = re.sub(r'\[timing_modifier\]', '[TM]', structure)
        structure = re.sub(r'\[group_name\]', '[G]', structure)
        structure = re.sub(r'\[([0-9]+)E\]', '[E]', structure)
        structure = re.sub(r'\[character_name\]', '[C]', structure)
        structure = re.sub(r'\[score_modifier\]', '[S]', structure)
        structure = re.sub(r'\[icon\]', '[I]', structure)
        structure = re.sub(r'\[icon_text\]', '[IT]', structure)
        
        level_groups['level2'][structure].append(template_data)
        
        # Level 3: Abstract hierarchical relationships
        # Abstract cost thresholds (コスト9以上 → コスト以上)
        structure3 = re.sub(r'コスト[0-9]+以上', 'コスト[THRESHOLD]以上', structure)
        structure3 = re.sub(r'コスト[0-9]+以下', 'コスト[THRESHOLD]以下', structure3)
        
        # Abstract group names (『μ's』 → 『GROUP』)
        structure3 = re.sub(r'『[^』]+』', '『GROUP』', structure3)
        
        # Abstract specific numbers in conditionals
        structure3 = re.sub(r'[0-9]+以上', '[NUM]以上', structure3)
        structure3 = re.sub(r'[0-9]+以下', '[NUM]以下', structure3)
        
        # Abstract position modifiers
        structure3 = re.sub(r'一番上|一番下', '[POS_MOD]', structure3)
        
        # Abstract quantifiers
        structure3 = re.sub(r'すべて|1人|2人|3人|[0-9]+人', '[QUANT]', structure3)
        
        # Abstract color patterns
        structure3 = re.sub(r'(桃|赤|黄|緑|紫|青)\[CT\]', '[COLOR_CT]', structure3)
        
        level_groups['level3'][structure3].append(template_data)
    
    # Build compressed templates using hierarchical matching
    compressed_templates = []
    processed_indices = set()
    
    # Start with level 3 (most abstract)
    for structure, templates in level_groups['level3'].items():
        if len(templates) > 1:
            indices = [i for i, t in enumerate(template_list) if t in templates]
            if all(idx not in processed_indices for idx in indices):
                compressed_template = {
                    'template': structure,
                    'usage_count': sum(t['usage_count'] for t in templates),
                    'variables': sorted(set().union(*[t['variables'] for t in templates])),
                    'abilities': [ability for t in templates for ability in t['abilities'][:5]],
                    'compressed_from': len(templates),
                    'compression_level': 3
                }
                compressed_templates.append(compressed_template)
                processed_indices.update(indices)
    
    # Then level 2 for remaining
    for structure, templates in level_groups['level2'].items():
        indices = [i for i, t in enumerate(template_list) if t in templates]
        if len(indices) > 1 and all(idx not in processed_indices for idx in indices):
            compressed_template = {
                'template': structure,
                'usage_count': sum(t['usage_count'] for t in templates),
                'variables': sorted(set().union(*[t['variables'] for t in templates])),
                'abilities': [ability for t in templates for ability in t['abilities'][:5]],
                'compressed_from': len(templates),
                'compression_level': 2
            }
            compressed_templates.append(compressed_template)
            processed_indices.update(indices)
    
    # Add remaining templates (level 1)
    for i, template_data in enumerate(template_list):
        if i not in processed_indices:
            compressed_template = {
                'template': template_data['template'],
                'usage_count': template_data['usage_count'],
                'variables': template_data['variables'],
                'abilities': template_data['abilities'][:5],
                'compressed_from': 1,
                'compression_level': 1
            }
            compressed_templates.append(compressed_template)
    
    compressed_templates.sort(key=lambda x: -x['usage_count'])
    return compressed_templates


def create_expression_template(text: str, terms: dict) -> str:
    """
    Create a template by replacing game terms with placeholders.
    """
    template = text
    
    # Replace all {{}} patterns with [icon] placeholder
    for icon_pattern in terms['icon_patterns']:
        if icon_pattern.startswith('{{'):
            template = template.replace(icon_pattern, '[icon]')
        else:
            # This is just the text content, replace it too
            template = template.replace(icon_pattern, '[icon_text]')
    
    # Replace score modifiers
    for score in terms['score_modifiers']:
        template = template.replace(f'+{score}', '[score_modifier]')
    
    # Replace energy costs
    for energy in terms['energy_costs']:
        e_count = int(energy.replace('E', ''))
        energy_pattern = r'\{\{icon_energy\.png\|E\}\}' * e_count
        template = re.sub(energy_pattern, f'[{energy}]', template)
    
    # Replace group names from 『』 patterns
    for group_name in terms['group_names']:
        template = template.replace(f'『{group_name}』', '[group_name]')
    
    # Replace character names from 「」 patterns
    for char_name in terms['character_names']:
        template = template.replace(f'「{char_name}」', '[character_name]')
    
    # Replace timing modifiers
    for timing in terms['timing_modifiers']:
        template = template.replace(timing, '[timing_modifier]')
    
    # Replace positions
    for position in terms['positions']:
        template = template.replace(position, '[position]')
    
    # Replace numbers first (longest to shortest to avoid partial matches)
    for num in sorted(terms['numbers'], key=len, reverse=True):
        template = template.replace(num + '枚', '[number]')
    
    # Replace card types (longest to shortest)
    for card_type in sorted(terms['card_types'], key=len, reverse=True):
        template = template.replace(card_type, '[card_type]')
    
    # Replace zones (longest to shortest)
    for zone in sorted(terms['zones'], key=len, reverse=True):
        template = template.replace(zone, '[zone]')
    
    # Replace players
    for player in terms['players']:
        template = template.replace(player, '[player]')
    
    return template


def calculate_text_coverage(text: str, terms: dict) -> dict:
    """
    Calculate how much of the text is covered by identified game terms.
    Returns coverage statistics.
    """
    total_chars = len(text)
    covered_positions = set()
    
    # Find all occurrences of each term type and mark positions
    for card_type in terms['card_types']:
        start = 0
        while True:
            pos = text.find(card_type, start)
            if pos == -1:
                break
            for i in range(pos, pos + len(card_type)):
                covered_positions.add(i)
            start = pos + 1
    
    for zone in terms['zones']:
        start = 0
        while True:
            pos = text.find(zone, start)
            if pos == -1:
                break
            for i in range(pos, pos + len(zone)):
                covered_positions.add(i)
            start = pos + 1
    
    for player in terms['players']:
        start = 0
        while True:
            pos = text.find(player, start)
            if pos == -1:
                break
            for i in range(pos, pos + len(player)):
                covered_positions.add(i)
            start = pos + 1
    
    for number in terms['numbers']:
        num_text = number + '枚'
        start = 0
        while True:
            pos = text.find(num_text, start)
            if pos == -1:
                break
            for i in range(pos, pos + len(num_text)):
                covered_positions.add(i)
            start = pos + 1
    
    # New variable types
    for position in terms['positions']:
        start = 0
        while True:
            pos = text.find(position, start)
            if pos == -1:
                break
            for i in range(pos, pos + len(position)):
                covered_positions.add(i)
            start = pos + 1
    
    for timing in terms['timing_modifiers']:
        start = 0
        while True:
            pos = text.find(timing, start)
            if pos == -1:
                break
            for i in range(pos, pos + len(timing)):
                covered_positions.add(i)
            start = pos + 1
    
    for group_name in terms['group_names']:
        group_text = f'『{group_name}』'
        start = 0
        while True:
            pos = text.find(group_text, start)
            if pos == -1:
                break
            for i in range(pos, pos + len(group_text)):
                covered_positions.add(i)
            start = pos + 1
    
    for char_name in terms['character_names']:
        char_text = f'「{char_name}」'
        start = 0
        while True:
            pos = text.find(char_text, start)
            if pos == -1:
                break
            for i in range(pos, pos + len(char_text)):
                covered_positions.add(i)
            start = pos + 1
    
    for energy in terms['energy_costs']:
        e_count = int(energy.replace('E', ''))
        energy_pattern = r'\{\{icon_energy\.png\|E\}\}' * e_count
        start = 0
        while True:
            pos = text.find('{{icon_energy.png|E}}', start)
            if pos == -1:
                break
            for i in range(pos, pos + len('{{icon_energy.png|E}}')):
                covered_positions.add(i)
            start = pos + 1
    
    # New: icon patterns
    for icon_pattern in terms['icon_patterns']:
        if icon_pattern.startswith('{{'):
            start = 0
            while True:
                pos = text.find(icon_pattern, start)
                if pos == -1:
                    break
                for i in range(pos, pos + len(icon_pattern)):
                    covered_positions.add(i)
                start = pos + 1
    
    # New: score modifiers
    for score in terms['score_modifiers']:
        score_text = f'+{score}'
        start = 0
        while True:
            pos = text.find(score_text, start)
            if pos == -1:
                break
            for i in range(pos, pos + len(score_text)):
                covered_positions.add(i)
            start = pos + 1
    
    covered_chars = len(covered_positions)
    coverage_percent = (covered_chars / total_chars * 100) if total_chars > 0 else 0
    
    return {
        'total_chars': total_chars,
        'covered_chars': covered_chars,
        'coverage_percent': round(coverage_percent, 2)
    }


def collect_unique_variables(all_abilities: list) -> dict:
    """
    Collect all unique game term variables found across all abilities.
    """
    unique_vars = {
        'card_types': set(),
        'zones': set(),
        'players': set(),
        'numbers': set(),
        'positions': set(),
        'timing_modifiers': set(),
        'group_names': set(),
        'energy_costs': set(),
        'character_names': set(),
        'score_modifiers': set(),
        'icon_patterns': set()
    }
    
    for ability in all_abilities:
        effect = ability['effect']
        cost, effect_text = split_cost_effect(effect)
        
        # Extract terms from both cost and effect
        cost_terms = extract_game_terms(cost)
        effect_terms = extract_game_terms(effect_text)
        
        # Collect unique variables
        unique_vars['card_types'].update(cost_terms['card_types'])
        unique_vars['card_types'].update(effect_terms['card_types'])
        unique_vars['zones'].update(cost_terms['zones'])
        unique_vars['zones'].update(effect_terms['zones'])
        unique_vars['players'].update(cost_terms['players'])
        unique_vars['players'].update(effect_terms['players'])
        unique_vars['numbers'].update(cost_terms['numbers'])
        unique_vars['numbers'].update(effect_terms['numbers'])
        unique_vars['positions'].update(cost_terms['positions'])
        unique_vars['positions'].update(effect_terms['positions'])
        unique_vars['timing_modifiers'].update(cost_terms['timing_modifiers'])
        unique_vars['timing_modifiers'].update(effect_terms['timing_modifiers'])
        unique_vars['group_names'].update(cost_terms['group_names'])
        unique_vars['group_names'].update(effect_terms['group_names'])
        unique_vars['energy_costs'].update(cost_terms['energy_costs'])
        unique_vars['energy_costs'].update(effect_terms['energy_costs'])
        unique_vars['character_names'].update(cost_terms['character_names'])
        unique_vars['character_names'].update(effect_terms['character_names'])
        unique_vars['score_modifiers'].update(cost_terms['score_modifiers'])
        unique_vars['score_modifiers'].update(effect_terms['score_modifiers'])
        unique_vars['icon_patterns'].update(cost_terms['icon_patterns'])
        unique_vars['icon_patterns'].update(effect_terms['icon_patterns'])
    
    # Convert sets to sorted lists
    return {
        'card_types': sorted(list(unique_vars['card_types'])),
        'zones': sorted(list(unique_vars['zones'])),
        'players': sorted(list(unique_vars['players'])),
        'numbers': sorted(list(unique_vars['numbers'])),
        'positions': sorted(list(unique_vars['positions'])),
        'timing_modifiers': sorted(list(unique_vars['timing_modifiers'])),
        'group_names': sorted(list(unique_vars['group_names'])),
        'energy_costs': sorted(list(unique_vars['energy_costs'])),
        'character_names': sorted(list(unique_vars['character_names'])),
        'score_modifiers': sorted(list(unique_vars['score_modifiers'])),
        'icon_patterns': sorted(list(unique_vars['icon_patterns']))
    }


def generate_coverage_log(all_abilities: list, output_file: Path):
    """
    Generate a log file with text coverage statistics and unique variables.
    """
    unique_vars = collect_unique_variables(all_abilities)
    
    # Calculate coverage for each ability
    coverage_stats = []
    total_coverage = 0
    for ability in all_abilities:
        effect = ability['effect']
        cost, effect_text = split_cost_effect(effect)
        
        cost_terms = extract_game_terms(cost)
        effect_terms = extract_game_terms(effect_text)
        
        cost_coverage = calculate_text_coverage(cost, cost_terms)
        effect_coverage = calculate_text_coverage(effect_text, effect_terms)
        
        combined_coverage = calculate_text_coverage(cost + '：' + effect_text, {
            'card_types': cost_terms['card_types'] + effect_terms['card_types'],
            'zones': cost_terms['zones'] + effect_terms['zones'],
            'players': cost_terms['players'] + effect_terms['players'],
            'numbers': cost_terms['numbers'] + effect_terms['numbers'],
            'positions': cost_terms['positions'] + effect_terms['positions'],
            'timing_modifiers': cost_terms['timing_modifiers'] + effect_terms['timing_modifiers'],
            'group_names': cost_terms['group_names'] + effect_terms['group_names'],
            'energy_costs': cost_terms['energy_costs'] + effect_terms['energy_costs'],
            'character_names': cost_terms['character_names'] + effect_terms['character_names'],
            'score_modifiers': cost_terms['score_modifiers'] + effect_terms['score_modifiers'],
            'icon_patterns': cost_terms['icon_patterns'] + effect_terms['icon_patterns']
        })
        
        coverage_stats.append({
            'full_text': ability['full_text'],
            'cost_coverage': cost_coverage,
            'effect_coverage': effect_coverage,
            'combined_coverage': combined_coverage
        })
        
        total_coverage += combined_coverage['coverage_percent']
    
    avg_coverage = total_coverage / len(all_abilities) if all_abilities else 0
    
    # Group by templates
    template_groups = defaultdict(lambda: {'count': 0, 'variables': set(), 'abilities': []})
    
    # Build a lookup for unique abilities to get card_examples
    unique_abilities_lookup = {}
    for ability in all_abilities:
        unique_abilities_lookup[ability['full_text']] = ability
    
    for ability in all_abilities:
        effect = ability['effect']
        cost, effect_text = split_cost_effect(effect)
        
        cost_terms = extract_game_terms(cost)
        effect_terms = extract_game_terms(effect_text)
        
        cost_template = create_expression_template(cost, cost_terms)
        effect_template = create_expression_template(effect_text, effect_terms)
        
        combined_template = f"{cost_template} ： {effect_template}"
        
        # Collect all variables used in this template
        all_vars = set()
        all_vars.update(cost_terms['card_types'])
        all_vars.update(cost_terms['zones'])
        all_vars.update(cost_terms['players'])
        all_vars.update(cost_terms['numbers'])
        all_vars.update(cost_terms['positions'])
        all_vars.update(cost_terms['timing_modifiers'])
        all_vars.update(cost_terms['group_names'])
        all_vars.update(cost_terms['energy_costs'])
        all_vars.update(cost_terms['character_names'])
        all_vars.update(cost_terms['score_modifiers'])
        all_vars.update(cost_terms['icon_patterns'])
        all_vars.update(effect_terms['card_types'])
        all_vars.update(effect_terms['zones'])
        all_vars.update(effect_terms['players'])
        all_vars.update(effect_terms['numbers'])
        all_vars.update(effect_terms['positions'])
        all_vars.update(effect_terms['timing_modifiers'])
        all_vars.update(effect_terms['group_names'])
        all_vars.update(effect_terms['energy_costs'])
        all_vars.update(effect_terms['character_names'])
        all_vars.update(effect_terms['score_modifiers'])
        all_vars.update(effect_terms['icon_patterns'])
        
        template_groups[combined_template]['count'] += 1
        template_groups[combined_template]['variables'].update(all_vars)
        
        # Add full ability data structure
        template_groups[combined_template]['abilities'].append({
            'full_text': ability['full_text'],
            'triggers': ability['triggers'],
            'effect': ability['effect'],
            'trigger_count': ability['trigger_count'],
            'card_count': 1,  # Each ability instance counts as 1
            'card_examples': [f"{ability['card_id']} | {ability['card_name']} (ab#{ability['ability_index']})"]
        })
    
    # Convert to list and sort by usage
    template_list = []
    for template, data in template_groups.items():
        template_list.append({
            'template': template,
            'usage_count': data['count'],
            'variables': sorted(list(data['variables'])),
            'abilities': data['abilities'][:5]  # Limit to 5 examples
        })
    
    template_list.sort(key=lambda x: -x['usage_count'])
    
    # Compress templates
    compressed_templates = compress_templates(template_list)
    compressed_templates.sort(key=lambda x: -x['usage_count'])
    
    # Count variable usage
    variable_counts = defaultdict(int)
    for ability in all_abilities:
        effect = ability['effect']
        cost, effect_text = split_cost_effect(effect)
        
        cost_terms = extract_game_terms(cost)
        effect_terms = extract_game_terms(effect_text)
        
        for var in cost_terms['card_types'] + effect_terms['card_types']:
            variable_counts[f"card_type:{var}"] += 1
        for var in cost_terms['zones'] + effect_terms['zones']:
            variable_counts[f"zone:{var}"] += 1
        for var in cost_terms['players'] + effect_terms['players']:
            variable_counts[f"player:{var}"] += 1
        for var in cost_terms['numbers'] + effect_terms['numbers']:
            variable_counts[f"number:{var}"] += 1
        for var in cost_terms['positions'] + effect_terms['positions']:
            variable_counts[f"position:{var}"] += 1
        for var in cost_terms['timing_modifiers'] + effect_terms['timing_modifiers']:
            variable_counts[f"timing:{var}"] += 1
        for var in cost_terms['group_names'] + effect_terms['group_names']:
            variable_counts[f"group:{var}"] += 1
        for var in cost_terms['energy_costs'] + effect_terms['energy_costs']:
            variable_counts[f"energy:{var}"] += 1
        for var in cost_terms['character_names'] + effect_terms['character_names']:
            variable_counts[f"character:{var}"] += 1
        for var in cost_terms['score_modifiers'] + effect_terms['score_modifiers']:
            variable_counts[f"score:+{var}"] += 1
        for var in cost_terms['icon_patterns'] + effect_terms['icon_patterns']:
            variable_counts[f"icon:{var}"] += 1
    
    log_data = {
        'schema': 'ability_coverage_log.v4',
        'generated_at': datetime.now().isoformat(),
        'coverage_statistics': {
            'total_abilities': len(all_abilities),
            'average_coverage_percent': round(avg_coverage, 2)
        },
        'unique_variables': unique_vars,
        'variable_counts': dict(sorted(variable_counts.items(), key=lambda x: -x[1])),
        'template_statistics': {
            'original_templates': len(template_list),
            'compressed_templates': len(compressed_templates),
            'compression_ratio': f"{len(compressed_templates)}/{len(template_list)}"
        },
        'templates': compressed_templates
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)
    
    print(f"Coverage log written to {output_file}")
    print(f"Average text coverage: {avg_coverage:.2f}%")
    print(f"Original templates: {len(template_list)}")
    print(f"Compressed templates: {len(compressed_templates)}")
    print(f"Compression ratio: {len(compressed_templates)}/{len(template_list)}")
    print(f"Total variables: {len(variable_counts)}")



def extract_trigger(text: str) -> tuple[list[str], str]:
    """
    Extract trigger(s) and effect text from ability text.
    Only extracts triggers at the very start of the text.
    Excludes cost icons (energy, hearts, blades, etc.) from triggers.
    
    Returns: (list of triggers, effect text)
    """
    # Pattern to match trigger icons: {{icon.png|trigger_name}}
    trigger_pattern = re.compile(r'\{\{([^|]+)\|([^}]+)\}\}')
    
    # Cost icon patterns to exclude from triggers
    cost_icon_patterns = [
        'icon_energy', 'heart', 'icon_blade', 'icon_b_all', 'icon_score', 'center'
    ]
    
    # Find all triggers at the start
    triggers = []
    trigger_end = 0
    trigger_matches = list(trigger_pattern.finditer(text))
    
    if not trigger_matches:
        return [], text
    
    # Only consider triggers at the very start (before any non-icon, non-whitespace, non-/ text)
    valid_triggers = []
    pos = 0
    for match in trigger_matches:
        # Check if there's any non-trigger text before this match
        before = text[pos:match.start()]
        if before.strip() and before.strip() != '/':
            # Found non-trigger text, stop here
            break
        
        # Check if this is a cost icon (not a trigger)
        icon_file = match.group(1)
        if any(cost_pattern in icon_file for cost_pattern in cost_icon_patterns):
            # This is a cost icon, not a trigger
            pos = match.end()
            continue
        
        valid_triggers.append(match)
        pos = match.end()
    
    if not valid_triggers:
        return [], text
    
    # Check if triggers are separated by /
    for i in range(len(valid_triggers) - 1):
        current_end = valid_triggers[i].end()
        next_start = valid_triggers[i + 1].start()
        # Check if there's a / between triggers with no other text
        between = text[current_end:next_start].strip()
        if between == '/':
            # This is a multi-trigger ability
            triggers = [m.group(2) for m in valid_triggers]
            trigger_end = valid_triggers[-1].end()
            effect = text[trigger_end:].lstrip('：')
            return triggers, effect
    
    # Single trigger case
    first_trigger = valid_triggers[0]
    triggers = [first_trigger.group(2)]
    trigger_end = first_trigger.end()
    effect = text[trigger_end:].lstrip('：')
    
    return triggers, effect


def extract_abilities_from_card(card_id: str, card: dict) -> list[dict]:
    """
    Extract all abilities from a single card.
    Handles continuation lines starting with ・ as part of same ability.
    """
    ability_text = card.get("ability", "")
    if not ability_text or not isinstance(ability_text, str):
        return []
    
    abilities = []
    # Split by newline to get individual abilities
    ability_parts = ability_text.split('\n')
    
    for part in ability_parts:
        part = part.strip()
        if not part:
            continue
        
        # Check if this is a continuation line (starts with ・)
        if part.startswith('・'):
            # Append to previous ability
            if abilities:
                abilities[-1]["full_text"] += "\n" + part
                abilities[-1]["effect"] += "\n" + part
            continue
        
        triggers, effect = extract_trigger(part)
        
        abilities.append({
            "card_id": card_id,
            "card_name": card.get("name", ""),
            "full_text": part,
            "triggers": triggers,
            "effect": effect,
            "trigger_count": len(triggers),
            "ability_index": len(abilities),  # Track which ability this is (ab#0, ab#1, etc.)
        })
    
    return abilities


def extract_all_abilities(cards_file: Path) -> dict:
    """
    Extract all abilities from cards.json.
    """
    with open(cards_file, encoding='utf-8') as f:
        cards = json.load(f)
    
    all_abilities = []
    ability_groups = defaultdict(list)  # Group by full ability text
    
    for card_id, card in cards.items():
        abilities = extract_abilities_from_card(card_id, card)
        for ability in abilities:
            all_abilities.append(ability)
            # Format card example as "card_id | card_name (ab#index)"
            card_example = f"{card_id} | {card.get('name', '')} (ab#{ability['ability_index']})"
            ability_groups[ability["full_text"]].append(card_example)
    
    # Build unique abilities with card examples
    unique_abilities = []
    for full_text, card_examples in ability_groups.items():
        # Get the first occurrence to extract triggers/effect
        sample = next(a for a in all_abilities if a["full_text"] == full_text)
        
        unique_abilities.append({
            "full_text": full_text,
            "triggers": sample["triggers"],
            "effect": sample["effect"],
            "trigger_count": sample["trigger_count"],
            "card_count": len(card_examples),
            "card_examples": card_examples[:10],  # Limit to 10 examples
        })
    
    # Sort by card count (most common first)
    unique_abilities.sort(key=lambda x: -x["card_count"])
    
    return {
        "schema": "extracted_abilities.v1",
        "generated_at": datetime.now().isoformat(),
        "source_file": str(cards_file),
        "statistics": {
            "total_cards": len(cards),
            "cards_with_abilities": len([c for c in cards.values() if c.get("ability")]),
            "total_abilities": len(all_abilities),
            "unique_abilities": len(unique_abilities),
        },
        "unique_abilities": unique_abilities,
        "all_abilities": all_abilities,
    }


def test_parsing():
    test_ability = "{{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室からライブカードを1枚手札に加える。"
    triggers, effect = extract_trigger(test_ability)
    cost, effect_text = split_cost_effect(effect)
    cost_terms = extract_game_terms(cost)
    effect_terms = extract_game_terms(effect_text)
    
    cost_template = create_expression_template(cost, cost_terms)
    effect_template = create_expression_template(effect_text, effect_terms)
    
    print("=== Test Parsing ===")
    print(f"Original: {test_ability}")
    print(f"Triggers: {triggers}")
    print(f"Cost: {cost}")
    print(f"Cost terms: {cost_terms}")
    print(f"Cost template: {cost_template}")
    print(f"Effect: {effect_text}")
    print(f"Effect terms: {effect_terms}")
    print(f"Effect template: {effect_template}")
    print()


def main():
    # Test parsing on single ability first
    test_parsing()
    
    cards_file = Path("data/cards.json")
    output_file = Path("data/abilities_extracted_from_cards.json")
    coverage_log_file = Path("data/ability_coverage_log.json")
    
    print(f"Extracting abilities from {cards_file}...")
    result = extract_all_abilities(cards_file)
    
    print(f"Found {result['statistics']['total_abilities']} abilities across {result['statistics']['cards_with_abilities']} cards")
    print(f"Unique abilities: {result['statistics']['unique_abilities']}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"Output written to {output_file}")
    
    # Generate coverage log
    print("\nGenerating coverage log...")
    generate_coverage_log(result['all_abilities'], coverage_log_file)


if __name__ == "__main__":
    main()
