#!/usr/bin/env python3
"""
Comprehensive analysis of all abilities in ability_frame_source.json
Identifies frame/text mismatches and common issues.
"""

import json
import re
from pathlib import Path

def load_abilities():
    path = Path("C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/data/ability_frame_source.json")
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    return data.get('abilities', [])

def extract_keywords(text):
    """Extract key condition keywords from Japanese ability text."""
    keywords = {
        'center_area': bool(re.search(r'センター|center', text, re.I)),
        'left_area': bool(re.search(r'左|left', text, re.I)),
        'right_area': bool(re.search(r'右|right', text, re.I)),
        'stage': bool(re.search(r'ステージ|stage', text, re.I)),
        'member': bool(re.search(r'メンバー|member', text, re.I)),
        'liella': bool(re.search(r'Liella|リエラ', text, re.I)),
        'muse': bool(re.search(r'μ.s|ミューズ', text, re.I)),
        'aquors': bool(re.search(r'Aqours|アクア', text, re.I)),
        'niji': bool(re.search(r'虹ヶ咲|にじがさき|ニジガク', text, re.I)),
        'hasuno': bool(re.search(r'蓮ノ空|hasuno', text, re.I)),
        'moved_this_turn': bool(re.search(r'このターン.*移動|移動.*このターン', text)),
        'optional': bool(re.search(r'もよい|may|optional', text, re.I)),
        'or_cost': bool(re.search(r'するか|か.*を|または', text)),
        'and_cost': bool(re.search(r'し、|をし', text)),
        'pay_energy': bool(re.search(r'エネルギー.*支払|E.*支払|支払ってもよい', text)),
        'tap_self': bool(re.search(r'このメンバーをウェイト|このカードをウェイト', text)),
        'discard_hand': bool(re.search(r'手札.*控え室|手札.*置く', text)),
        'draw': bool(re.search(r'カード.*引く|ドロー', text)),
        'activate': bool(re.search(r'アクティブ|activate', text, re.I)),
        'search': bool(re.search(r'サーチ|search|デッキ.*見る', text, re.I)),
        'only_condition': bool(re.search(r'のみ|only', text)),
        'count_hearts': bool(re.search(r'ハート|heart', text, re.I)),
        'count_blades': bool(re.search(r'ブレード|blade', text, re.I)),
        'formation_change': bool(re.search(r'フォーメーション|formation', text, re.I)),
        'transform': bool(re.search(r'変身|transform|ための', text)),
        'recover': bool(re.search(r'回復|recover', text)),
        'once_per_turn': bool(re.search(r'ターン1回|once per turn|ターンに1回', text)),
        'live_start': bool(re.search(r'ライブ開始時|live start', text, re.I)),
        'live_success': bool(re.search(r'ライブ成功時|live success', text, re.I)),
        'live_failure': bool(re.search(r'ライブ失敗時|live failure', text, re.I)),
        'on_play': bool(re.search(r'登場時|on play|登場した', text, re.I)),
        'auto': bool(re.search(r'自動|auto', text)),
        'startup': bool(re.search(r'起動|startup', text)),
        'continuous': bool(re.search(r'常時|continuous', text)),
        'center_trait': bool(re.search(r'センター', text)),
    }
    return keywords

