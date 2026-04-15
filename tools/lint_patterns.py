#!/usr/bin/env python3
"""Lint DSL patterns to find inconsistencies and issues."""

import ast
import re
from pathlib import Path
from collections import defaultdict

def extract_patterns_from_file(filepath: Path) -> list[dict]:
    """Extract DSL_PATTERNS list from Python file using regex."""
    content = filepath.read_text(encoding='utf-8')
    
    # Find DSL_PATTERNS = [...]
    match = re.search(r'DSL_PATTERNS\s*=\s*\[(.*?)\n    \]', content, re.DOTALL)
    if not match:
        print("Could not find DSL_PATTERNS")
        return []
    
    # Extract individual pattern dicts
    pattern_texts = re.findall(r'\{\s*"name":\s*"([^"]+)".*?\},', match.group(1), re.DOTALL)
    
    patterns = []
    for name in pattern_texts:
        # Find this pattern's full text
        pattern_search = re.search(
            rf'"name":\s*"{re.escape(name)}".*?(\{{.*?\}}),',
            match.group(1),
            re.DOTALL
        )
        if pattern_search:
            p_text = pattern_search.group(1)
            
            # Extract fields
            regex_match = re.search(r'"regex":\s*r"(.*?)"[,\n]', p_text, re.DOTALL)
            template_match = re.search(r'"template":\s*"(.*?)"[,\n]', p_text, re.DOTALL)
            structure_match = re.search(r'"structure":\s*"(.*?)"[,\n]', p_text, re.DOTALL)
            
            patterns.append({
                'name': name,
                'regex': regex_match.group(1) if regex_match else '',
                'template': template_match.group(1) if template_match else '',
                'structure': structure_match.group(1) if structure_match else '',
            })
    
    return patterns


def check_placeholder_consistency(patterns: list[dict]) -> list[str]:
    """Check for inconsistent placeholder naming in placement patterns."""
    issues = []
    
    # Only check simple placement patterns where SOURCE should be used
    for p in patterns:
        template = p['template']
        regex = p['regex']
        
        # Skip patterns with multiple cards (legitimate use of CARD)
        has_multiple_cards = template.count('⟧') > 2
        
        # Only flag single-card placement patterns
        if (not has_multiple_cards and 
            '⟦CARD⟧' in template and 
            re.search(r'を[^。]*に置く', regex)):
            issues.append(f"{p['name']}: uses ⟦CARD⟧ instead of ⟦SOURCE⟧ for simple placement")
    
    return issues


def find_duplicate_regexes(patterns: list[dict]) -> list[str]:
    """Find patterns with identical regexes."""
    issues = []
    regex_to_names = defaultdict(list)
    
    for p in patterns:
        regex_to_names[p['regex']].append(p['name'])
    
    for regex, names in regex_to_names.items():
        if len(names) > 1:
            issues.append(f"Duplicate regex: {names}")
            issues.append(f"  Regex: {regex[:80]}...")
    
    return issues


def check_pattern_order(patterns: list[dict]) -> list[str]:
    """Check if specific patterns come before generic fallbacks."""
    issues = []
    
    # Look for "place" patterns - specific ones should come before generic
    place_patterns = [(i, p) for i, p in enumerate(patterns) if 'place' in p['name']]
    
    generic_idx = None
    for i, p in place_patterns:
        if p['name'] == 'place_to_zone':
            generic_idx = i
            break
    
    if generic_idx:
        for i, p in place_patterns:
            if i > generic_idx and p['name'] not in ['place_to_zone', 'place_count_fragment', 'place_specific_zone_fragment']:
                if 'デッキ' in p['regex'] or '手札' in p['regex'] or 'ステージ' in p['regex'] or '控え室' in p['regex']:
                    issues.append(f"{p['name']} (line ~{i}) should come BEFORE place_to_zone (generic)")
    
    # Check "per" patterns - specific per_* should come before generic per_unit
    per_patterns = [(i, p) for i, p in enumerate(patterns) if p['name'].startswith('per_')]
    per_unit_idx = None
    for i, p in per_patterns:
        if p['name'] == 'per_unit':
            per_unit_idx = i
            break
    
    if per_unit_idx:
        for i, p in per_patterns:
            if i > per_unit_idx and p['name'] != 'per_unit':
                issues.append(f"{p['name']} (line ~{i}) should come BEFORE per_unit (generic)")
    
    return issues


def check_broken_regexes(patterns: list[dict]) -> list[str]:
    """Check for broken/incomplete regexes."""
    issues = []
    
    for p in patterns:
        regex = p['regex']
        # Check for unbalanced braces in regex
        open_braces = regex.count('{')
        close_braces = regex.count('}')
        
        # For icon patterns, check specifically
        if 'atomic_icon' in p['name'] or '{{' in regex:
            if open_braces != close_braces:
                issues.append(f"{p['name']}: Unbalanced braces - open:{open_braces} close:{close_braces}")
                issues.append(f"  Regex: {regex}")
    
    return issues


