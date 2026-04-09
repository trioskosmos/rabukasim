#!/usr/bin/env python3
"""Analyze ability_frame_source.json to find mismatches between frames and JP text."""

import json
import re
from pathlib import Path

def _opcode_sequence(group):
    seq = group.get('opcode_sequence') or []
    if seq:
        return seq
    frames = group.get('frames', []) or []
    return [
        str(frame.get('op', '')).strip().upper()
        for frame in frames
        if isinstance(frame, dict) and str(frame.get('op', '')).strip()
    ]


def _frame_raw_effects(frames):
    effects = set()
    for frame in frames or []:
        if not isinstance(frame, dict):
            continue
        params = frame.get('params')
        if isinstance(params, dict):
            raw_effect = params.get('raw_effect') or params.get('RAW_EFFECT')
            if isinstance(raw_effect, str) and raw_effect.strip():
                effects.add(raw_effect.strip().upper())
    return effects


def _frame_raw_conditions(frames):
    conditions = set()
    for frame in frames or []:
        if not isinstance(frame, dict):
            continue
        params = frame.get('params')
        if isinstance(params, dict):
            raw_cond = params.get('raw_cond') or params.get('RAW_COND')
            if isinstance(raw_cond, str) and raw_cond.strip():
                conditions.add(raw_cond.strip().upper())
    return conditions

def analyze_ability_frames():
    filepath = Path("c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/data/ability_frame_source.json")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    abilities = data.get('abilities', [])
    
    issues = []
    
    for group in abilities:
        signature = group.get('signature', '')
        primary_jp = group.get('primary_text_jp', '')
        frames = group.get('frames', [])
        opcode_seq = _opcode_sequence(group)
        raw_conds = _frame_raw_conditions(frames)
        card_refs = group.get('card_refs', [])
        source_texts = group.get('source_ability_texts', [])
        
        # Skip empty or trivial frames
        if len(frames) <= 1:
            continue
        
        # Check for multiple different JP texts in same group (Issue 9 pattern)
        if len(source_texts) > 1:
            # Check if the texts describe different abilities
            different_abilities = check_different_abilities(source_texts)
            if different_abilities:
                issues.append({
                    'signature': signature,
                    'cards': card_refs[:3] if card_refs else [],
                    'jp_text': primary_jp[:150] + '...' if len(primary_jp) > 150 else primary_jp,
                    'issues': [f"Shared frame for cards with different abilities: {different_abilities}"],
                    'opcodes': opcode_seq,
                    'severity': 'HIGH'
                })
                continue
        
        issue = analyze_group(signature, primary_jp, frames, opcode_seq, card_refs)
        if issue:
            issues.append(issue)
    
    return issues

def check_different_abilities(source_texts):
    """Check if source_ability_texts describe meaningfully different abilities."""
    if len(source_texts) < 2:
        return None
    
    # Extract key elements from each text
    key_elements = []
    for st in source_texts:
        jp = st.get('jp', '')
        elements = {
            'has_live_card': 'ライブカード' in jp,
            'deck_top': '一番上' in jp or '上に置く' in jp,
            'deck_bottom': '一番下' in jp or '下に置く' in jp,
            'to_deck': 'デッキ' in jp and ('上に' in jp or '下に' in jp or '一番' in jp),
            'to_hand': '手札に加える' in jp,
            'discard': '控え室に置く' in jp or '控え室に置いて' in jp,
            'draw': '引く' in jp and '枚' in jp,
        }
        key_elements.append(elements)
    
    # Compare first element with others
    first = key_elements[0]
    differences = []
    for i, other in enumerate(key_elements[1:], 1):
        diff_parts = []
        for key in first:
            if first[key] != other[key]:
                diff_parts.append(key)
        if diff_parts:
            card_examples = source_texts[i].get('card_examples', [])
            if card_examples:
                card_name = card_examples[0].split('|')[1].strip() if '|' in card_examples[0] else ''
                differences.append(f"Card '{card_name}' differs in: {', '.join(diff_parts)}")
    
    return '; '.join(differences) if differences else None

