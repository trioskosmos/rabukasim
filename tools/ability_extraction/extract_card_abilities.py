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
from difflib import SequenceMatcher


def load_variable_config():
    """Load variable configuration from external config file."""
    config_file = Path("tools/ability_extraction/variable_config.json")
    
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # Fallback to hardcoded values if config doesn't exist
        return {
            'card_types': [
                'このメンバー', 'ライブカード', 'メンバーカード', 'カード',
                'エネルギーカード', 'ライブ中のカード', '成功ライブカード',
                'エネルギーデッキ', 'エネルギー', 'ハート', 'ブレード'
            ],
            'zones': [
                'ステージ', '控え室', '手札', 'デッキ', 'ウェイト',
                'エネルギー置き場', '成功ライブカード置き場', 'エリア'
            ],
            'players': ['自分', '相手'],
            'positions': [
                '【左サイド】', '【右サイド】', '【センター】', '【左】', '【右】', '【中央】',
                'センター', '左サイド', '右サイド'
            ],
            'timing_modifiers': [
                '【ターン1回】', '［ターン1回］', 'ターン1回',
                'ターン2回', '2回', '毎ターン'
            ],
            'group_names': [],
            'character_names': [],
        }


# Load variable configuration
VAR_CONFIG = load_variable_config()

CARD_TYPES = VAR_CONFIG['card_types']
ZONES = VAR_CONFIG['zones']
PLAYERS = VAR_CONFIG['players']
POSITIONS = VAR_CONFIG['positions']
TIMING_MODIFIERS = VAR_CONFIG['timing_modifiers']
GROUP_NAMES = VAR_CONFIG['group_names']
CHARACTER_NAMES = VAR_CONFIG['character_names']
OPTIONAL_MODIFIERS = VAR_CONFIG.get('optional_modifiers', [])

ENERGY_COSTS = []  # Will be extracted from {{icon_energy.png|E}} patterns
SCORE_MODIFIERS = []  # Will be extracted from +1/+2/+3 patterns

# Pre-compiled regex patterns for performance
NUMBER_PATTERN = re.compile(r'[0-9０-９]+')
GROUP_PATTERN = re.compile(r'『([^』]+)』')
ENERGY_PATTERN = re.compile(r'([0-9]+)E')
CHAR_PATTERN = re.compile(r'「([^」]+)」')
SCORE_PATTERN = re.compile(r'[＋+]([0-9]+)')
ICON_PATTERN = re.compile(r'\{\{([^}]+)\}\}')
WHITESPACE_PATTERN = re.compile(r'\s+')
ICON_COUNT_PATTERN = re.compile(r'(\[icon\]\s*)+')
TRIGGER_PATTERN = re.compile(r'\{\{([^|]+)\|([^}]+)\}\}')


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
    Extract game terms from ability text.
    Returns dict with lists of different term types.
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
    
    # Card types
    card_type_patterns = [
        'このメンバー', 'エネルギー', 'エネルギーカード', 'エネルギーデッキ',
        'カード', 'ハート', 'ブレード', 'メンバーカード', 'ライブカード',
        'ライブ中のカード', '成功ライブカード'
    ]
    for card_type in card_type_patterns:
        if card_type in text:
            terms['card_types'].append(card_type)
    
    # Zones
    zone_patterns = [
        'ウェイト', 'エネルギー置き場', 'エリア', 'ステージ', 'デッキ',
        '成功ライブカード置き場', '手札', '控え室'
    ]
    for zone in zone_patterns:
        if zone in text:
            terms['zones'].append(zone)
    
    # Players
    player_patterns = ['自分', '相手']
    for player in player_patterns:
        if player in text:
            terms['players'].append(player)
    
    # Numbers (including full-width)
    numbers = NUMBER_PATTERN.findall(text)
    terms['numbers'].extend(numbers)
    
    # Positions
    position_patterns = POSITIONS
    for position in position_patterns:
        if position in text:
            terms['positions'].append(position)
    
    # Timing modifiers
    timing_patterns = TIMING_MODIFIERS
    for timing in timing_patterns:
        if timing in text:
            terms['timing_modifiers'].append(timing)
    
    # Group names (in brackets)
    group_matches = GROUP_PATTERN.findall(text)
    terms['group_names'].extend(group_matches)
    
    # Energy costs (like 1E, 2E, etc.)
    energy_matches = ENERGY_PATTERN.findall(text)
    for match in energy_matches:
        terms['energy_costs'].append(f"{match}E")
    
    # Character names (in brackets and quotes)
    char_matches = CHAR_PATTERN.findall(text)
    # Filter out score modifiers and other non-character patterns
    for char in char_matches:
        # Skip if it's just a number or score modifier
        if not re.match(r'^[０-９]+$', char) and not re.match(r'^\+', char):
            terms['character_names'].append(char)
    
    # Score modifiers (+1, +2, +3)
    score_matches = SCORE_PATTERN.findall(text)
    terms['score_modifiers'].extend(score_matches)
    
    # All {{}} patterns
    icon_matches = ICON_PATTERN.findall(text)
    terms['icon_patterns'].extend(icon_matches)
    
    return terms


