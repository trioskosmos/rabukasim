# IMPORTANT: Ability-Level DSL Parser
# - Parses full card abilities (not just individual clauses)
# - Preserves structure: trigger → conditions → effects → options
# - Handles bullet-point choice structures
# - Maintains relationships between ability components
import json
import re
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional

# Load data
data = json.load(open('../data/abilities_from_cards.json', encoding='utf-8'))
abilities = data['abilities']

# Icon token regex
ICON_TOKEN_RE = re.compile(r'\{\{([^|]+)\|([^}]+)\}\}')

# Trigger mapping
TRIGGER_MAP = {
    0: "CONSTANT",
    1: "ON_PLAY",
    2: "LIVE_START",
    3: "LIVE_SUCCESS",
    4: "ACTIVATED",
    5: "ON_DISCARD",
    6: "WHEN",
    7: "LIVE_END",
    8: "SCORE_CALCULATION",
}

def extract_trigger_icon(text: str) -> Optional[str]:
    """Extract trigger icon from ability text"""
    match = ICON_TOKEN_RE.search(text)
    if match:
        return match.group(0)
    return None

def split_into_components(text: str) -> Dict[str, Any]:
    """Split ability into structural components"""
    components = {
        'trigger': None,
        'condition': None,
        'main_effect': None,
        'options': [],
    }
    
    # Extract trigger icon
    trigger_icon = extract_trigger_icon(text)
    if trigger_icon:
        components['trigger'] = trigger_icon
        text = text.replace(trigger_icon, '', 1).strip()
    
    # Split by newlines to identify bullet points
    lines = text.split('\n')
    
    # Check for bullet points (options)
    bullet_points = []
    main_lines = []
    for line in lines:
        if line.strip().startswith('・'):
            bullet_points.append(line.strip()[1:].strip())
        else:
            main_lines.append(line.strip())
    
    if bullet_points:
        components['options'] = bullet_points
        main_text = ''.join(main_lines)
    else:
        main_text = ''.join(main_lines)
    
    # Split main text into condition and effect
    # Look for conditional patterns
    conditional_patterns = [
        r'([^。]+)がある場合、([^。]+)',
        r'([^。]+)とき、([^。]+)',
        r'([^。]+)場合、([^。]+)',
    ]
    
    for pattern in conditional_patterns:
        match = re.search(pattern, main_text)
        if match:
            components['condition'] = match.group(1)
            components['main_effect'] = match.group(2)
            return components
    
    # No condition found, treat entire text as main effect
    components['main_effect'] = main_text
    
    return components

# Analyze all abilities
ability_structures = []
for ability in abilities:
    for source in ability['source_ability_texts']:
        jp_text = source['jp']
        trigger_id = ability['trigger_id']
        trigger_name = TRIGGER_MAP.get(trigger_id, f"UNKNOWN_{trigger_id}")
        
        components = split_into_components(jp_text)
        components['trigger_id'] = trigger_id
        components['trigger_name'] = trigger_name
        components['original_text'] = jp_text
        
        ability_structures.append(components)

# Count structure types
structure_counts = Counter()
for struct in ability_structures:
    has_condition = struct['condition'] is not None
    has_options = len(struct['options']) > 0
    structure_key = f"trigger_{struct['trigger_name']}_condition_{has_condition}_options_{has_options}"
    structure_counts[structure_key] += 1

print("Ability-Level Structure Analysis")
print("="*80)
print(f"Total abilities analyzed: {len(ability_structures)}")
print()

print("Structure type distribution:")
print("-"*80)
for struct_type, count in sorted(structure_counts.items(), key=lambda x: -x[1]):
    print(f"  {struct_type:50s}: {count:3d} abilities")
print()

# Show examples of each structure type
print("Sample abilities by structure type:")
print("-"*80)
for struct_type in sorted(structure_counts.keys()):
    print(f"\n{struct_type}:")
    for struct in ability_structures[:3]:
        current_key = f"trigger_{struct['trigger_name']}_condition_{struct['condition'] is not None}_options_{len(struct['options']) > 0}"
        if current_key == struct_type:
            print(f"  Trigger: {struct['trigger_name']}")
            print(f"  Condition: {struct['condition']}")
            print(f"  Effect: {struct['main_effect']}")
            print(f"  Options: {struct['options']}")
            print(f"  Original: {struct['original_text']}")
            break