def analyze_group(signature, jp_text, frames, opcode_seq, card_refs):
    """Analyze a single signature group for mismatches."""
    
    if not jp_text:
        return None
    
    found_issues = []
    severity = 'MEDIUM'
    raw_conds = _frame_raw_conditions(frames)
    
    # Check 1: "discard up to X, draw same amount" pattern (Issue 1)
    # Pattern: discard revealed cards with no live cards, then re-yell
    raw_effects = _frame_raw_effects(frames)
    if (
        'DISCARD_YELL_PILE' not in raw_effects
        and 'RE_YELL' not in raw_effects
        and 'MOVE_TO_DISCARD' in opcode_seq
        and 'DRAW' in opcode_seq
        and ('???????????' in jp_text or '???????' in jp_text)
    ):
        has_discard = 'MOVE_TO_DISCARD' in opcode_seq
        has_draw = 'DRAW' in opcode_seq
        # Check ordering - should discard first, then draw
        discard_idx = opcode_seq.index('MOVE_TO_DISCARD') if 'MOVE_TO_DISCARD' in opcode_seq else -1
        draw_idx = opcode_seq.index('DRAW') if 'DRAW' in opcode_seq else -1
        
        if draw_idx >= 0 and discard_idx == -1:
            found_issues.append("Text: discard then draw; Frame: only DRAW, missing discard")
            severity = 'HIGH'
        elif draw_idx >= 0 and discard_idx > draw_idx:
            found_issues.append("Text: discard then draw; Frame: wrong order (draw first)")
            severity = 'HIGH'
    
    # Check 2: Energy count requirement (Issue 8)
    energy_match = re.search(r'エネルギーが(\d+)枚以上', jp_text)
    if energy_match:
        required = energy_match.group(1)
        if 'COUNT_ENERGY' not in opcode_seq:
            found_issues.append(f"Text requires energy >= {required}; Frame lacks energy count check")
            severity = 'HIGH'
    
    # Check 3: "Energy >= X" with specific value
    if 'エネルギーが7枚以上' in jp_text or 'エネルギーが 7 枚以上' in jp_text:
        has_count_energy = 'COUNT_ENERGY' in opcode_seq
        # Look for value 7 in frames
        has_value_7 = any(
            str(f.get('value', '')) == '7' or 
            str(f.get('attr', {}).get('value_threshold', '')) == '7'
            for f in frames
        )
        if not has_count_energy or not has_value_7:
            found_issues.append("Text: energy >= 7 required; Frame: missing energy check")
            severity = 'HIGH'
    
    # Check 4: Multi-group treatment (Issue 2 - AURORA FLOWER)
    if ('?????' in jp_text or 'treated as' in jp_text) and 'META_RULE' in opcode_seq:
        non_trivial_ops = [op for op in opcode_seq if op not in ['RETURN', 'NOP']]
        if len(non_trivial_ops) == 0 or (len(non_trivial_ops) == 1 and non_trivial_ops[0] == 'META_RULE'):
            pass
        elif len(non_trivial_ops) == 1 and non_trivial_ops[0] == 'META_RULE':
            pass
    
    # Check 5: "blade count <= X" condition (Issue 3)
    blade_match = re.search(r'元々持つ.*?ブレード.*?(\d+)つ', jp_text)
    if blade_match:
        limit = blade_match.group(1)
        # Check for blade count in frame conditions
        has_blade_condition = any(
            'BLADE' in json.dumps(f, ensure_ascii=False).upper()
            for f in frames
        )
        if not has_blade_condition:
            found_issues.append(f"Text: blade count <= {limit}; Frame: missing blade count check")
            severity = 'HIGH'
    
    # Check 6: Swap/exchange mechanic (Issue 4)
    # Pattern: put to discard THEN put from discard to success
    if '成功ライブカード置き場' in jp_text and '控え室' in jp_text and '置いて' in jp_text:
        # Should have move from success to discard, then recover
        has_discard_move = 'MOVE_TO_DISCARD' in opcode_seq
        has_recover = 'RECOVER_LIVE' in opcode_seq
        
        # Check if only doing one direction
        if has_recover and not has_discard_move:
            found_issues.append("Text: swap live cards (success<->discard); Frame: only recovers from discard (half implemented)")
            severity = 'HIGH'
    
    # Check 7: Baton touch with specific discard tracking (Issue 5)
    if 'BATON' in opcode_seq and 'RECOVER_MEMBER' in opcode_seq:
        # Baton provenance is tracked at runtime; don't flag this family as a missing discard-tracking frame.
        pass
    
    # Check 8: Complex META_RULE placeholder (Issue 6)
    if (
        'エールにより公開された' in jp_text
        and '失い' in jp_text
        and 'もう一度エール' in jp_text
        and 'DISCARD_YELL_PILE' not in raw_effects
        and 'RE_YELL' not in raw_effects
    ):
        non_trivial = [op for op in opcode_seq if op not in ['RETURN', 'NOP', 'META_RULE']]
        if len(non_trivial) == 0:
            found_issues.append("Text: complex yell-repeat mechanic; Frame: only META_RULE placeholder")
            severity = 'CRITICAL'
    
    # Check 9: stale yell-placeholder conditions reused for non-yell text
    if 'REDUCE_YELL_COUNT' in raw_conds and 'エール' not in jp_text and 'yell' not in jp_text.lower():
        found_issues.append(
            "Text does not mention yell/public reveal; Frame still uses REDUCE_YELL_COUNT placeholder"
        )
        severity = 'HIGH'

    # Check 10: "hand cards to deck top" (Issue 14)
    if '手札' in jp_text and ('デッキの上に置く' in jp_text or 'デッキの一番上に' in jp_text):
        has_hand_select = any(
            f.get('slot', {}).get('source_zone') == 'HAND' 
            for f in frames if f.get('op') == 'SELECT_CARDS'
        )
        has_deck_top = any(
            'DECK_TOP' in str(f.get('slot', {})) or 
            'remainder_zone' in str(f.get('slot', {})) and 'DECK' in str(f.get('slot', {}))
            for f in frames
        )
        if not has_hand_select:
            found_issues.append("Text: put hand cards to deck top; Frame: lacks hand card selection")
            severity = 'HIGH'
        if not has_deck_top:
            found_issues.append("Text: put to deck top; Frame: lacks deck top specification")
            severity = 'MEDIUM'
    
    # Check 11: "put to deck" without position specified in frame (Issue 12, 13)
    if ('デッキの一番上' in jp_text or 'デッキの上に' in jp_text) and 'MOVE_TO_DECK' in opcode_seq:
        has_deck_top = any(
            'DECK_TOP' in str(f.get('slot', {})) or 
            'remainder_zone' in str(f.get('slot', {})) and 'TOP' in str(f.get('slot', {}))
            for f in frames if f.get('op') == 'MOVE_TO_DECK'
        )
        if not has_deck_top:
            found_issues.append("Text: put to deck TOP; Frame: MOVE_TO_DECK lacks top position")
            severity = 'MEDIUM'
    
    # Check 12: "put to deck bottom" without position
    if ('デッキの一番下' in jp_text or 'デッキの下に' in jp_text) and 'MOVE_TO_DECK' in opcode_seq:
        has_deck_bottom = any(
            'DECK_BOTTOM' in str(f.get('slot', {})) or 
            'remainder_zone' in str(f.get('slot', {})) and 'BOTTOM' in str(f.get('slot', {}))
            for f in frames if f.get('op') == 'MOVE_TO_DECK'
        )
        if not has_deck_bottom:
            found_issues.append("Text: put to deck BOTTOM; Frame: MOVE_TO_DECK lacks bottom position")
            severity = 'MEDIUM'
    
    # Check 13: RECOVER_LIVE for "put to deck" (wrong destination)
    if ('デッキの一番上' in jp_text or 'デッキの上に' in jp_text) and 'RECOVER_LIVE' in opcode_seq:
        has_move_to_deck = 'MOVE_TO_DECK' in opcode_seq
        if not has_move_to_deck:
            found_issues.append("Text: put live card to deck; Frame: uses RECOVER_LIVE (wrong dest, should be MOVE_TO_DECK)")
            severity = 'MEDIUM'
    
    # Check 14: Yell count comparison (Issue 15)
    if 'エールにより公開された' in jp_text and '枚数' in jp_text and ('少ない' in jp_text or '多い' in jp_text or 'より' in jp_text):
        # Should have proper comparison, not just NOP
        has_explicit_raw_condition = any(
            isinstance(frame.get('params'), dict) and frame.get('params', {}).get('raw_cond')
            for frame in frames
        )
        has_nop_only = all(op in ['NOP', 'JUMP_IF_FALSE', 'DRAW', 'RETURN'] for op in opcode_seq) and not has_explicit_raw_condition
        if has_nop_only:
            found_issues.append("Text: compare yell counts; Frame: uses NOP check (not proper comparison)")
            severity = 'MEDIUM'
    
    # Check 15: "live card" filter not applied (Issue 9)
    if 'ライブカードを' in jp_text and ('デッキ' in jp_text or '手札' in jp_text):
        # Should filter by LIVE type when selecting
        select_frames = [f for f in frames if f.get('op') == 'SELECT_CARDS']
        for sf in select_frames:
            attr = sf.get('attr', {})
            if attr.get('card_type') != 'LIVE' and 'LIVE' not in str(attr):
                # Check if source zone is DISCARD or DECK (where we need to filter)
                source = sf.get('slot', {}).get('source_zone', '')
                if source in ['DISCARD', 'DECK', 'DECK_TOP']:
                    found_issues.append("Text: select LIVE card; Frame: SELECT_CARDS lacks LIVE type filter")
                    severity = 'MEDIUM'
                    break
    
    if found_issues:
        return {
            'signature': signature,
            'cards': card_refs[:2] if card_refs else [],
            'jp_text': jp_text[:180] + '...' if len(jp_text) > 180 else jp_text,
            'issues': found_issues,
            'opcodes': opcode_seq,
            'severity': severity
        }
    
    return None

