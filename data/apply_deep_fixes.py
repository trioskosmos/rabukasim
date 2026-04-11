#!/usr/bin/env python3
"""
Apply comprehensive fixes to all identified ability frame issues.
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

def save_json(data):
    backup_path = JSON_PATH.with_suffix('.json.backup')
    # Create backup first
    with open(JSON_PATH, encoding='utf-8') as f:
        with open(backup_path, 'w', encoding='utf-8') as bf:
            bf.write(f.read())
    # Save new data
    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def extract_card_ref(ability):
    refs = ability.get('card_refs', [])
    if refs:
        return f"{refs[0].get('card_no', 'Unknown')}#Ab{refs[0].get('ability_index', 0)}"
    return "Unknown"

def reindex_frames(frames):
    """Reindex all frames to be sequential."""
    for i, f in enumerate(frames):
        f['frame_index'] = i

def apply_fixes(ability, fix_log):
    """Apply all applicable fixes to an ability."""
    modified = False
    frames = ability.get('frames', [])
    text = ability.get('primary_text_jp', '')
    card_ref = extract_card_ref(ability)
    
    if not frames or not text:
        return False
    
    # === FIX TYPE 1: Add missing target_player: SELF ===
    for i, f in enumerate(frames):
        if f.get('op') in ['COUNT_STAGE', 'GROUP_FILTER', 'SELECT_MEMBER']:
            attr = f.get('attr', {})
            slot = f.get('slot', {})
            
            # Check if it's checking own stage
            if '自分の' in text and 'STAGE' in slot.get('target_slot', ''):
                if not attr.get('target_player'):
                    if 'attr' not in f:
                        f['attr'] = {}
                    f['attr']['target_player'] = 'SELF'
                    fix_log.append(f"{card_ref}: Frame {f.get('frame_index', i)} - Added target_player: SELF")
                    modified = True
    
    # === FIX TYPE 2: Add group_id filters where missing ===
    for i, f in enumerate(frames):
        if f.get('op') in ['COUNT_STAGE', 'SELECT_MEMBER', 'GROUP_FILTER']:
            attr = f.get('attr', {})
            if not attr.get('group_id'):
                # Check text for group mentions
                if 'Liella' in text and 'group_id' not in str(attr):
                    attr['group_enabled'] = 1
                    attr['group_id'] = 'LIELLA'
                    fix_log.append(f"{card_ref}: Frame {f.get('frame_index', i)} - Added Liella! group filter")
                    modified = True
                elif ('μ\'s' in text or 'ミューズ' in text):
                    attr['group_enabled'] = 1
                    attr['group_id'] = 'MUSE'
                    fix_log.append(f"{card_ref}: Frame {f.get('frame_index', i)} - Added μ's group filter")
                    modified = True
                elif 'Aqours' in text or 'アクア' in text:
                    attr['group_enabled'] = 1
                    attr['group_id'] = 'AQOURS'
                    fix_log.append(f"{card_ref}: Frame {f.get('frame_index', i)} - Added Aqours group filter")
                    modified = True
                elif '虹ヶ咲' in text or 'にじがさき' in text:
                    attr['group_enabled'] = 1
                    attr['group_id'] = 'NIJIGAKU'
                    fix_log.append(f"{card_ref}: Frame {f.get('frame_index', i)} - Added 虹ヶ咲 group filter")
                    modified = True
    
    # === FIX TYPE 3: Add is_optional for optional actions ===
    for i, f in enumerate(frames):
        if f.get('op') in ['FORMATION_CHANGE', 'MOVE_MEMBER', 'MOVE_TO_DISCARD']:
            attr = f.get('attr', {})
            if 'してもよい' in text and not attr.get('is_optional'):
                attr['is_optional'] = 1
                fix_log.append(f"{card_ref}: Frame {f.get('frame_index', i)} - Added is_optional: 1 for optional action")
                modified = True
    
    # === FIX TYPE 4: Add missing JUMP_IF_FALSE after conditions ===
    condition_ops = ['COUNT_STAGE', 'GROUP_FILTER']
    for i, f in enumerate(frames):
        if f.get('op') in condition_ops:
            if i + 1 < len(frames):
                next_op = frames[i + 1].get('op')
                if next_op not in ['JUMP_IF_FALSE', 'JUMP', 'RETURN']:
                    # Need to insert JUMP_IF_FALSE
                    jump_value = 1
                    jump_frame = {
                        "op": "JUMP_IF_FALSE",
                        "frame_index": i + 1,
                        "value": jump_value
                    }
                    frames.insert(i + 1, jump_frame)
                    reindex_frames(frames)
                    fix_log.append(f"{card_ref}: Added JUMP_IF_FALSE after {f.get('op')}")
                    modified = True
    
    # === FIX TYPE 5: Add missing JUMP_IF_FALSE after optional costs ===
    cost_ops = ['PAY_ENERGY', 'MOVE_TO_DISCARD', 'SET_TAPPED']
    for i, f in enumerate(frames):
        if f.get('op') in cost_ops and f.get('attr', {}).get('is_optional'):
            if i + 1 < len(frames) and frames[i + 1].get('op') != 'JUMP_IF_FALSE':
                jump_frame = {
                    "op": "JUMP_IF_FALSE",
                    "frame_index": i + 1,
                    "value": 1
                }
                frames.insert(i + 1, jump_frame)
                reindex_frames(frames)
                fix_log.append(f"{card_ref}: Added JUMP_IF_FALSE after optional {f.get('op')}")
                modified = True
    
    # === FIX TYPE 6: Fix target_slot for center area ===
    for i, f in enumerate(frames):
        if f.get('op') in ['SELECT_MEMBER', 'COUNT_STAGE']:
            slot = f.get('slot', {})
            # If text mentions center area
            if 'センターエリア' in text and '自分のステージのセンター' in text:
                if slot.get('area_idx') == 2 and slot.get('target_slot') not in ['STAGE_2', 'CONTEXT']:
                    slot['target_slot'] = 'STAGE_2'
                    fix_log.append(f"{card_ref}: Frame {f.get('frame_index', i)} - Fixed target_slot to STAGE_2 for center area")
                    modified = True
    
    # === FIX TYPE 7: Replace SELECT_MEMBER with COUNT_STAGE for automatic checks ===
    for i, f in enumerate(frames):
        if f.get('op') == 'SELECT_MEMBER':
            # Check if this should be automatic
            if 'センターエリア' in text and '自分のステージのセンター' in text:
                if f.get('slot', {}).get('area_idx') == 2:
                    # Convert to COUNT_STAGE
                    new_frame = {
                        "op": "COUNT_STAGE",
                        "frame_index": f['frame_index'],
                        "value": f.get('value', 1),
                        "attr": {
                            **f.get('attr', {}),
                            "target_player": "SELF"
                        },
                        "slot": {
                            "target_slot": "STAGE_2",
                            "comparison": "GE"
                        }
                    }
                    frames[i] = new_frame
                    fix_log.append(f"{card_ref}: Replaced SELECT_MEMBER with COUNT_STAGE for automatic center check")
                    modified = True
                    
                    # Also add JUMP_IF_FALSE after if not present
                    if i + 1 < len(frames) and frames[i + 1].get('op') != 'JUMP_IF_FALSE':
                        jump_frame = {
                            "op": "JUMP_IF_FALSE",
                            "frame_index": i + 1,
                            "value": 1
                        }
                        frames.insert(i + 1, jump_frame)
                        reindex_frames(frames)
    
    # === FIX TYPE 8: Add check_moved_this_turn for movement conditions ===
    if 'このターン' in text and '移動' in text:
        has_check = any(f.get('attr', {}).get('check_moved_this_turn') for f in frames)
        if not has_check:
            for f in frames:
                if f.get('op') in ['COUNT_STAGE', 'SELECT_MEMBER']:
                    if 'attr' not in f:
                        f['attr'] = {}
                    f['attr']['check_moved_this_turn'] = 1
                    fix_log.append(f"{card_ref}: Added check_moved_this_turn flag")
                    modified = True
                    break
    
    return modified

def main():
    print("Loading ability data...")
    data = load_json()
    abilities = data.get('abilities', [])
    
    fix_log = []
    modified_count = 0
    
    print(f"Processing {len(abilities)} abilities...")
    
    for ability in abilities:
        if apply_fixes(ability, fix_log):
            modified_count += 1
    
    # Save changes
    if fix_log:
        print(f"\nSaving {len(fix_log)} fixes across {modified_count} abilities...")
        save_json(data)
    
    # Validate JSON
    try:
        with open(JSON_PATH, encoding='utf-8') as f:
            json.load(f)
        print("✓ JSON validation passed")
    except json.JSONDecodeError as e:
        print(f"✗ JSON validation failed: {e}")
        return
    
    # Write report
    report_path = DOCS_DIR / "deep_fixes_applied.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Deep Ability Fixes Applied\n\n")
        f.write(f"Total abilities modified: {modified_count}\n")
        f.write(f"Total fixes applied: {len(fix_log)}\n\n")
        f.write("## Fixes by Category\n\n")
        
        categories = defaultdict(list)
        for entry in fix_log:
            if 'target_player' in entry:
                categories['target_player: SELF'].append(entry)
            elif 'group_id' in entry:
                categories['group_id filters'].append(entry)
            elif 'is_optional' in entry:
                categories['is_optional flags'].append(entry)
            elif 'JUMP_IF_FALSE' in entry:
                categories['JUMP_IF_FALSE additions'].append(entry)
            elif 'target_slot' in entry:
                categories['target_slot fixes'].append(entry)
            elif 'SELECT_MEMBER' in entry and 'COUNT_STAGE' in entry:
                categories['SELECT_MEMBER→COUNT_STAGE'].append(entry)
            elif 'check_moved' in entry:
                categories['movement checks'].append(entry)
            else:
                categories['other'].append(entry)
        
        for cat, entries in sorted(categories.items()):
            f.write(f"### {cat} ({len(entries)})\n\n")
            for entry in entries:
                f.write(f"- {entry}\n")
            f.write("\n")
        
        f.write("\n## All Fixes\n\n")
        for entry in fix_log:
            f.write(f"- {entry}\n")
    
    print(f"\n✓ Done! Modified {modified_count} abilities with {len(fix_log)} fixes.")
    print(f"✓ Report written to: {report_path}")

if __name__ == '__main__':
    main()