def create_expression_template(text: str, terms: dict) -> tuple[str, list[dict]]:
    """
    Create a template by replacing game terms with placeholders.
    Uses smart variable extraction: groups repeated icons and handles optional modifiers.
    Returns: (template, list of modifier_info dicts with 'pattern' and 'replacement')
    """
    template = text
    modifier_info = []
    
    # Normalize text: strip quotes, normalize commas to full-width, and remove all spaces for consistent comparison
    template = template.strip('"\'')  # Strip leading/trailing quotes
    template = template.replace(',', '、')  # Normalize half-width comma to full-width
    template = WHITESPACE_PATTERN.sub('', template)  # Remove all spaces
    
    # Replace in order of specificity (longer patterns first)
    replacements = []
    
    # Card types
    for card_type in sorted(terms['card_types'], key=len, reverse=True):
        replacements.append((card_type, '[card_type]'))
    
    # Zones
    for zone in sorted(terms['zones'], key=len, reverse=True):
        replacements.append((zone, '[zone]'))
    
    # Players
    for player in sorted(terms['players'], key=len, reverse=True):
        replacements.append((player, '[player]'))
    
    # Numbers
    for number in sorted(terms['numbers'], key=len, reverse=True):
        replacements.append((number, '[number]'))
    
    # Positions
    for position in sorted(terms['positions'], key=len, reverse=True):
        replacements.append((position, '[position]'))
    
    # Timing modifiers
    for timing in sorted(terms['timing_modifiers'], key=len, reverse=True):
        replacements.append((timing, '[timing_modifier]'))
    
    # Group names
    for group in sorted(terms['group_names'], key=len, reverse=True):
        replacements.append((group, '[group_name]'))
    
    # Energy costs
    for energy in sorted(terms['energy_costs'], key=len, reverse=True):
        replacements.append((energy, '[energy_cost]'))
    
    # Character names
    for char in sorted(terms['character_names'], key=len, reverse=True):
        replacements.append((char, '[character_name]'))
    
    # Score modifiers
    for score in sorted(terms['score_modifiers'], key=len, reverse=True):
        replacements.append((f'+{score}', '[score_modifier]'))
    
    # Icon patterns - group repeated icons as count variables
    icon_patterns = sorted(terms['icon_patterns'], key=len, reverse=True)
    for icon in icon_patterns:
        replacements.append((f'{{{{{icon}}}}}', '[icon]'))
    
    # Apply replacements
    for original, placeholder in replacements:
        template = template.replace(original, placeholder)
    
    # Smart: Group repeated [icon] as count variables
    template = ICON_COUNT_PATTERN.sub(lambda m: f'[icon_count:{len(m.group(0).split())}]', template)
    
    # Smart: Handle optional modifiers (group_nameの, ライブ中の, etc.)
    # Track what each modifier replaced for hierarchical compression
    for modifier in sorted(OPTIONAL_MODIFIERS, key=len, reverse=True):
        if modifier in template:
            # Find what precedes/follows the modifier to build full context
            # For example: [group_name] + の = [group_name]の
            template = template.replace(modifier, '[opt_mod]')
            modifier_info.append({'pattern': modifier, 'replacement': '[opt_mod]'})
    
    return template, modifier_info


