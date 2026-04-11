#!/usr/bin/env python3
"""
Deep scan of all abilities looking for:
1. Missing frames (conditions not checked)
2. Wrong opcodes (should be different operation)
3. Enhancement needed (wrong zone/color/area)
"""

import json
import re
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path("C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/data")
DOCS_DIR = Path("C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/docs")
JSON_PATH = DATA_DIR / "ability_frame_source.json"

def load_json():
    with open(JSON_PATH, encoding='utf-8') as f:
        return json.load(f)

def extract_card_ref(ability):
    refs = ability.get('card_refs', [])
    if refs:
        return f"{refs[0].get('card_no', 'Unknown')}#Ab{refs[0].get('ability_index', 0)}"
    return "Unknown"

def deep_scan_ability(ability):
    """Deep scan a single ability for all types of issues."""
    issues = {
        'missing_frames': [],
        'wrong_opcode': [],
        'needs_enhancement': [],
        'structural_issues': []
    }
    
    frames = ability.get('frames', [])
    text = ability.get('primary_text_jp', '')
    card_ref = extract_card_ref(ability)
    
    if not frames or not text:
        return issues
    
    # === 1. MISSING FRAMES ===
    
    # 1a. Missing once-per-turn check for startup abilities
    if 'ターン1回' in text and '起動' in text:
        has_turn_check = any(
            f.get('op') in ['CHECK_ONCE_PER_TURN', 'VERIFY_ONCE_PER_TURN'] or 
            f.get('attr', {}).get('once_per_turn') 
            for f in frames
        )
        if not has_turn_check:
            issues['missing_frames'].append({
                'frame_idx': 0,
                'issue': 'Missing once-per-turn check for ターン1回 startup ability',
                'recommendation': 'Add CHECK_ONCE_PER_TURN as first frame'
            })
    
    # 1b. Missing zone specification
    for i, f in enumerate(frames):
        if f.get('op') in ['COUNT_STAGE', 'SELECT_MEMBER', 'GROUP_FILTER']:
            slot = f.get('slot', {})
            if not slot.get('target_slot'):
                issues['missing_frames'].append({
                    'frame_idx': f.get('frame_index', i),
                    'issue': f"{f.get('op')} missing target_slot specification",
                    'recommendation': 'Add target_slot based on text (STAGE_0, STAGE_1, STAGE_2)'
                })
    
    # 1c. Missing jump after condition checks
    condition_ops = ['COUNT_STAGE', 'GROUP_FILTER', 'CHECK_HAS_MEMBER']
    for i, f in enumerate(frames):
        if f.get('op') in condition_ops:
            # Check if next frame is JUMP_IF_FALSE or this is the last frame before effect
            if i + 1 < len(frames):
                next_op = frames[i + 1].get('op')
                if next_op not in ['JUMP_IF_FALSE', 'JUMP']:
                    # This condition check isn't followed by proper flow control
                    issues['missing_frames'].append({
                        'frame_idx': f.get('frame_index', i),
                        'issue': f"{f.get('op')} not followed by JUMP_IF_FALSE",
                        'recommendation': 'Add JUMP_IF_FALSE to skip effect if condition fails'
                    })
    
    # 1d. Missing cost enforcement (optional cost without proper skip)
    cost_ops = ['PAY_ENERGY', 'MOVE_TO_DISCARD', 'SET_TAPPED']
    for i, f in enumerate(frames):
        if f.get('op') in cost_ops and f.get('attr', {}).get('is_optional'):
            if i + 1 < len(frames) and frames[i + 1].get('op') != 'JUMP_IF_FALSE':
                issues['missing_frames'].append({
                    'frame_idx': f.get('frame_index', i),
                    'issue': f"Optional {f.get('op')} missing JUMP_IF_FALSE after",
                    'recommendation': 'Add JUMP_IF_FALSE to skip effect if cost not paid'
                })
    
    # === 2. WRONG OPCODES ===
    
    # 2a. SELECT_MEMBER when should be COUNT_STAGE (automatic conditions)
    for i, f in enumerate(frames):
        if f.get('op') == 'SELECT_MEMBER':
            # Check if text indicates automatic selection
            if any(phrase in text for phrase in ['センターエリアにいる', '自分のステージのセンター']):
                if f.get('slot', {}).get('area_idx') == 2:
                    issues['wrong_opcode'].append({
                        'frame_idx': f.get('frame_index', i),
                        'issue': "SELECT_MEMBER used for automatic center area check",
                        'current': 'SELECT_MEMBER',
                        'recommendation': 'COUNT_STAGE with STAGE_2 target and JUMP_IF_FALSE'
                    })
    
    # 2b. GROUP_FILTER for "only" conditions
    for i, f in enumerate(frames):
        if f.get('op') == 'GROUP_FILTER':
            # Check if text has "only" condition
            if 'のみ' in text and '自分のステージ' in text:
                issues['wrong_opcode'].append({
                    'frame_idx': f.get('frame_index', i),
                    'issue': f"GROUP_FILTER used for 'only' condition (value={f.get('value')})",
                    'current': 'GROUP_FILTER',
                    'recommendation': 'Use COUNT_STAGE sequence: count group members, sum, count total, compare with SUM_VALUE EQ'
                })
    
    # 2c. BOOST_SCORE on wrong target
    for i, f in enumerate(frames):
        if f.get('op') == 'BOOST_SCORE':
            slot = f.get('slot', {}).get('target_slot', '')
            # If text says "this card" or "このカード" but target is CONTEXT
            if 'このカード' in text and slot == 'CONTEXT':
                # Check if there's a prior SELECT_MEMBER
                prev_ops = [frames[j].get('op') for j in range(i)]
                if 'SELECT_MEMBER' not in prev_ops:
                    issues['wrong_opcode'].append({
                        'frame_idx': f.get('frame_index', i),
                        'issue': "BOOST_SCORE uses CONTEXT but text says 'this card'",
                        'current': f"target_slot: {slot}",
                        'recommendation': 'Should use CARD_SELF or similar explicit target'
                    })
    
    # === 3. NEEDS ENHANCEMENT ===
    
    # 3a. Missing color/group specification
    for i, f in enumerate(frames):
        if f.get('op') in ['COUNT_STAGE', 'SELECT_MEMBER']:
            attr = f.get('attr', {})
            # Check if text specifies group but frame doesn't
            if 'Liella' in text and not attr.get('group_id'):
                issues['needs_enhancement'].append({
                    'frame_idx': f.get('frame_index', i),
                    'issue': "Text mentions Liella! but frame has no group_id filter",
                    'current': f"group_enabled: {attr.get('group_enabled', 0)}",
                    'recommendation': 'Add attr: {group_enabled: 1, group_id: "LIELLA"}'
                })
            if 'μ\'s' in text or 'ミューズ' in text:
                if not attr.get('group_id') or attr.get('group_id') != 'MUSE':
                    issues['needs_enhancement'].append({
                        'frame_idx': f.get('frame_index', i),
                        'issue': "Text mentions μ's but frame has wrong/missing group_id",
                        'recommendation': 'Add attr: {group_enabled: 1, group_id: "MUSE"}'
                    })
            if 'Aqours' in text or 'アクア' in text:
                if not attr.get('group_id') or attr.get('group_id') != 'AQOURS':
                    issues['needs_enhancement'].append({
                        'frame_idx': f.get('frame_index', i),
                        'issue': "Text mentions Aqours but frame has wrong/missing group_id",
                        'recommendation': 'Add attr: {group_enabled: 1, group_id: "AQOURS"}'
                    })
    
    # 3b. Missing target_player specification
    for i, f in enumerate(frames):
        if f.get('op') in ['COUNT_STAGE', 'GROUP_FILTER', 'SELECT_MEMBER']:
            attr = f.get('attr', {})
            slot = f.get('slot', {})
            # Check if it's checking own stage but no target_player
            if '自分の' in text and 'STAGE' in slot.get('target_slot', ''):
                if not attr.get('target_player'):
                    issues['needs_enhancement'].append({
                        'frame_idx': f.get('frame_index', i),
                        'issue': f"Checking own stage but missing target_player: SELF",
                        'current': f"attr: {list(attr.keys())}",
                        'recommendation': 'Add target_player: SELF to attr'
                    })
    
    # 3c. Wrong area specification
    for i, f in enumerate(frames):
        if f.get('op') in ['SELECT_MEMBER', 'COUNT_STAGE']:
            slot = f.get('slot', {})
            area_idx = slot.get('area_idx')
            target_slot = slot.get('target_slot', '')
            
            # Text mentions center area but area_idx not set or wrong
            if 'センターエリア' in text:
                if target_slot != 'STAGE_2' and area_idx != 2:
                    issues['needs_enhancement'].append({
                        'frame_idx': f.get('frame_index', i),
                        'issue': "Text mentions center area but frame targets wrong slot",
                        'current': f"target_slot: {target_slot}, area_idx: {area_idx}",
                        'recommendation': 'Set target_slot: STAGE_2 or area_idx: 2'
                    })
    
    # 3d. Missing optional flag for optional actions
    for i, f in enumerate(frames):
        if f.get('op') in ['FORMATION_CHANGE', 'MOVE_MEMBER']:
            attr = f.get('attr', {})
            if 'してもよい' in text and not attr.get('is_optional'):
                issues['needs_enhancement'].append({
                    'frame_idx': f.get('frame_index', i),
                    'issue': f"Text says 'may' (してもよい) but {f.get('op')} not marked optional",
                    'current': f"is_optional: {attr.get('is_optional', 'missing')}",
                    'recommendation': 'Add is_optional: 1 to attr'
                })
    
    # === 4. STRUCTURAL ISSUES ===
    
    # 4a. SELECT_MODE without proper JUMP chain
    select_modes = [(i, f) for i, f in enumerate(frames) if f.get('op') == 'SELECT_MODE']
    for i, sm in select_modes:
        value = sm.get('value', 0)
        # Count JUMP frames immediately after
        jump_count = 0
        for j in range(i+1, min(i+1+value, len(frames))):
            if frames[j].get('op') == 'JUMP':
                jump_count += 1
        if jump_count != value:
            issues['structural_issues'].append({
                'frame_idx': sm.get('frame_index', i),
                'issue': f"SELECT_MODE value={value} but only {jump_count} JUMP frames follow",
                'recommendation': f'Should have {value} JUMP frames immediately after SELECT_MODE'
            })
    
    # 4b. Effect frame without proper targeting
    effect_ops = ['BOOST_SCORE', 'ADD_BLADES', 'ADD_HEART', 'ACTIVATE_ENERGY']
    for i, f in enumerate(frames):
        if f.get('op') in effect_ops:
            slot = f.get('slot', {})
            if slot.get('target_slot') == 'CONTEXT':
                # Check if there's a prior selection
                prev_ops = [frames[j].get('op') for j in range(i)]
                if 'SELECT_MEMBER' not in prev_ops and 'COUNT_STAGE' not in prev_ops:
                    issues['structural_issues'].append({
                        'frame_idx': f.get('frame_index', i),
                        'issue': f"{f.get('op')} uses CONTEXT but no prior member selection",
                        'recommendation': 'Add SELECT_MEMBER before or use explicit target'
                    })
    
    # 4c. OR cost without SELECT_MODE
    if any(word in text for word in ['するか', 'か、', 'または']):
        if '起動' in text or '支払ってもよい' in text:
            has_select_mode = any(f.get('op') == 'SELECT_MODE' for f in frames)
            if not has_select_mode:
                # Check if it's truly an OR cost
                if ('するか、' in text or 'するか：' in text) and 'メンバーを' in text:
                    issues['structural_issues'].append({
                        'frame_idx': 0,
                        'issue': "Text has OR cost (X するか Y する) but no SELECT_MODE frame",
                        'recommendation': 'Add SELECT_MODE with value=2 followed by JUMP frames for each option'
                    })
    
    return issues