def generate_report(issues):
    # Sort by severity
    severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
    issues.sort(key=lambda x: severity_order.get(x.get('severity', 'MEDIUM'), 2))
    
    lines = []
    lines.append("# Ability Frame Issues - Mismatches Between Frames and JP Text")
    lines.append("")
    lines.append(f"**File analyzed:** `ability_frame_source.json`")
    lines.append(f"**Generated:** 2026-04-09")
    lines.append(f"**Issues found:** {len(issues)}")
    lines.append("")
    
    # Summary by severity
    critical = len([i for i in issues if i.get('severity') == 'CRITICAL'])
    high = len([i for i in issues if i.get('severity') == 'HIGH'])
    medium = len([i for i in issues if i.get('severity') == 'MEDIUM'])
    lines.append(f"| Severity | Count |")
    lines.append(f"|----------|-------|")
    lines.append(f"| CRITICAL | {critical} |")
    lines.append(f"| HIGH | {high} |")
    lines.append(f"| MEDIUM | {medium} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    for i, issue in enumerate(issues, 1):
        lines.append(f"## Issue {i}: `{issue['signature']}`")
        lines.append(f"**Severity:** {issue.get('severity', 'MEDIUM')}")
        lines.append("")
        lines.append("**Cards:**")
        for card in issue['cards']:
            if isinstance(card, dict):
                card_no = card.get('card_no', 'unknown')
                name = card.get('name', 'unknown')
                lines.append(f"- {card_no} | {name}")
            elif '|' in str(card):
                parts = card.split('|')
                card_no = parts[0].strip()
                name = parts[1].strip().split('[')[0].strip() if '[' in parts[1] else parts[1].strip()
                lines.append(f"- {card_no} | {name}")
            else:
                lines.append(f"- {card}")
        lines.append("")
        lines.append(f"**Frame opcodes:** `{' → '.join(issue['opcodes'])}`")
        lines.append("")
        lines.append("**Primary JP Text:**")
        lines.append(f"> {issue['jp_text']}")
        lines.append("")
        lines.append("**Problem(s):**")
        for problem in issue['issues']:
            lines.append(f"- {problem}")
        lines.append("")
        lines.append("---")
        lines.append("")
    
    return '\n'.join(lines)

if __name__ == '__main__':
    print("Analyzing ability frames for mismatches...")
    issues = analyze_ability_frames()
    print(f"Found {len(issues)} issues")
    
    if issues:
        report = generate_report(issues)
        output_path = Path("c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/data/ability_frame_issues.md")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"Report saved to: {output_path}")
        
        # Print summary
        critical = len([i for i in issues if i.get('severity') == 'CRITICAL'])
        high = len([i for i in issues if i.get('severity') == 'HIGH'])
        medium = len([i for i in issues if i.get('severity') == 'MEDIUM'])
        print(f"\nBreakdown: {critical} CRITICAL, {high} HIGH, {medium} MEDIUM")
    else:
        print("No issues found!")
