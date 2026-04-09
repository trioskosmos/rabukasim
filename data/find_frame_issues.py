#!/usr/bin/env python3
"""Analyze ability_frame_source.json to find mismatches between frames and JP text."""

import json
import re
from pathlib import Path

def analyze_ability_frames():
    filepath = Path("c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/data/ability_frame_source.json")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    signature_groups = data.get('signature_groups', [])
    
    issues = []
    
    for group in signature_groups:
        signature = group.get('signature', '')
        primary_jp = group.get('primary_text_jp', '')
        frames = group.get('frames', [])
        opcode_seq = group.get('opcode_sequence', [])
        cards = group.get('cards', [])
        
        # Skip empty or trivial frames
        if len(frames) <= 1:  # Just RETURN
            continue
            
        issue = analyze_group(signature, primary_jp, frames, opcode_seq, cards)
        if issue:
            issues.append(issue)
    
    return issues

def analyze_group(signature, jp_text, frames, opcode_seq, cards):
    """Analyze a single signature group for mismatches."""
    
    # Skip empty text
    if not jp_text:
        return None
    
    # Extract key elements from Japanese text
    text_patterns = {
        'discard_to_draw': r'手札を(\d+)枚まで控え室に置いてもよい.*引く',
        'discard_to_blades': r'手札を(\d+)枚まで控え室に置いてもよい.*ブレード',
        'live_to_deck_bottom': r'ライブカードを\d+枚までデッキの一番下',
        'any_to_deck_top': r'カードを\d+枚までデッキの一番上',
        'energy_count_check': r'エネルギーが(\d+)枚以上',
        'blade_count_check': r'ブレード.*(\d+)つ以下',
        'recover_live': r'ライブカードを\d+枚.*成功ライブ',
        'hand_to_deck_top': r'手札を\d+枚.*デッキの上に置く',
        'meta_rule_placeholder': r'すべての領域にあるこのカードは',
        'yell_compare': r'エールにより公開された.*枚数',
    }
    
    found_issues = []
    
    # Check for discard -> draw mechanics
    discard_draw_match = re.search(text_patterns['discard_to_draw'], jp_text)
    if discard_draw_match:
        count = int(discard_draw_match.group(1))
        # Check if frame has proper discard then draw sequence
        has_discard = 'MOVE_TO_DISCARD' in opcode_seq
        has_draw = 'DRAW' in opcode_seq
        if has_draw and not has_discard:
            found_issues.append(f"Text says 'discard up to {count}, draw same' but frame only does DRAW without discard")
        elif not has_discard and not has_draw:
            found_issues.append(f"Text describes discard-draw mechanic but frame lacks both")
    
    # Check for energy count conditions
    energy_match = re.search(text_patterns['energy_count_check'], jp_text)
    if energy_match:
        required = int(energy_match.group(1))
        has_energy_check = 'COUNT_ENERGY' in opcode_seq
        if not has_energy_check:
            found_issues.append(f"Text requires energy >= {required} but frame lacks COUNT_ENERGY check")
    
    # Check for blade count conditions
    blade_match = re.search(text_patterns['blade_count_check'], jp_text)
    if blade_match:
        limit = int(blade_match.group(1))
        has_blade_check = any('BLADE' in str(f.get('attr', {})) for f in frames)
        if not has_blade_check:
            found_issues.append(f"Text requires blade count <= {limit} but frame lacks blade check")
    
    # Check for "put live card to deck bottom" vs generic MOVE_TO_DECK
    if re.search(text_patterns['live_to_deck_bottom'], jp_text):
        # Check if frame has proper card_type filter
        has_live_filter = any(
            f.get('attr', {}).get('card_type') == 'LIVE' 
            for f in frames if f.get('op') in ['SELECT_CARDS', 'MOVE_TO_DECK']
        )
        has_deck_bottom = any(
            'DECK_BOTTOM' in str(f.get('slot', {})) 
            for f in frames
        )
        if not has_live_filter:
            found_issues.append("Text says 'put LIVE card to deck bottom' but frame lacks LIVE type filter")
        if not has_deck_bottom:
            found_issues.append("Text specifies 'deck bottom' but frame lacks DECK_BOTTOM specification")
    
    # Check for "put any card to deck top"
    if re.search(text_patterns['any_to_deck_top'], jp_text):
        has_deck_top = any(
            'DECK_TOP' in str(f.get('slot', {})) 
            for f in frames
        )
        if not has_deck_top:
            found_issues.append("Text specifies 'deck top' but frame lacks DECK_TOP specification")
    
    # Check for meta-rule placeholder (cards treated as multiple groups)
    if re.search(text_patterns['meta_rule_placeholder'], jp_text):
        has_meta = 'META_RULE' in opcode_seq
        has_actual_impl = len([op for op in opcode_seq if op not in ['NOP', 'RETURN', 'META_RULE']]) > 0
        if has_meta and not has_actual_impl:
            found_issues.append("Text describes multi-group treatment but frame only has META_RULE placeholder")
    
    # Check for yell comparison
    if re.search(text_patterns['yell_compare'], jp_text):
        # Should have proper comparison logic, not just NOP
        has_nop_only = all(op in ['NOP', 'JUMP_IF_FALSE', 'DRAW', 'RETURN'] for op in opcode_seq)
        if has_nop_only:
            found_issues.append("Text compares yell counts but frame uses NOP check instead of actual comparison")
    
    # Check for "hand to deck top" (putting hand cards on deck)
    if re.search(text_patterns['hand_to_deck_top'], jp_text):
        has_hand_select = any(
            f.get('slot', {}).get('source_zone') == 'HAND' 
            for f in frames if f.get('op') == 'SELECT_CARDS'
        )
        has_deck_top = any(
            'DECK_TOP' in str(f.get('slot', {})) 
            for f in frames
        )
        if not has_hand_select:
            found_issues.append("Text says 'put hand cards to deck top' but frame lacks hand selection")
        if not has_deck_top:
            found_issues.append("Text specifies 'deck top' but frame lacks DECK_TOP specification")
    
    # Check for recover_live from discard
    if re.search(text_patterns['recover_live'], jp_text):
        # Should use MOVE_TO_DECK_TOP, not RECOVER_LIVE
        has_recover = 'RECOVER_LIVE' in opcode_seq
        has_move_to_deck = 'MOVE_TO_DECK' in opcode_seq
        if has_recover and not has_move_to_deck:
            found_issues.append("Text says 'put to deck' but frame uses RECOVER_LIVE (wrong destination)")
    
    if found_issues:
        return {
            'signature': signature,
            'cards': cards[:3] if cards else [],  # First 3 cards as examples
            'jp_text': jp_text[:200] + '...' if len(jp_text) > 200 else jp_text,
            'issues': found_issues,
            'opcodes': opcode_seq
        }
    
    return None

def generate_report(issues):
    lines = []
    lines.append("# Ability Frame Issues - Mismatches Between Frames and JP Text")
    lines.append("")
    lines.append(f"**File analyzed:** `ability_frame_source.json`")
    lines.append(f"**Generated:** 2026-04-09")
    lines.append(f"**Issues found:** {len(issues)}")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    for i, issue in enumerate(issues, 1):
        lines.append(f"## Issue {i}: {issue['signature']}")
        lines.append("")
        lines.append("**Cards:**")
        for card in issue['cards']:
            card_name = card.split('|')[1].strip() if '|' in card else card
            lines.append(f"- {card_name}")
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
    print("Analyzing ability frames...")
    issues = analyze_ability_frames()
    print(f"Found {len(issues)} issues")
    
    if issues:
        report = generate_report(issues)
        output_path = Path("c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/data/ability_frame_issues.md")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"Report saved to: {output_path}")
    else:
        print("No issues found!")