def analyze_frame_issues(ability):
    """Analyze frames for issues based on text."""
    issues = []
    frames = ability.get('frames', [])
    text = ability.get('primary_text_jp', '')
    keywords = extract_keywords(text)
    card_refs = ability.get('card_refs', [])
    
    if not frames:
        return ['No frames defined']
    
    # Check for common issues
    
    # 1. SELECT_MEMBER used when text specifies specific area/position
    if any(f.get('op') == 'SELECT_MEMBER' for f in frames):
        if keywords['center_area'] and not any(f.get('slot', {}).get('area_idx') == 2 for f in frames if f.get('op') == 'SELECT_MEMBER'):
            # Has SELECT_MEMBER but text mentions center area specifically
            if 'センターエリア' in text and '自分のステージのセンター' in text:
                issues.append("SELECT_MEMBER used but text specifies center area - should use COUNT_STAGE with STAGE_2")
        
        # Check if text mentions specific member (this member, that member, etc.)
        if 'このメンバー' in text and not any(f.get('attr', {}).get('special_id') == 'Self' for f in frames):
            pass  # May be okay if it's for targeting other members
    
    # 2. Missing target_player: SELF when checking own stage
    if keywords['stage'] and '自分の' in text:
        for f in frames:
            if f.get('op') in ['COUNT_STAGE', 'SELECT_MEMBER', 'GROUP_FILTER']:
                if not f.get('attr', {}).get('target_player') and not f.get('slot', {}).get('target_player'):
                    if f.get('slot', {}).get('target_slot', '').startswith('STAGE'):
                        issues.append(f"Frame {f.get('frame_index')}: Missing target_player: SELF for own stage check")
    
    # 3. OR cost not properly handled
    if keywords['or_cost'] and ('するか' in text or 'か、' in text):
        has_select_mode = any(f.get('op') == 'SELECT_MODE' for f in frames)
        if not has_select_mode:
            # Check if it's a simple OR that should have SELECT_MODE
            if ('するか、' in text or 'するか：' in text or '置く：' in text):
                issues.append("Text has OR cost (するか) but no SELECT_MODE frame - may need branching logic")
    
    # 4. Missing jump after optional cost
    for i, f in enumerate(frames):
        if f.get('attr', {}).get('is_optional') and f.get('op') in ['PAY_ENERGY', 'MOVE_TO_DISCARD', 'SET_TAPPED']:
            # Next frame should be JUMP_IF_FALSE
            if i + 1 < len(frames) and frames[i + 1].get('op') != 'JUMP_IF_FALSE':
                issues.append(f"Frame {f.get('frame_index')}: Optional {f.get('op')} not followed by JUMP_IF_FALSE")
    
    # 5. Missing condition for "only" check (のみ)
    if keywords['only_condition']:
        # Should have COUNT_STAGE comparison logic
        has_sum_value = any(f.get('op') == 'SUM_VALUE' for f in frames)
        if not has_sum_value and ('のみ' in text and '自分のステージ' in text):
            issues.append("Text has 'only' condition (のみ) but no SUM_VALUE for comparison - may not check properly")
    
    # 6. "Moved this turn" condition
    if keywords['moved_this_turn']:
        has_moved_check = any(f.get('attr', {}).get('check_moved_this_turn') for f in frames)
        if not has_moved_check:
            issues.append("Text mentions 'moved this turn' but no check_moved_this_turn flag in frames")
    
    # 7. Formation change
    if keywords['formation_change']:
        has_formation_change = any(f.get('op') == 'FORMATION_CHANGE' for f in frames)
        if has_formation_change:
            fc_frame = [f for f in frames if f.get('op') == 'FORMATION_CHANGE'][0]
            if not fc_frame.get('attr', {}).get('is_optional') and 'してもよい' in text:
                issues.append("FORMATION_CHANGE should have is_optional: 1 for optional formation change")
    
    # 8. Missing once-per-turn check
    if keywords['once_per_turn']:
        # This is usually handled at trigger level, but verify
        if ability.get('trigger') == 'ACTIVATED' and not any(f.get('op') == 'CHECK_ONCE_PER_TURN' for f in frames):
            pass  # May be okay if engine handles it
    
    # 9. Group filter without proper targeting
    for f in frames:
        if f.get('op') == 'GROUP_FILTER':
            if not f.get('attr', {}).get('target_player') and '自分の' in text:
                issues.append(f"Frame {f.get('frame_index')}: GROUP_FILTER missing target_player: SELF")
    
    # 10. Check for wrong slot targets
    for f in frames:
        if f.get('op') in ['BOOST_SCORE', 'ADD_BLADES', 'ADD_HEART']:
            slot = f.get('slot', {}).get('target_slot', '')
            f_idx = f.get('frame_index', 0)
            if slot == 'CONTEXT':
                prev_frames = [p for p in frames if p.get('frame_index', 0) < f_idx]
                has_select = any(p.get('op') == 'SELECT_MEMBER' for p in prev_frames)
                if not has_select and '自分の' in text:
                    issues.append(f"Frame {f_idx}: Uses CONTEXT but no prior SELECT_MEMBER - may need explicit target")
    
    # 11. Check for inconsistencies in OR choices
    select_modes = [f for f in frames if f.get('op') == 'SELECT_MODE']
    for sm in select_modes:
        value = sm.get('value', 0)
        idx = frames.index(sm)
        # After SELECT_MODE should be value number of JUMP frames
        jump_count = 0
        for f in frames[idx+1:idx+1+value]:
            if f.get('op') == 'JUMP':
                jump_count += 1
        if jump_count != value:
            issues.append(f"SELECT_MODE value={value} but only {jump_count} JUMP frames follow (should be {value})")
    
    # 12. Check for GROUP_FILTER with wrong value
    for f in frames:
        if f.get('op') == 'GROUP_FILTER':
            value = f.get('value', 0)
            # If text says "only" but value is 4, that's wrong
            if 'のみ' in text and value == 4:
                issues.append(f"Frame {f.get('frame_index')}: GROUP_FILTER value=4 but text says 'only' - should check ALL members are in group")
    
    return issues

def main():
    abilities = load_abilities()
    
    all_issues = []
    fixed_count = 0
    
    for i, ability in enumerate(abilities):
        text = ability.get('primary_text_jp', '')
        card_refs = ability.get('card_refs', [])
        
        if not card_refs:
            continue
            
        card_no = card_refs[0].get('card_no', 'Unknown')
        ab_index = card_refs[0].get('ability_index', 0)
        
        issues = analyze_frame_issues(ability)
        
        if issues:
            all_issues.append({
                'index': i,
                'card_no': card_no,
                'ability_index': ab_index,
                'text': text[:100] + '...' if len(text) > 100 else text,
                'frames': [f.get('op') for f in ability.get('frames', [])],
                'issues': issues
            })
    
    # Write analysis report
    report_path = Path("C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/docs/ability_analysis_report.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Ability Frame Analysis Report\n\n")
        f.write(f"Total abilities analyzed: {len(abilities)}\n")
        f.write(f"Abilities with issues: {len(all_issues)}\n\n")
        
        for item in all_issues:
            f.write(f"## {item['card_no']}#Ab{item['ability_index']}\n\n")
            f.write(f"**Text:** {item['text']}\n\n")
            f.write(f"**Frame Flow:** {' → '.join(item['frames'])}\n\n")
            f.write(f"**Issues:**\n")
            for issue in item['issues']:
                f.write(f"- {issue}\n")
            f.write("\n---\n\n")
    
    print(f"Analysis complete. Found {len(all_issues)} abilities with potential issues.")
    print(f"Report written to: {report_path}")
    
    return all_issues

if __name__ == '__main__':
    issues = main()