def _merge_dicts(*dicts):
    """Helper function to merge multiple dictionaries."""
    result = {}
    for d in dicts:
        result.update(d)
    return result


def calculate_template_similarity(template1: str, template2: str) -> float:
    """
    Calculate similarity between two templates as a percentage.
    Uses a simple character-based similarity metric.
    """
    return SequenceMatcher(None, template1, template2).ratio()


def extract_optional_modifiers(template: str, modifier_info: list = None) -> tuple[str, list[str]]:
    """
    Extract optional modifiers from a template and return the base template and list of modifiers.
    modifier_info: list of dicts with 'pattern' and 'replacement' from template creation
    """
    base_template = template
    modifiers_found = []
    
    if not modifier_info:
        # Fallback: extract from template directly
        # Pattern: [placeholder]の[placeholder] -> base: [second_placeholder], modifier: [first_placeholder]の
        modifier_patterns = [
            (r'\[group_name\]\[opt_mod\]', '[group_name]の'),
            (r'\[opt_mod\]', '[opt_mod]'),
        ]
        
        for pattern, modifier in modifier_patterns:
            if re.search(pattern, template):
                base_template = re.sub(pattern, '', base_template)
                modifiers_found.append(modifier)
    else:
        # Use tracked modifier info
        for mod in modifier_info:
            pattern = mod['pattern']
            replacement = mod['replacement']
            # Remove the replacement from template to get base
            base_template = base_template.replace(replacement, '')
            modifiers_found.append(pattern)
    
    # Clean up extra spaces
    base_template = WHITESPACE_PATTERN.sub(' ', base_template).strip()
    
    return base_template, modifiers_found


def compress_templates(template_list: list, all_abilities: list = None) -> list:
    """
    Compress templates by grouping identical templates together.
    Then apply hierarchical compression based on optional modifiers.
    """
    # Level 1: Group identical templates
    template_groups = defaultdict(list)
    
    for template_data in template_list:
        template = template_data['template']
        template_groups[template].append(template_data)
    
    # Build level 1 compressed templates
    level1_templates = []
    for template, templates in template_groups.items():
        if len(templates) > 1:
            compressed_template = {
                'template': template,
                'usage_count': sum(t['usage_count'] for t in templates),
                'variables': sorted(set().union(*[t['variables'] for t in templates])),
                'abilities': [ability for t in templates for ability in t['abilities'][:5]],
                'compressed_from': len(templates),
                'compression_level': 1,
                'modifiers': templates[0].get('modifiers', [])
            }
            level1_templates.append(compressed_template)
        else:
            # Add uncompressed templates - use the single template from this group
            level1_templates.append({
                'template': template,
                'usage_count': templates[0]['usage_count'],
                'variables': templates[0]['variables'],
                'abilities': templates[0]['abilities'],
                'compressed_from': 1,
                'compression_level': 1,
                'modifiers': templates[0].get('modifiers', [])
            })
    
    # Analyze template similarity on level1 templates (after grouping identical ones)
    # to understand what patterns exist
    similarity_report = analyze_template_similarity(level1_templates, threshold=0.90)
    print(f"\n=== Template Similarity Analysis ===")
    print(f"Found {len(similarity_report)} highly similar template pairs (>=90% similarity)")
    for i, (t1, t2, sim, data1, data2) in enumerate(similarity_report[:10]):
        print(f"  {i+1}. Sim {sim:.2%}: '{t1}' vs '{t2}'")
    
    # Only output similar pairs if there are any (not all identical)
    if len(similarity_report) > 0 and len(similarity_report) < len(level1_templates) * len(level1_templates) / 2:
        with open("template_similarity_report.txt", "w", encoding="utf-8") as f:
            f.write(f"Template Similarity Report\n")
            f.write(f"===========================\n\n")
            f.write(f"Found {len(similarity_report)} highly similar template pairs (>=90% similarity)\n\n")
            for i, (t1, t2, sim, data1, data2) in enumerate(similarity_report):
                f.write(f"{i+1}. Sim {sim:.2%}\n")
                f.write(f"Template A: {t1}\n")
                f.write(f"Ability A examples: {data1.get('abilities', [])[:3]}\n")
                f.write(f"Template B: {t2}\n")
                f.write(f"Ability B examples: {data2.get('abilities', [])[:3]}\n")
                f.write(f"\n")
        print(f"Similarity report written to template_similarity_report.txt")
    else:
        print("Skipping similarity report - all templates are identical or no similar pairs found")
    
    # Level 2: Skip hierarchical compression for now - focus on decomposition first
    # The similar templates have structural differences that shouldn't be grouped
    level2_templates = level1_templates
    
    level2_templates.sort(key=lambda x: -x['usage_count'])
    return level2_templates


