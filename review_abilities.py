#!/usr/bin/env python3
"""Systematic ability frame review script."""

import json
import sys

def load_abilities():
    with open('data/ability_frame_source.json', encoding='utf-8') as f:
        return json.load(f)

def analyze_ability(ability, index):
    """Analyze an ability and return issues found."""
    issues = []
    text = ability.get('primary_text_jp', '')
    frames = ability.get('frames', [])
    trigger = ability.get('trigger', '')
    
    # Check for empty frames
    if not frames:
        issues.append(f"[{index}] EMPTY FRAMES - {text[:50]}...")
        return issues
    
    # Check frame structure
    for i, frame in enumerate(frames):
        if 'op' not in frame:
            issues.append(f"[{index}] Frame {i} missing 'op' field")
        if 'frame_index' not in frame:
            issues.append(f"[{index}] Frame {i} missing 'frame_index' field")
    
    # Check for specific patterns that need attention
    if 'SELECT_MODE' in [f.get('op') for f in frames]:
        # Check if option_names is present
        has_option_names = any('option_names' in f for f in frames)
        if not has_option_names:
            issues.append(f"[{index}] SELECT_MODE missing option_names - {text[:50]}...")
    
    # Check for flavor choice patterns (contain する or 行う)
    if 'する' in text or '行う' in text:
        has_select_mode = any(f.get('op') == 'SELECT_MODE' for f in frames)
        if has_select_mode and not any('option_names' in f for f in frames):
            issues.append(f"[{index}] Flavor choice missing option_names - {text[:50]}...")
    
    return issues

def main():
    data = load_abilities()
    abilities = data['abilities']
    
    print(f"Total abilities: {len(abilities)}")
    print("="*60)
    
    all_issues = []
    
    for i, ability in enumerate(abilities):
        issues = analyze_ability(ability, i)
        all_issues.extend(issues)
        
        # Print progress every 100 abilities
        if (i + 1) % 100 == 0:
            print(f"Reviewed {i + 1}/{len(abilities)} abilities...")
    
    print("="*60)
    print(f"Found {len(all_issues)} issues:")
    for issue in all_issues[:50]:  # Show first 50
        print(issue)
    
    if len(all_issues) > 50:
        print(f"... and {len(all_issues) - 50} more issues")

if __name__ == '__main__':
    main()
