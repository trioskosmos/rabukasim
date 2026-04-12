#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Group abilities by text similarity to make manual inspection easier
Generate a rearranged ability_frame_source.json with similar abilities grouped together
"""
import json
from pathlib import Path
from collections import defaultdict
import re

def load_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_text_features(text):
    """Extract key features from ability text for similarity matching"""
    if not text:
        return {}
    
    features = {
        'length': len(text),
        'lines': len([l for l in text.split('\n') if l.strip()]),
        'has_optional': 'してもよい' in text or 'してもいい' in text,
        'has_choice': '以下から1つを選ぶ' in text or '選んで' in text,
        'has_discard': '控え室' in text or '捨てる' in text,
        'has_draw': '引く' in text or 'ドロー' in text,
        'has_energy': 'エネルギー' in text or 'E' in text,
        'has_live': 'ライブ' in text,
        'has_stage': 'ステージ' in text,
        'has_hand': '手札' in text,
        'has_deck': 'デッキ' in text,
    }
    
    # Extract numbers
    numbers = re.findall(r'\d+', text)
    features['numbers'] = numbers
    features['number_count'] = len(numbers)
    
    return features

def calculate_similarity(features1, features2):
    """Calculate similarity score between two ability text features"""
    score = 0
    
    # Similar length
    length_diff = abs(features1['length'] - features2['length'])
    if length_diff < 50:
        score += 10
    elif length_diff < 100:
        score += 5
    
    # Similar line count
    line_diff = abs(features1['lines'] - features2['lines'])
    if line_diff == 0:
        score += 5
    elif line_diff == 1:
        score += 3
    
    # Similar features
    for key in ['has_optional', 'has_choice', 'has_discard', 'has_draw', 'has_energy', 'has_live', 'has_stage', 'has_hand', 'has_deck']:
        if features1.get(key) == features2.get(key):
            score += 2
    
    # Similar number count
    num_diff = abs(features1['number_count'] - features2['number_count'])
    if num_diff == 0:
        score += 3
    elif num_diff == 1:
        score += 1
    
    return score

def group_abilities(abilities):
    """Group abilities by similarity"""
    # Extract features for all abilities
    ability_features = []
    for ability in abilities:
        primary_text = ability.get('primary_text_jp', '')
        card_refs = ability.get('card_refs', [])
        card_no = card_refs[0].get('card_no', 'unknown') if card_refs else 'unknown'
        trigger = ability.get('trigger_id', 0)
        
        features = extract_text_features(primary_text)
        features['card_no'] = card_no
        features['trigger'] = trigger
        features['ability'] = ability
        
        ability_features.append(features)
    
    # Group by trigger first (major grouping)
    trigger_groups = defaultdict(list)
    for features in ability_features:
        trigger_groups[features['trigger']].append(features)
    
    # Within each trigger group, group by similarity
    grouped_abilities = []
    
    for trigger, trigger_abilities in trigger_groups.items():
        # Sort by card_no for consistent ordering
        trigger_abilities.sort(key=lambda x: x['card_no'])
        
        # Simple clustering: group consecutive similar abilities
        if len(trigger_abilities) <= 1:
            grouped_abilities.extend([f['ability'] for f in trigger_abilities])
            continue
        
        clusters = []
        current_cluster = [trigger_abilities[0]]
        
        for i in range(1, len(trigger_abilities)):
            similarity = calculate_similarity(trigger_abilities[i-1], trigger_abilities[i])
            
            if similarity >= 5:  # Similarity threshold
                current_cluster.append(trigger_abilities[i])
            else:
                clusters.append(current_cluster)
                current_cluster = [trigger_abilities[i]]
        
        clusters.append(current_cluster)
        
        # Add clusters to grouped abilities
        for cluster in clusters:
            # Sort cluster by similarity within itself
            if len(cluster) > 1:
                cluster.sort(key=lambda x: x['length'])
            grouped_abilities.extend([f['ability'] for f in cluster])
    
    return grouped_abilities

def main():
    base_path = Path('C:/Users/trios/.gemini/antigravity/vscode/loveca-copy')
    input_file = base_path / 'data' / 'ability_frame_source.json'
    output_file = base_path / 'data' / 'ability_frame_source_grouped.json'
    
    print("Loading ability_frame_source.json...")
    data = load_json(input_file)
    abilities = data.get('abilities', [])
    
    print(f"Total abilities: {len(abilities)}")
    
    print("Grouping abilities by similarity...")
    grouped_abilities = group_abilities(abilities)
    
    print(f"Grouped abilities: {len(grouped_abilities)}")
    
    # Create new data structure with grouped abilities
    grouped_data = {
        'schema': data.get('schema', 'ability_frame_source.v1'),
        'abilities': grouped_abilities,
        '_grouping_info': {
            'method': 'text_similarity',
            'grouped_by': ['trigger', 'text_features', 'length'],
            'total_groups': len(abilities)  # Each ability is now in similarity order
        }
    }
    
    # Save to new file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(grouped_data, f, indent=2, ensure_ascii=False)
    
    print(f"Saved grouped abilities to {output_file}")
    
    # Show some examples of groupings
    print("\nSample of grouped abilities (first 10):")
    for i, ability in enumerate(grouped_abilities[:10]):
        card_refs = ability.get('card_refs', [])
        card_no = card_refs[0].get('card_no', 'unknown') if card_refs else 'unknown'
        trigger = ability.get('trigger_id', 0)
        text = ability.get('primary_text_jp', '')[:50]
        print(f"  {i+1}. {card_no} (trigger {trigger}): {text}")

if __name__ == '__main__':
    main()