def is_optional_modifier(text: str) -> bool:
    """
    Check if text looks like an optional modifier pattern.
    Optional modifiers are typically short and contain placeholders.
    """
    # Check if it's a placeholder pattern
    placeholder_patterns = [
        '[group_name]', '[opt_mod]', '[card_type]', '[zone]', '[player]'
    ]
    
    # If it's very short and contains placeholders, it's likely an optional modifier
    if len(text) <= 20 and any(p in text for p in placeholder_patterns):
        return True
    
    # If it starts with a placeholder, it's likely a prefix modifier
    if any(text.startswith(p) for p in placeholder_patterns):
        return True
    
    return False


def find_common_base(templates: list) -> str:
    """
    Find the common base template by removing differences.
    Uses longest common subsequence approach.
    """
    if not templates:
        return ""
    if len(templates) == 1:
        return templates[0]
    
    # Find common prefix
    def common_prefix(s1, s2):
        min_len = min(len(s1), len(s2))
        for i in range(min_len):
            if s1[i] != s2[i]:
                return s1[:i]
        return s1[:min_len]
    
    # Find common suffix
    def common_suffix(s1, s2):
        min_len = min(len(s1), len(s2))
        for i in range(1, min_len + 1):
            if s1[-i] != s2[-i]:
                return s1[-i+1:] if i > 1 else ""
        return s1[-min_len:]
    
    # Start with first template as base
    base = templates[0]
    
    for template in templates[1:]:
        # Find common prefix and suffix
        prefix = common_prefix(base, template)
        suffix = common_suffix(base, template)
        
        # Build base from prefix + suffix
        # This is a simplified approach - might need refinement
        if len(prefix) + len(suffix) > len(base):
            base = prefix + suffix
        elif len(prefix) > len(base) * 0.5:
            base = prefix
        else:
            # Keep the shorter template as base
            base = template if len(template) < len(base) else base
    
    return base


def find_difference(base: str, template: str) -> str:
    """
    Find the difference between base and template.
    Returns the portion that's in template but not in base.
    """
    if base == template:
        return ""
    
    # Simple approach: find where they differ
    # This is a simplified diff - could be improved
    for i in range(min(len(base), len(template))):
        if base[i] != template[i]:
            # Found difference point
            # Return the rest of template from this point
            return template[i:]
    
    # If one is prefix of the other, return the suffix
    if len(template) > len(base):
        return template[len(base):]
    
    return ""


def analyze_template_similarity(templates: list, threshold: float = 0.90) -> list:
    """
    Analyze similarity between templates and return pairs above threshold.
    Returns list of (template1, template2, similarity_score, template1_data, template2_data) tuples.
    """
    similar_pairs = []
    
    for i in range(len(templates)):
        for j in range(i + 1, len(templates)):
            t1 = templates[i]['template']
            t2 = templates[j]['template']
            
            similarity = calculate_template_similarity(t1, t2)
            if similarity >= threshold:
                similar_pairs.append((t1, t2, similarity, templates[i], templates[j]))
    
    # Sort by similarity descending
    similar_pairs.sort(key=lambda x: -x[2])
    return similar_pairs