def main():
    print("Loading ability data...")
    data = load_json()
    abilities = data.get('abilities', [])
    
    all_issues = []
    stats = defaultdict(int)
    
    print(f"Scanning {len(abilities)} abilities...")
    
    for ability in abilities:
        card_ref = extract_card_ref(ability)
        issues = deep_scan_ability(ability)
        
        # Count issues
        has_issues = False
        for category, issue_list in issues.items():
            if issue_list:
                has_issues = True
                stats[category] += len(issue_list)
        
        if has_issues:
            all_issues.append({
                'card_ref': card_ref,
                'text': ability.get('primary_text_jp', '')[:150],
                'issues': issues
            })
    
    # Write report
    report_path = DOCS_DIR / "deep_ability_scan_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Deep Ability Scan Report\n\n")
        f.write(f"Total abilities scanned: {len(abilities)}\n")
        f.write(f"Abilities with issues: {len(all_issues)}\n\n")
        
        f.write("## Issue Summary\n\n")
        f.write(f"- Missing frames: {stats['missing_frames']}\n")
        f.write(f"- Wrong opcodes: {stats['wrong_opcode']}\n")
        f.write(f"- Needs enhancement: {stats['needs_enhancement']}\n")
        f.write(f"- Structural issues: {stats['structural_issues']}\n\n")
        
        # Write detailed issues
        for item in all_issues:
            f.write(f"## {item['card_ref']}\n\n")
            f.write(f"**Text:** {item['text']}\n\n")
            
            for category, issue_list in item['issues'].items():
                if issue_list:
                    f.write(f"### {category.replace('_', ' ').title()}\n\n")
                    for issue in issue_list:
                        f.write(f"**Frame {issue['frame_idx']}:**\n")
                        f.write(f"- Issue: {issue['issue']}\n")
                        if 'current' in issue:
                            f.write(f"- Current: {issue['current']}\n")
                        f.write(f"- Fix: {issue['recommendation']}\n\n")
            f.write("---\n\n")
    
    print(f"\nScan complete!")
    print(f"Total issues found: {sum(stats.values())}")
    print(f"  - Missing frames: {stats['missing_frames']}")
    print(f"  - Wrong opcodes: {stats['wrong_opcode']}")
    print(f"  - Needs enhancement: {stats['needs_enhancement']}")
    print(f"  - Structural issues: {stats['structural_issues']}")
    print(f"\nReport written to: {report_path}")
    
    return all_issues, stats

if __name__ == '__main__':
    issues, stats = main()
