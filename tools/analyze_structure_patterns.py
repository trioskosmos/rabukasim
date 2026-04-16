#!/usr/bin/env python3
"""
Analyze structural patterns in abilities (condition markers, modifiers, etc).
"""
import json
from collections import defaultdict

# Read the abilities file
with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Analyze modifiers
time_prefixes = []
duration_prefixes = []
use_limits = []
condition_markers = defaultdict(int)

for ability in data['unique_abilities']:
    text = ability['costless_text']
    
    # Check for time prefixes
    if text.startswith('このターン、'):
        time_prefixes.append(text)
    
    # Check for duration prefixes
    if text.startswith('ライブ終了時まで、'):
        duration_prefixes.append(text)
    
    # Check for use limits
    if '［ターン' in text:
        use_limits.append(text)
    
    # Count condition markers
    if '場合' in text:
        condition_markers['場合'] += 1
    if 'とき' in text:
        condition_markers['とき'] += 1
    if 'かぎり' in text:
        condition_markers['かぎり'] += 1
    if 'なら' in text:
        condition_markers['なら'] += 1

# Analyze 1P_1C patterns specifically
one_p_one_c = []
for ability in data['unique_abilities']:
    text = ability['costless_text']
    if text.count('。') == 1 and text.count('、') == 1:
        one_p_one_c.append(text)

# Analyze 1P_2C patterns specifically
one_p_two_c = []
for ability in data['unique_abilities']:
    text = ability['costless_text']
    if text.count('。') == 1 and text.count('、') == 2:
        one_p_two_c.append(text)

# Write analysis
with open('data/structure_pattern_analysis.txt', 'w', encoding='utf-8') as f:
    f.write("=" * 80 + "\n")
    f.write("STRUCTURAL PATTERN ANALYSIS\n")
    f.write("=" * 80 + "\n\n")
    
    f.write("MODIFIER FREQUENCY\n")
    f.write("-" * 80 + "\n")
    f.write(f"Time prefixes (このターン、): {len(time_prefixes)}\n")
    f.write(f"Duration prefixes (ライブ終了時まで、): {len(duration_prefixes)}\n")
    f.write(f"Use limits (［ターン...回］): {len(use_limits)}\n\n")
    
    f.write("CONDITION MARKER FREQUENCY\n")
    f.write("-" * 80 + "\n")
    for marker, count in sorted(condition_markers.items(), key=lambda x: x[1], reverse=True):
        f.write(f"{marker}: {count}\n")
    
    f.write("\n" + "=" * 80 + "\n")
    f.write("1P_1C PATTERN ANALYSIS (163 abilities)\n")
    f.write("=" * 80 + "\n\n")
    
    # Categorize 1P_1C by structure
    simple_actions = []
    duration_actions = []
    condition_actions = []
    other = []
    
    for text in one_p_one_c:
        parts = text.split('、')
        if len(parts) == 2:
            if parts[0].startswith('ライブ終了時まで、'):
                duration_actions.append(text)
            elif '場合' in parts[0] or 'とき' in parts[0] or 'かぎり' in parts[0]:
                condition_actions.append(text)
            else:
                simple_actions.append(text)
        else:
            other.append(text)
    
    f.write(f"Duration + action: {len(duration_actions)}\n")
    f.write(f"Condition + action: {len(condition_actions)}\n")
    f.write(f"Action + action: {len(simple_actions)}\n")
    f.write(f"Other: {len(other)}\n\n")
    
    f.write("SAMPLES - Duration + action:\n")
    for i, text in enumerate(duration_actions[:5], 1):
        f.write(f"  [{i}] {text}\n")
    
    f.write("\nSAMPLES - Condition + action:\n")
    for i, text in enumerate(condition_actions[:5], 1):
        f.write(f"  [{i}] {text}\n")
    
    f.write("\nSAMPLES - Action + action:\n")
    for i, text in enumerate(simple_actions[:5], 1):
        f.write(f"  [{i}] {text}\n")
    
    f.write("\n" + "=" * 80 + "\n")
    f.write("1P_2C PATTERN ANALYSIS (102 abilities)\n")
    f.write("=" * 80 + "\n\n")
    
    # Categorize 1P_2C by structure
    time_condition_action = []
    duration_per_unit_action = []
    two_conditions_action = []
    condition_duration_action = []
    other_two = []
    
    for text in one_p_two_c:
        parts = text.split('、')
        if text.startswith('このターン、'):
            time_condition_action.append(text)
        elif text.startswith('ライブ終了時まで、') and 'につき' in text:
            duration_per_unit_action.append(text)
        elif 'あり' in parts[0] and '場合' in parts[1]:
            two_conditions_action.append(text)
        elif '場合' in parts[0] and 'ライブ終了時まで' in parts[1]:
            condition_duration_action.append(text)
        else:
            other_two.append(text)
    
    f.write(f"Time + condition + action: {len(time_condition_action)}\n")
    f.write(f"Duration + per-unit + action: {len(duration_per_unit_action)}\n")
    f.write(f"Two conditions + action: {len(two_conditions_action)}\n")
    f.write(f"Condition + duration + action: {len(condition_duration_action)}\n")
    f.write(f"Other: {len(other_two)}\n\n")
    
    f.write("SAMPLES - Time + condition + action:\n")
    for i, text in enumerate(time_condition_action[:5], 1):
        f.write(f"  [{i}] {text}\n")
    
    f.write("\nSAMPLES - Duration + per-unit + action:\n")
    for i, text in enumerate(duration_per_unit_action[:5], 1):
        f.write(f"  [{i}] {text}\n")
    
    f.write("\nSAMPLES - Two conditions + action:\n")
    for i, text in enumerate(two_conditions_action[:5], 1):
        f.write(f"  [{i}] {text}\n")
    
    f.write("\nSAMPLES - Condition + duration + action:\n")
    for i, text in enumerate(condition_duration_action[:5], 1):
        f.write(f"  [{i}] {text}\n")
    
    f.write("\nSAMPLES - Other (unclassified):\n")
    for i, text in enumerate(other_two[:10], 1):
        f.write(f"  [{i}] {text}\n")

print("Analysis complete. See data/structure_pattern_analysis.txt")