def _mark_covered_positions(text: str, term_list: list, covered_positions: set, transform_func=None):
    """
    Helper function to mark covered positions for a list of terms.
    transform_func: optional function to transform term before searching (e.g., add brackets)
    """
    for term in term_list:
        search_text = transform_func(term) if transform_func else term
        start = 0
        while True:
            pos = text.find(search_text, start)
            if pos == -1:
                break
            for i in range(pos, pos + len(search_text)):
                covered_positions.add(i)
            start = pos + 1


def calculate_text_coverage(text: str, terms: dict) -> dict:
    """
    Calculate how much of the text is covered by identified game terms.
    Returns coverage statistics.
    """
    total_chars = len(text)
    covered_positions = set()
    
    # Find all occurrences of each term type and mark positions using helper function
    _mark_covered_positions(text, terms.get('card_types', []), covered_positions)
    _mark_covered_positions(text, terms.get('zones', []), covered_positions)
    _mark_covered_positions(text, terms.get('players', []), covered_positions)
    _mark_covered_positions(text, terms.get('numbers', []), covered_positions, lambda n: n + '枚')
    _mark_covered_positions(text, terms.get('positions', []), covered_positions)
    _mark_covered_positions(text, terms.get('timing_modifiers', []), covered_positions)
    _mark_covered_positions(text, terms.get('group_names', []), covered_positions, lambda g: f'『{g}』')
    _mark_covered_positions(text, terms.get('character_names', []), covered_positions, lambda c: f'「{c}」')
    _mark_covered_positions(text, terms.get('score_modifiers', []), covered_positions, lambda s: f'+{s}')
    
    # Energy costs (special handling for multiple energy icons)
    for energy in terms.get('energy_costs', []):
        e_count = int(energy.replace('E', ''))
        start = 0
        while True:
            pos = text.find('{{icon_energy.png|E}}', start)
            if pos == -1:
                break
            for i in range(pos, pos + len('{{icon_energy.png|E}}')):
                covered_positions.add(i)
            start = pos + 1
    
    # Icon patterns
    for icon_pattern in terms.get('icon_patterns', []):
        if icon_pattern.startswith('{{'):
            _mark_covered_positions(text, [icon_pattern], covered_positions)
    
    # Additional term types (if present)
    _mark_covered_positions(text, terms.get('actions', []), covered_positions)
    _mark_covered_positions(text, terms.get('placements', []), covered_positions)
    _mark_covered_positions(text, terms.get('gains', []), covered_positions)
    
    covered_chars = len(covered_positions)
    coverage_percent = (covered_chars / total_chars * 100) if total_chars > 0 else 0
    
    return {
        'total_chars': total_chars,
        'covered_chars': covered_chars,
        'coverage_percent': round(coverage_percent, 2)
    }


