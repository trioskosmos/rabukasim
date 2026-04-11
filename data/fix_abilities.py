#!/usr/bin/env python3
"""
Comprehensive ability frame fixer.
Reads ability_frame_source.json and fixes identified issues.
"""

import json
import re
from pathlib import Path
from copy import deepcopy

# Path to files
DATA_DIR = Path("C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/data")
DOCS_DIR = Path("C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/docs")
JSON_PATH = DATA_DIR / "ability_frame_source.json"
ANALYSIS_PATH = DOCS_DIR / "ability_fixes_report.md"

def load_json():
    with open(JSON_PATH, encoding='utf-8') as f:
        return json.load(f)

def save_json(data):
    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def extract_card_ref(ability):
    """Get first card reference."""
    refs = ability.get('card_refs', [])
    if refs:
        return f"{refs[0].get('card_no', 'Unknown')}#Ab{refs[0].get('ability_index', 0)}"
    return "Unknown"

def needs_target_player(text, frame):
    """Check if frame needs target_player: SELF."""
    if '自分の' in text and frame.get('op') in ['COUNT_STAGE', 'GROUP_FILTER', 'SELECT_MEMBER']:
        slot = frame.get('slot', {})
        target = slot.get('target_slot', '')
        if 'STAGE' in target and not frame.get('attr', {}).get('target_player'):
            return True
    return False

def is_mandatory_cost(text, frame):
    """Check if cost is mandatory vs optional."""
    # If text says "置く：" or similar with no "もよい", it's mandatory
    if frame.get('op') in ['MOVE_TO_DISCARD', 'SET_TAPPED', 'PAY_ENERGY']:
        if 'もよい' not in text and 'optional' not in text:
            return True
    return False

def fix_ability(ability, fix_log):
    """Fix issues in a single ability. Returns True if modified."""
    modified = False
    frames = ability.get('frames', [])
    text = ability.get('primary_text_jp', '')
    card_ref = extract_card_ref(ability)
    
    if not frames or not text:
        return False
    
    # Fix 1: Add missing target_player: SELF for own stage checks
    for i, frame in enumerate(frames):
        if needs_target_player(text, frame):
            if 'attr' not in frame:
                frame['attr'] = {}
            if not frame['attr'].get('target_player'):
                frame['attr']['target_player'] = 'SELF'
                fix_log.append(f"{card_ref}: Frame {frame.get('frame_index', i)} - Added target_player: SELF for own stage check")
                modified = True
    
    # Fix 2: Fix optional cost detection
    for i, frame in enumerate(frames):
        if frame.get('op') == 'MOVE_TO_DISCARD' and frame.get('attr', {}).get('is_optional'):
            # Check if this is actually mandatory (no "もよい" in text)
            if is_mandatory_cost(text, frame):
                # This is actually mandatory, remove is_optional
                del frame['attr']['is_optional']
                fix_log.append(f"{card_ref}: Frame {frame.get('frame_index', i)} - Removed incorrect is_optional from mandatory cost")
                modified = True
            else:
                # Ensure it has JUMP_IF_FALSE after
                if i + 1 < len(frames) and frames[i + 1].get('op') != 'JUMP_IF_FALSE':
                    # Need to insert JUMP_IF_FALSE
                    jump_frame = {
                        "op": "JUMP_IF_FALSE",
                        "frame_index": i + 1,
                        "value": 1
                    }
                    # Update subsequent frame indices
                    for f in frames[i + 1:]:
                        f['frame_index'] = f.get('frame_index', 0) + 1
                    frames.insert(i + 1, jump_frame)
                    fix_log.append(f"{card_ref}: Added JUMP_IF_FALSE after optional MOVE_TO_DISCARD")
                    modified = True
    
    # Fix 3: Replace SELECT_MEMBER with COUNT_STAGE for specific areas
    for i, frame in enumerate(frames):
        if frame.get('op') == 'SELECT_MEMBER':
            # Check if text specifies exact location (center area, etc.)
            if 'センターエリア' in text and '自分のステージのセンター' in text:
                area_idx = frame.get('slot', {}).get('area_idx')
                if area_idx == 2:  # Center area
                    # Replace with COUNT_STAGE
                    new_frame = {
                        "op": "COUNT_STAGE",
                        "frame_index": frame['frame_index'],
                        "value": frame.get('value', 1),
                        "attr": {
                            "target_player": "SELF",
                            "group_enabled": frame.get('attr', {}).get('group_enabled', 0),
                            "group_id": frame.get('attr', {}).get('group_id', '')
                        },
                        "slot": {
                            "target_slot": "STAGE_2",
                            "comparison": "GE"
                        }
                    }
                    frames[i] = new_frame
                    fix_log.append(f"{card_ref}: Replaced SELECT_MEMBER with COUNT_STAGE for automatic center area check")
                    modified = True
    
    # Fix 4: Fix GROUP_FILTER with wrong value for "only" conditions
    for i, frame in enumerate(frames):
        if frame.get('op') == 'GROUP_FILTER':
            value = frame.get('value', 0)
            # If text says "only" but value is arbitrary number, flag it
            if 'のみ' in text and value not in [0, 1]:
                # This is likely wrong - "only" means ALL members must be in group
                # Should use COUNT_STAGE sequence instead
                fix_log.append(f"{card_ref}: Frame {frame.get('frame_index', i)} - GROUP_FILTER with value={value} but text says 'only' - needs COUNT_STAGE+SUM_VALUE pattern")
                # Don't auto-fix this as it requires structural changes
    
    # Fix 5: Add missing moved_this_turn check
    if 'このターン' in text and '移動' in text:
        has_check = any(f.get('attr', {}).get('check_moved_this_turn') for f in frames)
        if not has_check:
            # Add check to the first relevant COUNT_STAGE or SELECT_MEMBER
            for f in frames:
                if f.get('op') in ['COUNT_STAGE', 'SELECT_MEMBER', 'GROUP_FILTER']:
                    if 'attr' not in f:
                        f['attr'] = {}
                    f['attr']['check_moved_this_turn'] = 1
                    fix_log.append(f"{card_ref}: Added check_moved_this_turn flag for movement check")
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
        if fix_ability(ability, fix_log):
            modified_count += 1
    
    # Save changes
    if fix_log:
        print(f"\nSaving changes... ({modified_count} abilities modified)")
        save_json(data)
    
    # Write report
    print("Writing fix report...")
    with open(ANALYSIS_PATH, 'w', encoding='utf-8') as f:
        f.write("# Ability Frame Fixes Report\n\n")
        f.write(f"Total abilities analyzed: {len(abilities)}\n")
        f.write(f"Abilities modified: {modified_count}\n")
        f.write(f"Total fixes applied: {len(fix_log)}\n\n")
        
        if fix_log:
            f.write("## Fixes Applied\n\n")
            for entry in fix_log:
                f.write(f"- {entry}\n")
        else:
            f.write("No automatic fixes were applied.\n")
    
    print(f"\nDone! Report written to: {ANALYSIS_PATH}")
    print(f"Modified {modified_count} abilities with {len(fix_log)} fixes.")

if __name__ == '__main__':
    main()
