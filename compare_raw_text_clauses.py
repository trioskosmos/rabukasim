#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compare raw Japanese text clauses to detect incomplete abilities
Split text into clauses and compare clause sets between similar abilities
"""
import json
from pathlib import Path
from collections import defaultdict
import re

def load_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def split_into_clauses(text):
    """Split Japanese ability text into clauses"""
    if not text:
        return []
    
    # Split by common Japanese punctuation
    clauses = re.split(r'[。：、\n]', text)
    
    # Clean up clauses
    clauses = [c.strip() for c in clauses if c.strip()]
    
    return clauses

def normalize_clause(clause):
    """Normalize a clause for comparison"""
    if not clause:
        return ""
    
    # Remove image tags like {{toujyou.png|登場}}
    clause = re.sub(r'\{\{[^}]+\}\}', '', clause)
    
    # Remove whitespace
    clause = clause.replace(' ', '').replace('　', '')
    
    return clause

def extract_clause_features(clause):
    """Extract features from a clause"""
    normalized = normalize_clause(clause)
    
    features = {
        'original': clause,
        'normalized': normalized,
        'length': len(normalized),
        'has_optional': 'してもよい' in clause or 'してもいい' in clause,
        'has_number': bool(re.search(r'\d+', clause)),
        'number': re.search(r'\d+', clause).group() if re.search(r'\d+', clause) else None,
        'keywords': [],
    }
    
    # Extract keywords
    keywords = ['控え室', '手札', 'デッキ', 'ステージ', 'エネルギー', 'ライブ', '引く', '置く', '加える', '選ぶ']
    for kw in keywords:
        if kw in clause:
            features['keywords'].append(kw)
    
    return features

def calculate_clause_similarity(clauses1, clauses2):
    """Calculate similarity between two sets of clauses"""
    features1 = [extract_clause_features(c) for c in clauses1]
    features2 = [extract_clause_features(c) for c in clauses2]
    
    # Check if one is subset of another
    norms1 = set(f['normalized'] for f in features1)
    norms2 = set(f['normalized'] for f in features2)
    
    is_subset = norms1.issubset(norms2) or norms2.issubset(norms1)
    
    # Calculate overlap
    overlap = len(norms1 & norms2)
    total_unique = len(norms1 | norms2)
    similarity_ratio = overlap / total_unique if total_unique > 0 else 0
    
    return {
        'is_subset': is_subset,
        'overlap_ratio': similarity_ratio,
        'missing_from_1': list(norms2 - norms1) if not norms1.issubset(norms2) else [],
        'missing_from_2': list(norms1 - norms2) if not norms2.issubset(norms1) else [],
    }

def group_by_clause_similarity(abilities):
    """Group abilities by clause similarity"""
    # Extract clauses for all abilities
    ability_clauses = []
    for ability in abilities:
        primary_text = ability.get('primary_text_jp', '')
        card_refs = ability.get('card_refs', [])
        card_no = card_refs[0].get('card_no', 'unknown') if card_refs else 'unknown'
        trigger = ability.get('trigger_id', 0)
        
        clauses = split_into_clauses(primary_text)
        clause_features = [extract_clause_features(c) for c in clauses]
        
        # Create a signature based on clause keywords and structure
        signature_parts = []
        for cf in clause_features:
            sig = f"{cf['length']}_{','.join(sorted(cf['keywords']))}"
            signature_parts.append(sig)
        
        signature = '|'.join(sorted(signature_parts))
        
        ability_clauses.append({
            'ability': ability,
            'card_no': card_no,
            'trigger': trigger,
            'clauses': clauses,
            'clause_features': clause_features,
            'signature': signature,
            'clause_count': len(clauses),
        })
    
    # Group by signature
    signature_groups = defaultdict(list)
    for ac in ability_clauses:
        signature_groups[ac['signature']].append(ac)
    
    # Within each signature group, find subset relationships
    incomplete_abilities = []
    
    for signature, group in signature_groups.items():
        if len(group) < 2:
            continue
        
        # Compare all pairs in the group
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                ac1 = group[i]
                ac2 = group[j]
                
                similarity = calculate_clause_similarity(ac1['clauses'], ac2['clauses'])
                
                if similarity['is_subset'] and similarity['overlap_ratio'] < 1.0:
                    # One is a subset of the other - likely incomplete
                    if len(similarity['missing_from_1']) > 0:
                        incomplete_abilities.append({
                            'card_no': ac1['card_no'],
                            'missing_clauses': similarity['missing_from_1'],
                            'similar_to': ac2['card_no'],
                            'trigger': ac1['trigger'],
                            'reason': 'subset_missing_clauses'
                        })
                    if len(similarity['missing_from_2']) > 0:
                        incomplete_abilities.append({
                            'card_no': ac2['card_no'],
                            'missing_clauses': similarity['missing_from_2'],
                            'similar_to': ac1['card_no'],
                            'trigger': ac2['trigger'],
                            'reason': 'subset_missing_clauses'
                        })
    
    return incomplete_abilities

def main():
    base_path = Path('C:/Users/trios/.gemini/antigravity/vscode/loveca-copy')
    input_file = base_path / 'data' / 'ability_frame_source.json'
    
    print("Loading ability_frame_source.json...")
    data = load_json(input_file)
    abilities = data.get('abilities', [])
    
    print(f"Total abilities: {len(abilities)}")
    
    print("Analyzing clause similarity...")
    incomplete = group_by_clause_similarity(abilities)
    
    print(f"\nFound {len(incomplete)} potentially incomplete abilities (missing clauses)")
    
    # Show examples
    print("\nExamples of abilities with missing clauses:")
    for i, inc in enumerate(incomplete[:10]):
        print(f"  {i+1}. {inc['card_no']} (trigger {inc['trigger']})")
        print(f"     Missing: {inc['missing_clauses']}")
        print(f"     Similar to: {inc['similar_to']}")
    
    # Save results
    output_file = base_path / 'clause_comparison_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'total_abilities': len(abilities),
            'incomplete_count': len(incomplete),
            'incomplete_abilities': incomplete
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\nSaved results to {output_file}")

if __name__ == '__main__':
    main()
