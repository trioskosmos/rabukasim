#!/usr/bin/env python
"""
Pseudocode Validator Tool

This tool validates pseudocode entries in manual_pseudocode.json and cards.json
to detect common issues that can cause infinite loops or runtime errors.

Checks performed:
1. Missing TRIGGER: for abilities with effects
2. ACTIVATED/ON_ACTIVATE abilities without COST:
3. CHEER_REVEAL effects without proper handling
4. Unknown trigger types
5. Abilities with no effects
"""

import json
import re
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

VALID_TRIGGERS = {
    "ON_PLAY",
    "ON_LIVE_START",
    "ON_LIVE_SUCCESS",
    "TURN_START",
    "TURN_END",
    "CONSTANT",
    "ACTIVATED",
    "ON_ACTIVATE",
    "ON_LEAVES",
    "ON_REVEAL",
    "ON_POSITION_CHANGE",
    "ON_MEMBER_DISCARD",
    "ON_OPPONENT_TAP",
    "ON_YELL",
    "ON_YELL_SUCCESS",
    "ON_YELL_REVEAL",
    "ON_OPPONENT_YELL",
    "ON_DISCARD",
    "ON_STAGE_ENTRY",
    "ON_REMOVE",
    "ON_ACTIVATE_FROM_DISCARD",
    "ACTIVATED_FROM_DISCARD",
    "ON_MOVE_TO_DISCARD",
    "ON_ENERGY_CHARGE",
    "ON_MEMBER_PLAYED",
    "ON_MEMBER_TAP",
    "ON_SELF_TAPPED",
    "ON_RECOVERED_FROM_DISCARD",
    "ON_SET_TO_LIVE_PLAY",
    "ON_PLACE_ENERGY_BY_EFFECT",
    "ON_ABILITY_RESOLVE",
}

VALID_EFFECTS = {
    "DRAW",
    "ADD_BLADES",
    "ADD_HEARTS",
    "REDUCE_COST",
    "LOOK_DECK",
    "RECOVER_LIVE",
    "BOOST_SCORE",
    "RECOVER_MEMBER",
    "BUFF_POWER",
    "IMMUNITY",
    "TAP_MEMBER",
    "TAP_OPPONENT",
    "ACTIVATE_MEMBER",
    "ACTIVATE_ENERGY",
    "DISCARD_HAND",
    "MOVE_TO_DECK",
    "MOVE_TO_DISCARD",
    "LOOK_AND_CHOOSE",
    "LOOK_AND_CHOOSE_REVEAL",
    "LOOK_AND_CHOOSE_ORDER",
    "SELECT_MODE",
    "COLOR_SELECT",
    "CHEER_REVEAL",
    "REVEAL_UNTIL",
    "PLAY_MEMBER",
    "PLAY_MEMBER_FROM_DISCARD",
    "PLAY_LIVE_FROM_DISCARD",
    "SWAP_CARDS",
    "PREVENT_ACTIVATE",
    "REVEAL_HAND",
    "REVEAL_CARDS",
    "SELECT_MEMBER",
    "SELECT_REVEALED",
    "REDUCE_HEART",
    "INCREASE_COST",
    "MOVE_MEMBER",
    "ORDER_DECK",
    "PREVENT_LIVE",
    "TAP_PLAYER",
    "ACTIVATE_SELF",
    "SWAP_AREA",
}

VALID_COSTS = {
    "TAP_SELF",
    "DISCARD_HAND",
    "PAY_ENERGY",
    "REMOVE_SELF",
    "TAP_MEMBER",
    "TAP_PLAYER",
    "REVEAL_HAND",
    "MOVE_TO_DECK",
    "PAY_HEART",
    "DISCARD_ENERGY",
}


class PseudocodeIssue:
    def __init__(self, card_no: str, issue_type: str, message: str, line_content: str = "", severity: str = "WARNING"):
        self.card_no = card_no
        self.issue_type = issue_type
        self.message = message
        self.line_content = line_content
        self.severity = severity

    def __str__(self):
        line_info = f" (Line: '{self.line_content}')" if self.line_content else ""
        return f"[{self.severity}] {self.card_no}: {self.issue_type} - {self.message}{line_info}"


