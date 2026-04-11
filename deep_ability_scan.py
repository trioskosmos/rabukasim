#!/usr/bin/env python3
"""Deep scan of all abilities for frame issues."""

import json
import re

def load_abilities():
    with open('data/ability_frame_source.json', encoding='utf-8') as f:
        return json.load(f)

def analyze_frame_issues(ability, index):
    """Deep analysis of ability frames."""
    issues = []
    text = ability.get('primary_text_jp', '')
    frames = ability.get('frames', [])
    trigger = ability.get('trigger', '')
    card_refs = ability.get('card_refs', [])
    card_no = card_refs[0].get('card_no', 'Unknown') if card_refs else 'Unknown'
    
    if not frames:
        return [(index, card_no, 'EMPTY_FRAMES', 'No frames defined')]
    
    # Check 1: ON_PLAY abilities should have proper entry flow
    if trigger == 'ON_PLAY':
        first_op = frames[0].get('op') if frames else None
        # Optional effects should have is_optional on first meaningful frame
        if 'してもよい' in text or '行ってもよい' in text:
            has_optional = any(f.get('attr', {}).get('is_optional') for f in frames[:2])
            if not has_optional and first_op not in ['SELECT_MODE', 'SUM_VALUE']:
                issues.append((index, card_no, 'MISSING_OPTIONAL', 'Text has optional but no is_optional flag'))
    
    # Check 2: Conditional effects should have condition checks
    if any(x in text for x in ['場合', 'とき', 'いる', 'ある']):
        # Check for condition opcodes
        condition_ops = ['COUNT_STAGE', 'IN_SUCCESS_PILE', 'HAS_KEYWORD', 'COUNT_BLADES', 
                        'COUNT_SUCCESS', 'COUNT_ENERGY', 'SCORE_COMPARE']
        jump_ops = ['JUMP_IF_FALSE', 'JUMP_IF_TRUE', 'JUMP']
        has_condition = any(f.get('op') in condition_ops for f in frames)
        has_jump = any(f.get('op') in jump_ops for f in frames)
        
        # Skip if it's a CONSTANT ability (they handle conditions differently)
        # Skip if it has SELECT_MODE (flavor choice handles its own flow)
        has_select_mode = any(f.get('op') == 'SELECT_MODE' for f in frames)
        
        if not has_select_mode and not has_condition and not has_jump and trigger != 'CONSTANT':
            # Check if text actually describes a condition
            # Simple patterns that don't need conditions
            simple_patterns = ['カードを', '引き', '置く', '得る']
            is_simple = all(p in text for p in simple_patterns[:2])
            
            if not is_simple:
                issues.append((index, card_no, 'MISSING_CONDITION', f'Text has conditions but no check: {text[:50]}...'))
    
    # Check 3: Group filters
    group_keywords = {
        "μ's": "MUSE",
        "Aqours": "AQOURS", 
        "虹ヶ咲": "NIJIGASAKI",
        "Liella!": "LIELLA",
        "蓮ノ空": "HASUNOSORA",
        "Saint Snow": "SAINT_SNOW",
        "SaintSnow": "SAINT_SNOW",
    }
    
    for jp_group, group_id in group_keywords.items():
        if jp_group in text:
            # Check if any frame has group filter
            has_group = any(
                f.get('attr', {}).get('group_enabled') and 
                f.get('attr', {}).get('group_id') == group_id
                for f in frames
            )
            # Skip if it's a keyword/character check
            if not has_group and 'keyword' not in text.lower():
                # Check if the group reference is about a specific card type
                member_pattern = f"『{jp_group}』のメンバー"
                if member_pattern in text:
                    issues.append((index, card_no, 'MISSING_GROUP_FILTER', f'Text references {jp_group} but no group_id:{group_id} filter'))
    
    # Check 4: RECOVER_MEMBER and RECOVER_LIVE should have zone specifications
    for f in frames:
        if f.get('op') in ['RECOVER_MEMBER', 'RECOVER_LIVE']:
            slot = f.get('slot', {})
            if not slot.get('source_zone'):
                issues.append((index, card_no, 'MISSING_SOURCE_ZONE', f'{f.get("op")} missing source_zone'))
    
    # Check 5: COUNT_X operations should have comparison operators
    for f in frames:
        if f.get('op', '').startswith('COUNT_'):
            slot = f.get('slot', {})
            attr = f.get('attr', {})
            has_comparison = (
                slot.get('comparison') or 
                attr.get('is_ge') or 
                attr.get('is_le') or 
                attr.get('is_eq') or
                attr.get('is_gt') or
                attr.get('is_lt')
            )
            # Only flag if value > 0 (0 values might be for accumulation)
            if f.get('value', 0) > 0 and not has_comparison:
                issues.append((index, card_no, 'MISSING_COMPARISON', f'{f.get("op")} value={f.get("value")} but no comparison'))
    
    # Check 6: JUMP_IF_FALSE should have reasonable jump values
    for i, f in enumerate(frames):
        if f.get('op') == 'JUMP_IF_FALSE':
            jump_val = f.get('value', 0)
            remaining = len(frames) - i - 1
            if jump_val > remaining:
                issues.append((index, card_no, 'INVALID_JUMP', f'JUMP_IF_FALSE value={jump_val} but only {remaining} frames remain'))
    
    # Check 7: Energy costs should be paid
    if trigger == 'ACTIVATED':
        energy_match = re.search(r'\[?\s*{{icon_energy.png\|(\w+)}}\s*\]?', text)
        if energy_match:
            # Check for PAY_ENERGY
            has_pay = any(f.get('op') == 'PAY_ENERGY' for f in frames)
            has_sum = any(f.get('op') == 'SUM_VALUE' for f in frames)
            if not has_pay and not has_sum:
                issues.append((index, card_no, 'MISSING_PAY_ENERGY', 'Activated ability with energy cost but no PAY_ENERGY'))
    
    # Check 8: Card type filters
    if 'メンバーカード' in text and ('控え室から' in text or '手札に加える' in text or '登場' in text):
        # Check for card_type filter
        has_type_filter = any(
            f.get('attr', {}).get('card_type') == 'MEMBER' or
            f.get('attr', {}).get('zone_mask') == 'MEMBER'
            for f in frames
        )
        if not has_type_filter:
            pass  # Don't flag - many abilities rely on implicit type from context
    
    # Check 9: Heart references should have heart_type
    heart_pattern = r'{{(?:icon_)?heart(?:_0?(\d+)|[^}]+).png'
    heart_match = re.search(heart_pattern, text)
    if heart_match:
        heart_num = heart_match.group(1) if heart_match.group(1) else None
        # Check for heart_type in frames
        has_heart_attr = any(
            f.get('attr', {}).get('heart_type') or 
            'heart' in str(f.get('attr', {})).lower()
            for f in frames
        )
        # Only flag if the ability is about hearts (adding/removing)
        if '得る' in text or '失う' in text or 'ブレード' in text:
            pass  # Heart abilities often use icon_blade.png instead
    
    return issues