def collect_unique_variables(all_abilities: list) -> dict:
    """
    Collect all unique game term variables from all abilities.
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
        cost, effect_text = split_cost_effect(ability['effect'])
        cost_terms = extract_game_terms(cost)
        effect_terms = extract_game_terms(effect_text)
        
        # Collect from cost
        unique_vars['card_types'].update(cost_terms['card_types'])
        unique_vars['zones'].update(cost_terms['zones'])
        unique_vars['players'].update(cost_terms['players'])
        unique_vars['numbers'].update(cost_terms['numbers'])
        unique_vars['positions'].update(cost_terms['positions'])
        unique_vars['timing_modifiers'].update(cost_terms['timing_modifiers'])
        unique_vars['group_names'].update(cost_terms['group_names'])
        unique_vars['energy_costs'].update(cost_terms['energy_costs'])
        unique_vars['character_names'].update(cost_terms['character_names'])
        unique_vars['score_modifiers'].update(cost_terms['score_modifiers'])
        unique_vars['icon_patterns'].update(cost_terms['icon_patterns'])
        
        # Collect from effect
        unique_vars['card_types'].update(effect_terms['card_types'])
        unique_vars['zones'].update(effect_terms['zones'])
        unique_vars['players'].update(effect_terms['players'])
        unique_vars['numbers'].update(effect_terms['numbers'])
        unique_vars['positions'].update(effect_terms['positions'])
        unique_vars['timing_modifiers'].update(effect_terms['timing_modifiers'])
        unique_vars['group_names'].update(effect_terms['group_names'])
        unique_vars['energy_costs'].update(effect_terms['energy_costs'])
        unique_vars['character_names'].update(effect_terms['character_names'])
        unique_vars['score_modifiers'].update(effect_terms['score_modifiers'])
        unique_vars['icon_patterns'].update(effect_terms['icon_patterns'])
    
    return {k: sorted(list(v)) for k, v in unique_vars.items()}


def generate_coverage_log(all_abilities: list, output_file: Path):
    """
    Generate a log file with text coverage statistics and unique variables.
    """
    unique_vars = collect_unique_variables(all_abilities)
    
    # Calculate coverage for each ability and cache term extraction results
    coverage_stats = []
    total_coverage = 0
    term_cache = {}  # Cache for term extraction results
    
    for ability in all_abilities:
        effect = ability['effect']
        cost, effect_text = split_cost_effect(effect)
        
        # Use cached results if available
        cache_key_cost = f"{ability['full_text']}_cost"
        cache_key_effect = f"{ability['full_text']}_effect"
        
        if cache_key_cost in term_cache:
            cost_terms = term_cache[cache_key_cost]
        else:
            cost_terms = extract_game_terms(cost)
            term_cache[cache_key_cost] = cost_terms
            
        if cache_key_effect in term_cache:
            effect_terms = term_cache[cache_key_effect]
        else:
            effect_terms = extract_game_terms(effect_text)
            term_cache[cache_key_effect] = effect_terms
        
        cost_coverage = calculate_text_coverage(cost, cost_terms)
        effect_coverage = calculate_text_coverage(effect_text, effect_terms)
        
        combined_coverage = calculate_text_coverage(cost + '：' + effect_text, _merge_dicts(cost_terms, effect_terms))
        
        coverage_stats.append({
            'full_text': ability['full_text'],
            'cost_coverage': cost_coverage,
            'effect_coverage': effect_coverage,
            'combined_coverage': combined_coverage
        })
        
        total_coverage += combined_coverage['coverage_percent']
    
    avg_coverage = total_coverage / len(all_abilities) if all_abilities else 0
    
    # Group by templates
    template_groups = defaultdict(lambda: {'count': 0, 'variables': set(), 'modifiers': [], 'abilities': []})
    
    # Build a lookup for unique abilities to get card_examples
    unique_abilities_lookup = {}
    for ability in all_abilities:
        unique_abilities_lookup[ability['full_text']] = ability
    
    for ability in all_abilities:
        effect = ability['effect']
        cost, effect_text = split_cost_effect(effect)
        
        # Use cached results if available
        cache_key_cost = f"{ability['full_text']}_cost"
        cache_key_effect = f"{ability['full_text']}_effect"
        
        if cache_key_cost in term_cache:
            cost_terms = term_cache[cache_key_cost]
        else:
            cost_terms = extract_game_terms(cost)
            term_cache[cache_key_cost] = cost_terms
            
        if cache_key_effect in term_cache:
            effect_terms = term_cache[cache_key_effect]
        else:
            effect_terms = extract_game_terms(effect_text)
            term_cache[cache_key_effect] = effect_terms
        
        cost_template, cost_modifiers = create_expression_template(cost, cost_terms)
        effect_template, effect_modifiers = create_expression_template(effect_text, effect_terms)
        
        combined_template = f"{cost_template} ： {effect_template}"
        # Normalize combined template to be consistent with create_expression_template
        combined_template = combined_template.strip('"\'')
        combined_template = WHITESPACE_PATTERN.sub('', combined_template)
        all_modifiers = cost_modifiers + effect_modifiers
        
        # Add template to ability data
        ability['cost_template'] = cost_template
        ability['effect_template'] = effect_template
        ability['combined_template'] = combined_template
        ability['cost_terms'] = cost_terms
        ability['effect_terms'] = effect_terms
        ability['modifiers'] = all_modifiers
        
        # Collect all variables used in this template
        all_vars = set()
        term_keys = ['card_types', 'zones', 'players', 'numbers', 'positions', 'timing_modifiers', 
                     'group_names', 'energy_costs', 'character_names', 'score_modifiers', 'icon_patterns']
        for key in term_keys:
            all_vars.update(cost_terms[key])
            all_vars.update(effect_terms[key])
        
        template_groups[combined_template]['count'] += 1
        template_groups[combined_template]['variables'].update(all_vars)
        template_groups[combined_template]['modifiers'].extend(all_modifiers)
        
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
            'abilities': data['abilities'][:5],  # Limit to 5 examples
            'modifiers': list(data['modifiers'])
        })
    
    template_list.sort(key=lambda x: -x['usage_count'])
    
    # Apply hierarchical compression with similarity analysis
    compressed_templates = compress_templates(template_list, all_abilities)
    
    # Count variable usage
    variable_counts = defaultdict(int)
    for ability in all_abilities:
        effect = ability['effect']
        cost, effect_text = split_cost_effect(effect)
        
        # Use cached results if available
        cache_key_cost = f"{ability['full_text']}_cost"
        cache_key_effect = f"{ability['full_text']}_effect"
        
        if cache_key_cost in term_cache:
            cost_terms = term_cache[cache_key_cost]
        else:
            cost_terms = extract_game_terms(cost)
            term_cache[cache_key_cost] = cost_terms
            
        if cache_key_effect in term_cache:
            effect_terms = term_cache[cache_key_effect]
        else:
            effect_terms = extract_game_terms(effect_text)
            term_cache[cache_key_effect] = effect_terms
        
        # Count variable usage using a loop over term types
        term_prefix_map = {
            'card_types': 'card_type',
            'zones': 'zone',
            'players': 'player',
            'numbers': 'number',
            'positions': 'position',
            'timing_modifiers': 'timing',
            'group_names': 'group',
            'energy_costs': 'energy',
            'character_names': 'character',
            'score_modifiers': 'score:+',
            'icon_patterns': 'icon'
        }
        for key, prefix in term_prefix_map.items():
            for var in cost_terms[key] + effect_terms[key]:
                variable_counts[f"{prefix}{var}"] += 1
    
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
    # Cost icon patterns to exclude from triggers
    cost_icon_patterns = [
        'icon_energy', 'heart', 'icon_blade', 'icon_b_all', 'icon_score', 'center'
    ]
    
    # Find all triggers at the start
    triggers = []
    trigger_end = 0
    trigger_matches = list(TRIGGER_PATTERN.finditer(text))
    
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
        
        # Generate templates
        cost, effect_text = split_cost_effect(sample["effect"])
        cost_terms = extract_game_terms(cost)
        effect_terms = extract_game_terms(effect_text)
        cost_template, cost_modifiers = create_expression_template(cost, cost_terms)
        effect_template, effect_modifiers = create_expression_template(effect_text, effect_terms)
        combined_template = f"{cost_template} ： {effect_template}"
        
        unique_abilities.append({
            "full_text": full_text,
            "triggers": sample["triggers"],
            "effect": sample["effect"],
            "trigger_count": sample["trigger_count"],
            "card_count": len(card_examples),
            "card_examples": card_examples[:10],  # Limit to 10 examples
            "cost_template": cost_template,
            "effect_template": effect_template,
            "combined_template": combined_template,
            "cost_terms": cost_terms,
            "effect_terms": effect_terms,
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
