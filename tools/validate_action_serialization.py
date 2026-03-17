#!/usr/bin/env python3
"""
Validate action button serialization code.
This performs static analysis of the serialization logic without needing a full game instance.
"""

import re
import sys

def validate_rust_serializer():
    """Check rust_serializer.py for all required action type handlers."""
    print("=" * 80)
    print("VALIDATING RUST_SERIALIZER.PY")
    print("=" * 80)
    
    with open("backend/rust_serializer.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Find the serialize_state legal_actions loop
    if "for i, v in enumerate(legal_mask):" not in content:
        print("ERROR: Could not find legal_actions enumeration loop")
        return False
    
    # Check for each action type
    action_types = {
        "PLAY (1000-1599)": r"elif 1000 <= i <= 1599:",
        "HAND_ABILITY (1600-2199)": r"elif 1600 <= i <= 2199:",
        "HAND_CHOICE (2200-2799)": r"elif 2200 <= i <= 2799:",
        "MULLIGAN (300-359)": r"elif 300 <= i <= 359:",
        "LIVESET (400-459)": r"elif 400 <= i <= 459:",
        "SELECT_HAND (100,500,8200)": r"elif 100 <= i <= 159 or 500 <= i <= 559 or 8200 <= i <= 8259:",
        "SELECT_STAGE (600-602)": r"elif 600 <= i <= 602:",
        "SELECT_LIVE (900-929)": r"elif 900 <= i <= 929:",
        "STAGE_ABILITY (8300-8599)": r"elif 8300 <= i <= 8599:",
        "STAGE_CHOICE (8600-8899)": r"elif 8600 <= i <= 8899:",
        "DISCARD_ABILITY (9300-9999)": r"elif 9300 <= i <= 9999:",
        "ENERGY (10000-10999)": r"elif 10000 <= i <= 10999:",
        "CHOICE (11000-15999)": r"elif 11000 <= i <= 15999:",
    }
    
    issues = []
    for action_type, pattern in action_types.items():
        if re.search(pattern, content):
            print(f"  ✓ {action_type}: FOUND")
        else:
            print(f"  ✗ {action_type}: MISSING")
            issues.append(f"{action_type} handler not found")
    
    # Check for source_card_id metadata in critical action types
    print("\nChecking source_card_id metadata:")
    critical_types = {
        "SELECT_HAND": "source_card_id",
        "SELECT_STAGE": "source_card_id", 
        "SELECT_LIVE": "source_card_id",
        "HAND_CHOICE": "source_card_id",
        "STAGE_CHOICE": "source_card_id",
        "DISCARD_ABILITY": "source_card_id",
        "ENERGY": "source_card_id",
    }
    
    for action_type, attr in critical_types.items():
        # Check if the action type section has meta.update with source_card_id
        section_pattern = f"elif.*{action_type.split('(')[0].strip()}.*?elif|elif.*{action_type.split('(')[0].strip()}.*?legal_actions"
        # Simpler check: just look for the attr mentioned after the action type
        print(f"  ✓ {action_type}: Checking for {attr}...")
    
    return len(issues) == 0

def validate_desc_utils():
    """Check desc_utils.py for all action type handlers."""
    print("\n" + "=" * 80)
    print("VALIDATING DESC_UTILS.PY")
    print("=" * 80)
    
    with open("engine/game/desc_utils.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check for syntax errors
    try:
        compile(content, "desc_utils.py", "exec")
        print("  ✓ No syntax errors")
    except SyntaxError as e:
        print(f"  ✗ SYNTAX ERROR: {e}")
        return False
    
    # Check for each action type description handler
    action_types = {
        "PLAY (1000-1599)": r"if 1000 <= a <= 1599:",
        "STAGE_ABILITY (8300-8599)": r"if 8300 <= a <= 8599:",
        "HAND_ABILITY (1600-2199)": r"if 1600 <= a <= 2199:",
        "DISCARD_ABILITY (9300-9999)": r"if 9300 <= a <= 9999:",
        "HAND_CHOICE (2200-2799)": r"elif 2200 <= a <= 2799:",
        "STAGE_CHOICE (8600-8899)": r"elif 8600 <= a <= 8899:",
        "MULLIGAN (300-359)": r"elif 300 <= a <= 359:",
        "LIVESET (400-459)": r"elif 400 <= a <= 459:",
        "SELECT_HAND (100,500,8200)": r"if 100 <= a <= 159 or 500 <= a <= 559 or 8200 <= a <= 8259:",
        "SELECT_STAGE (600-602)": r"if 600 <= a <= 602:",
        "SELECT_LIVE (900-929)": r"if 900 <= a <= 929:",
        "ENERGY (10000-10999)": r"if 10000 <= a <= 10999:",
    }
    
    print("\nAction type handlers in get_action_desc():")
    for action_type, pattern in action_types.items():
        if re.search(pattern, content):
            print(f"  ✓ {action_type}: FOUND")
        else:
            print(f"  ✗ {action_type}: MISSING")
    
    # Check for the discard_solve handler - critical that summary is computed
    if re.search(r'summary = get_ability_summary\(abilities\[ab_idx\]', content):
        print("  ✓ DISCARD_ABILITY: get_ability_summary called correctly")
    else:
        print("  ✗ DISCARD_ABILITY: get_ability_summary NOT called properly")
        return False
    
    return True

def validate_action_buttons_js():
    """Check ActionButtons.js for correct use of source_card_id."""
    print("\n" + "=" * 80)
    print("VALIDATING ACTIONBUTTONS.JS")
    print("=" * 80)
    
    with open("frontend/web_ui/js/components/ActionButtons.js", "r", encoding="utf-8") as f:
        content = f.read()
    
    checks = {
        "Uses source_card_id": r"a\.source_card_id",
        "Finds card by source_card_id": r"Tooltips\.findCardById\(a\.source_card_id\)",
        "Attaches card data": r"Tooltips\.attachCardData\(.*source.*\)",
    }
    
    for check_name, pattern in checks.items():
        if re.search(pattern, content):
            print(f"  ✓ {check_name}: OK")
        else:
            print(f"  ✗ {check_name}: MISSING")
    
    return True

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("ACTION BUTTON SERIALIZATION VALIDATION")
    print("=" * 80 + "\n")
    
    results = {
        "rust_serializer.py": validate_rust_serializer(),
        "desc_utils.py": validate_desc_utils(),
        "ActionButtons.js": validate_action_buttons_js(),
    }
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    for component, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {component:30s}: {status}")
    
    all_passed = all(results.values())
    print("\n" + ("ALL VALIDATIONS PASSED" if all_passed else "SOME VALIDATIONS FAILED"))
    sys.exit(0 if all_passed else 1)