def check_unused_placeholders(patterns: list[dict]) -> list[str]:
    """Check if placeholders in template match capture groups in regex."""
    issues = []
    
    # Patterns that are intentionally non-matching
    skip_patterns = {
        # Atomic patterns - literal replacements
        'atomic_duration_permanent', 'atomic_duration_end_live', 'atomic_duration_end_turn',
        'atomic_optional', 'atomic_to_deck_top', 'atomic_to_deck_bottom', 'atomic_to_hand',
        'atomic_to_discard', 'atomic_state_wait', 'atomic_state_activate',
        'atomic_from_deck_top', 'atomic_from_hand', 'atomic_from_discard',
        'atomic_reveal_card', 'atomic_from_energy_deck', 'atomic_move_member',
        # Catch-all patterns use .* which has no capture groups but needs placeholder
        'catchall_parenthetical', 'catchall_repeat', 'catchall_score', 'catchall_choice',
        'catchall_parenthetical_opponent', 'catchall_parenthetical_card',
        'catchall_repeat_procedure', 'catchall_score_zero', 'catchall_any',
        # Icon patterns
        'atomic_icon', 'atomic_zone', 'atomic_area',
        'icon_embedded_choose', 'icon_embedded_cost_effect',
        # Complex patterns with intentional non-matching
        'complex_cost_calculation', 'choice_turn_specific',
    }
    
    for p in patterns:
        if p['name'] in skip_patterns:
            continue
            
        regex = p['regex']
        template = p['template']
        
        # Count capture groups (excluding non-capturing groups)
        capture_groups = len(re.findall(r'\((?:\?[^)]*)?[^)]+\)', regex))
        # Count placeholders
        placeholders = len(re.findall(r'⟦[^⟧]+⟧', template))
        
        # These should generally match
        if capture_groups > 0 and placeholders == 0:
            issues.append(f"{p['name']}: Has {capture_groups} capture groups but no placeholders")
        elif capture_groups > 0 and placeholders != capture_groups:
            issues.append(f"{p['name']}: Has {capture_groups} capture groups but {placeholders} placeholders")
    
    return issues


def main():
    filepath = Path(__file__).parent / "extract_abilities_to_template.py"
    
    print("=" * 70)
    print("PATTERN LINTER - extract_abilities_to_template.py")
    print("=" * 70)
    
    patterns = extract_patterns_from_file(filepath)
    print(f"\nFound {len(patterns)} patterns\n")
    
    all_issues = []
    
    # Check 1: Broken regexes
    print("\n[1] BROKEN REGEXES (unbalanced braces)")
    print("-" * 50)
    issues = check_broken_regexes(patterns)
    if issues:
        for i in issues:
            print(f"  ! {i}")
        all_issues.extend(issues)
    else:
        print("  ✓ No broken regexes found")
    
    # Check 2: Duplicate regexes
    print("\n[2] DUPLICATE REGEXES")
    print("-" * 50)
    issues = find_duplicate_regexes(patterns)
    if issues:
        for i in issues:
            print(f"  ! {i}")
        all_issues.extend(issues)
    else:
        print("  ✓ No duplicates found")
    
    # Check 3: Ordering issues
    print("\n[3] PATTERN ORDERING (specific should come before generic)")
    print("-" * 50)
    issues = check_pattern_order(patterns)
    if issues:
        for i in issues:
            print(f"  ! {i}")
        all_issues.extend(issues)
    else:
        print("  ✓ Ordering looks correct")
    
    # Check 4: Placeholder consistency
    print("\n[4] PLACEHOLDER CONSISTENCY")
    print("-" * 50)
    issues = check_placeholder_consistency(patterns)
    if issues:
        for i in issues:
            print(f"  ! {i}")
        all_issues.extend(issues)
    else:
        print("  ✓ Placeholder naming is consistent")
    
    # Check 5: Placeholder/capture group mismatch
    print("\n[5] CAPTURE GROUP vs PLACEHOLDER MISMATCH")
    print("-" * 50)
    issues = check_unused_placeholders(patterns)
    if issues:
        for i in issues:
            print(f"  ! {i}")
        all_issues.extend(issues)
    else:
        print("  ✓ All patterns have matching capture groups and placeholders")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    if all_issues:
        print(f"\nFound {len(all_issues)} issues to fix.")
        print("\nTop fixes to make:")
        print("  1. Move specific patterns before generic fallbacks")
        print("  2. Fix any broken regexes (unbalanced braces)")
        print("  3. Remove duplicate patterns")
        print("  4. Ensure capture groups match placeholders")
    else:
        print("\n✓ All checks passed!")
    print()


if __name__ == "__main__":
    main()