def main():
    data = load_abilities()
    abilities = data['abilities']
    
    all_issues = []
    
    print(f"Scanning {len(abilities)} abilities...")
    print("="*80)
    
    for i, ability in enumerate(abilities):
        issues = analyze_frame_issues(ability, i)
        all_issues.extend(issues)
        
        if (i + 1) % 100 == 0:
            print(f"  Reviewed {i + 1}/{len(abilities)} abilities...")
    
    print("="*80)
    
    # Categorize issues
    categories = {}
    for idx, card, issue_type, desc in all_issues:
        if issue_type not in categories:
            categories[issue_type] = []
        categories[issue_type].append((idx, card, desc))
    
    print(f"\nFound {len(all_issues)} issues across {len(categories)} categories:\n")
    
    for issue_type, items in sorted(categories.items()):
        print(f"\n{issue_type}: {len(items)} occurrences")
        for idx, card, desc in items[:5]:  # Show first 5 of each type
            print(f"  [{idx}] {card}: {desc[:60]}...")
        if len(items) > 5:
            print(f"  ... and {len(items) - 5} more")
    
    # Save detailed report
    with open('ability_frame_issues_detailed.txt', 'w', encoding='utf-8') as f:
        f.write(f"Deep Ability Scan Report\n")
        f.write(f"Total abilities: {len(abilities)}\n")
        f.write(f"Issues found: {len(all_issues)}\n")
        f.write("="*80 + "\n\n")
        
        for idx, card, issue_type, desc in sorted(all_issues, key=lambda x: x[0]):
            f.write(f"[{idx}] {card}: {issue_type}\n")
            f.write(f"  {desc}\n\n")
    
    print(f"\n✓ Detailed report saved to ability_frame_issues_detailed.txt")

if __name__ == '__main__':
    main()
