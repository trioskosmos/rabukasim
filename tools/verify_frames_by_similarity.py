#!/usr/bin/env python3
"""
Verify unverified abilities by comparing with similar verified abilities.
Uses text similarity and trigger matching to suggest frame patterns.
"""

import json
import re
import sys
from pathlib import Path
from difflib import SequenceMatcher
from collections import defaultdict

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def normalize_text(text):
    """Normalize Japanese text for comparison."""
    # Remove template tags
    text = re.sub(r'\{\{[^}]+\}\}', '', text)
    # Remove common variations
    text = text.replace(' ', '').replace('\n', '')
    return text

def text_similarity(a, b):
    """Calculate similarity between two texts."""
    return SequenceMatcher(None, normalize_text(a), normalize_text(b)).ratio()

def extract_key_patterns(text):
    """Extract key patterns from ability text."""
    patterns = []
    # Draw patterns
    if 'カードを' in text and '枚引' in text:
        patterns.append('DRAW')
    # Discard patterns
    if '控え室に置く' in text:
        patterns.append('DISCARD')
    # Look at deck
    if '見る' in text and 'デッキ' in text:
        patterns.append('LOOK')
    # Add to hand
    if '手札に加える' in text:
        patterns.append('ADD_TO_HAND')
    # Energy payment
    if '支払う' in text and 'エネルギー' in text:
        patterns.append('PAY_ENERGY')
    # Play member
    if 'ステージに登場' in text or 'ステージに置く' in text:
        patterns.append('PLAY_MEMBER')
    # Heart gain
    if 'ハートを得る' in text or re.search(r'heart_\d+を得る', text):
        patterns.append('ADD_HEARTS')
    # Blade gain
    if 'ブレードを得る' in text or 'blade' in text.lower():
        patterns.append('ADD_BLADES')
    # Tap
    if 'ウェイトにする' in text or 'タップ' in text:
        patterns.append('TAP')
    # Conditional
    if '場合' in text or 'とき' in text:
        patterns.append('CONDITIONAL')
    # Optional
    if 'てもよい' in text:
        patterns.append('OPTIONAL')
    return patterns

def find_similar_verified(target_ability, verified_abilities):
    """Find similar verified abilities."""
    target_text = target_ability.get('primary_text_jp', '')
    target_trigger = target_ability.get('trigger_id', 0)
    target_patterns = extract_key_patterns(target_text)
    
    similar = []
    for va in verified_abilities:
        # Must have same trigger
        if va.get('trigger_id', 0) != target_trigger:
            continue
            
        va_text = va.get('primary_text_jp', '')
        va_patterns = extract_key_patterns(va_text)
        
        # Calculate similarity
        sim = text_similarity(target_text, va_text)
        pattern_match = len(set(target_patterns) & set(va_patterns))
        
        if sim > 0.3 or pattern_match >= 2:
            similar.append({
                'ability': va,
                'similarity': sim,
                'pattern_match': pattern_match,
                'patterns': va_patterns
            })
    
    # Sort by similarity then pattern match
    similar.sort(key=lambda x: (x['similarity'], x['pattern_match']), reverse=True)
    return similar[:5]

def suggest_frames(target_ability, similar_abilities):
    """Suggest frames based on similar abilities."""
    suggestions = []
    
    for sim in similar_abilities:
        va = sim['ability']
        frames = va.get('frames', [])
        verification = va.get('frame_verification', {})
        
        suggestions.append({
            'similar_text': va.get('primary_text_jp', '')[:80],
            'similarity': sim['similarity'],
            'pattern_match': sim['pattern_match'],
            'frames': frames,
            'verification_notes': verification.get('notes', []),
            'card_count': len(va.get('card_refs', []))
        })
    
    return suggestions

def analyze_unverified(source_file):
    """Analyze unverified abilities and suggest completions."""
    
    with open(source_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    abilities = data.get('abilities', [])
    
    # Separate verified and unverified
    verified = [a for a in abilities if a.get('frame_verification', {}).get('verified', False)]
    unverified = [a for a in abilities if not a.get('frame_verification', {}).get('verified', False)]
    
    print(f"Found {len(unverified)} unverified abilities")
    print(f"Found {len(verified)} verified abilities to compare against\n")
    
    # Analyze each unverified ability
    results = []
    for i, target in enumerate(unverified):
        target_text = target.get('primary_text_jp', '')
        target_frames = target.get('frames', [])
        target_issues = target.get('frame_verification', {}).get('issues', [])
        
        print(f"--- Unverified #{i+1} ---")
        print(f"Text: {target_text[:100]}...")
        print(f"Current frames: {len(target_frames)}")
        print(f"Current issues: {target_issues}")
        
        # Find similar verified abilities
        similar = find_similar_verified(target, verified)
        
        if similar:
            print(f"\nSimilar verified abilities found:")
            for j, sim in enumerate(similar):
                va = sim['ability']
                print(f"\n  {j+1}. Similarity: {sim['similarity']:.2f}, Pattern match: {sim['pattern_match']}")
                print(f"     Text: {va.get('primary_text_jp', '')[:80]}...")
                print(f"     Frames: {len(va.get('frames', []))}")
                print(f"     Cards: {len(va.get('card_refs', []))}")
                print(f"     Patterns: {sim['patterns']}")
                
                # Show frame structure
                frames = va.get('frames', [])
                print(f"     Frame ops: {[f.get('op') for f in frames]}")
        else:
            print("\nNo similar verified abilities found")
        
        print("\n" + "="*60)
        
        results.append({
            'target': target,
            'similar': similar
        })
    
    return results

if __name__ == "__main__":
    import sys
    source_file = Path(__file__).parent.parent / "data" / "ability_frame_source.json"
    
    # Check if output file argument provided
    if len(sys.argv) > 1:
        output_file = Path(sys.argv[1])
        # Redirect stdout to file
        original_stdout = sys.stdout
        with open(output_file, 'w', encoding='utf-8') as f:
            sys.stdout = f
            analyze_unverified(source_file)
            sys.stdout = original_stdout
        print(f"Results written to {output_file}")
    else:
        analyze_unverified(source_file)
