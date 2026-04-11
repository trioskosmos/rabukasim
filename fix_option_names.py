#!/usr/bin/env python3
"""Fix missing option_names for SELECT_MODE abilities."""

import json
import re

def load_abilities():
    with open('data/ability_frame_source.json', encoding='utf-8') as f:
        return json.load(f)

def save_abilities(data):
    with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def extract_choices(text):
    """Extract choice options from Japanese ability text."""
    choices = []
    
    # Pattern: "Xする。/ Yする。" or "Xしてもよい。/ Yしてもよい。"
    # Pattern: "Xする：/ Yする："
    
    # Look for common patterns
    patterns = [
        r'([^
。]+(?:する|してもよい|行う)[^
。]*)[。\n]\s*/\s*([^
。]+(?:する|してもよい|行う)[^
。]*)',
        r'([^
：]+)：\s*/\s*([^
：]+)：',
        r'もしくは',
        r'または',
    ]
    
    # Simple extraction based on common phrases
    if 'カードを1枚引く' in text and 'ライブにセットする' in text:
        choices = ['カードを1枚引く', 'ライブにセットする']
    elif '控え室に置く' in text and '手札に加える' in text:
        choices = ['控え室に置く', '手札に加える']
    elif '登場させる' in text and 'アクティブにする' in text:
        choices = ['登場させる', 'アクティブにする']
    elif 'アクティブにする' in text and 'ウェイトにする' in text:
        choices = ['アクティブにする', 'ウェイトにする']
    elif '引く' in text and ('スコアを' in text or 'ブレード' in text):
        # Extract specific actions
        if 'カードを' in text and ('引く' in text or '引き' in text):
            draw_match = re.search(r'カードを(\d+)枚引', text)
            if draw_match:
                choices.append(f'カードを{draw_match.group(1)}枚引く')
        if 'スコア' in text:
            choices.append('スコア+1')
        if 'ブレード' in text:
            blade_count = text.count('ブレード')
            if blade_count > 0:
                choices.append(f'ブレード×{blade_count}')
    
    # Default if no specific pattern matched
    if not choices:
        # Try to find choice indicators
        if 'する：' in text or 'してもよい' in text or '行う' in text:
            # Split on common dividers
            parts = re.split(r'(?:もしくは|または|/|、)', text)
            if len(parts) >= 2:
                choices = [p.strip()[:30] for p in parts[:2]]
    
    if not choices:
        choices = ['選択肢1', '選択肢2']  # Default fallback
    
    return choices[:2]  # Return max 2 choices

def fix_option_names():
    data = load_abilities()
    abilities = data['abilities']
    
    fixed_count = 0
    
    for i, ability in enumerate(abilities):
        frames = ability.get('frames', [])
        text = ability.get('primary_text_jp', '')
        
        # Find SELECT_MODE frames missing option_names
        for frame in frames:
            if frame.get('op') == 'SELECT_MODE' and 'option_names' not in frame:
                choices = extract_choices(text)
                frame['option_names'] = choices
                fixed_count += 1
                card = ability.get('card_refs', [{}])[0].get('card_no', 'Unknown')
                print(f"Fixed [{i}] {card}: {choices}")
    
    if fixed_count > 0:
        save_abilities(data)
        print(f"\n✓ Fixed {fixed_count} abilities with missing option_names")
    else:
        print("\nNo fixes needed - all SELECT_MODE abilities have option_names")
    
    return fixed_count

if __name__ == '__main__':
    fix_option_names()