def validate_pseudocode(card_no: str, pseudocode: str) -> list:
    """Validate a single pseudocode entry and return list of issues."""
    issues = []

    if not pseudocode or not pseudocode.strip():
        return issues

    # Handle escaped newlines
    pseudocode = pseudocode.replace("\\n", "\n")
    lines = pseudocode.strip().split("\n")

    # Track state
    current_trigger = None
    has_cost = False
    has_effect = False

    def check_previous_ability():
        nonlocal current_trigger, has_cost, has_effect
        if current_trigger:
            if not has_effect:
                issues.append(
                    PseudocodeIssue(card_no, "NO_EFFECT", f"Trigger '{current_trigger}' has no EFFECT:", "", "WARNING")
                )
            if current_trigger in ("ACTIVATED", "ON_ACTIVATE") and not has_cost:
                issues.append(
                    PseudocodeIssue(
                        card_no,
                        "ACTIVATED_NO_COST",
                        "ACTIVATED ability has no COST: - will cause infinite loop!",
                        "",
                        "ERROR",
                    )
                )

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.upper().startswith("TRIGGER:"):
            check_previous_ability()

            trigger_text = line[8:].strip()
            # Remove modifiers in parentheses
            trigger_text = re.sub(r"\s*\([^)]*\)\s*", " ", trigger_text).strip()
            # Remove parameters in curly braces
            trigger_text = re.sub(r"\{[^{}]*\}", " ", trigger_text).strip()

            # Split by possible combined triggers (comma or semicolon)
            split_triggers = [t.strip() for t in re.split(r",|;", trigger_text) if t.strip()]

            # Clean up redundant "TRIGGER:" prefix in split parts if any
            split_triggers = [re.sub(r"^TRIGGER:\s*", "", t, flags=re.IGNORECASE).strip() for t in split_triggers]

            for t in split_triggers:
                if t.upper() not in VALID_TRIGGERS:
                    issues.append(
                        PseudocodeIssue(
                            card_no, "INVALID_TRIGGER", f"Unknown trigger type: '{t}'", line, "ERROR"
                        )
                    )
            
            if split_triggers:
                current_trigger = split_triggers[0].upper()
            has_cost = False
            has_effect = False

        elif line.upper().startswith("COST:"):
            has_cost = True

        elif line.upper().startswith("EFFECT:"):
            has_effect = True
            if "CHEER_REVEAL" in line.upper():
                if current_trigger in ("ACTIVATED", "ON_ACTIVATE") and not has_cost:
                    issues.append(
                        PseudocodeIssue(
                            card_no,
                            "CHEER_REVEAL_LOOP",
                            "CHEER_REVEAL in ACTIVATED ability without cost!",
                            line,
                            "ERROR",
                        )
                    )

        elif line.upper().startswith("CONDITION:") or line.upper().startswith("OPTION:"):
            pass

        elif not line.startswith("#"):
            # Orphan effect check
            first_word = line.split("(")[0].split(" ")[0].split("{")[0].strip().upper()
            if first_word in VALID_EFFECTS:
                if current_trigger is None:
                    issues.append(
                        PseudocodeIssue(
                            card_no, "EFFECT_WITHOUT_TRIGGER", "Effect found before any TRIGGER:", line, "ERROR"
                        )
                    )

    check_previous_ability()
    return issues

    return issues


def validate_manual_pseudocode(filepath: str) -> list:
    """Validate all entries in manual_pseudocode.json"""
    issues = []

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    for card_no, entry in data.items():
        pseudocode = entry.get("pseudocode", "")
        card_issues = validate_pseudocode(card_no, pseudocode)
        issues.extend(card_issues)

    return issues


def validate_cards_json(filepath: str) -> list:
    """Validate all pseudocode entries in cards.json"""
    issues = []

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    for card_no, card_data in data.items():
        if isinstance(card_data, dict):
            pseudocode = card_data.get("pseudocode", "")
            card_issues = validate_pseudocode(card_no, pseudocode)
            issues.extend(card_issues)

    return issues


def main():
    data_dir = PROJECT_ROOT / "data"
    manual_path = data_dir / "manual_pseudocode.json"
    cards_path = data_dir / "cards.json"

    all_issues = []

    # Validate manual_pseudocode.json
    if manual_path.exists():
        manual_issues = validate_manual_pseudocode(str(manual_path))
        all_issues.extend(manual_issues)

    # Validate cards.json
    if cards_path.exists():
        cards_issues = validate_cards_json(str(cards_path))
        all_issues.extend(cards_issues)

    # Filter for Errors
    errors = [i for i in all_issues if i.severity == "ERROR"]

    with open("validate_report.txt", "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write("Pseudocode Validator Report\n")
        f.write("=" * 60 + "\n")

        if errors:
            f.write(f"\nFOUND {len(errors)} ERRORS:\n")
            for issue in errors:
                f.write(f"  {issue}\n")
        else:
            f.write("\nNO ERRORS FOUND\n")

    print(f"Validation complete. Found {len(errors)} errors. Report saved to validate_report.txt")
    return len(errors)

    return len(errors)


if __name__ == "__main__":
    sys.exit(main())
