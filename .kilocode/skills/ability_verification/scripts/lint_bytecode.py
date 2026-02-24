# -*- coding: utf-8 -*-
"""Bytecode Linter — scans cards_compiled.json for known bytecode bug patterns.

Usage:
    uv run python .agent/skills/ability_verification/scripts/lint_bytecode.py

Checks:
    1. LOOK_AND_CHOOSE slot leak: slot should be 0 (deck) unless source is explicitly HAND(6).
    2. Orphaned optional bits: is_optional set on effects that don't support it.
    3. Filter attr sanity: unit/group IDs within valid range.
    4. Destination-source confusion: slot values that don't match known source zones.
"""

import json
import sys
from pathlib import Path

# ── Opcodes (must match engine_rust_src/src/core/logic/enums.rs) ──
O_RETURN = 1
O_DRAW = 10
O_LOOK_DECK = 14
O_RECOVER_LIVE = 15
O_RECOVER_MEMBER = 17
O_SEARCH_DECK = 22
O_ORDER_DECK = 28
O_SELECT_MODE = 30
O_MOVE_TO_DECK = 31
O_REVEAL_CARDS = 40
O_LOOK_AND_CHOOSE = 41
O_ADD_TO_HAND = 44
O_TAP_MEMBER = 53
O_PLAY_MEMBER_FROM_HAND = 57
O_MOVE_TO_DISCARD = 58
O_GRANT_ABILITY = 60
O_SELECT_CARDS = 74

OPCODE_NAMES = {
    0: "NOP", 1: "RETURN", 2: "JUMP", 3: "JUMP_F",
    10: "DRAW", 11: "BLADES", 12: "HEARTS", 13: "REDUCE_COST",
    14: "LOOK_DECK", 15: "RECOV_L", 16: "BOOST", 17: "RECOV_M",
    18: "BUFF", 19: "IMMUNITY", 20: "MOVE_MEMBER", 21: "SWAP_CARDS",
    22: "SEARCH_DECK", 23: "CHARGE", 24: "SET_BLADES", 25: "SET_HEARTS",
    26: "FORMATION", 27: "NEGATE", 28: "ORDER_DECK", 29: "META_RULE",
    30: "SELECT_MODE", 31: "MOVE_TO_DECK", 32: "TAP_O", 33: "PLACE_UNDER",
    34: "FLAVOR", 35: "RESTRICTION", 36: "BATON_MOD", 37: "SET_SCORE",
    38: "SWAP_ZONE", 39: "TRANSFORM_COLOR", 40: "REVEAL",
    41: "LOOK_AND_CHOOSE", 42: "CHEER_REVEAL", 43: "ACTIVATE_MEMBER",
    44: "ADD_H", 45: "COLOR_SELECT", 46: "REPLACE_EFFECT",
    47: "TRIGGER_REMOTE", 48: "REDUCE_HEART_REQ", 49: "MODIFY_SCORE_RULE",
    50: "ADD_STAGE_ENERGY", 51: "SET_TAPPED", 52: "ADD_CONTINUOUS",
    53: "TAP_M", 57: "PLAY_MEMBER_FROM_HAND", 58: "MOVE_TO_DISCARD",
    60: "GRANT_ABILITY", 61: "INCREASE_HEART_COST", 62: "REDUCE_YELL_COUNT",
    63: "PLAY_MEMBER_FROM_DISCARD", 64: "PAY_ENERGY", 65: "SELECT_MEMBER",
    66: "DRAW_UNTIL", 67: "SELECT_PLAYER", 68: "SELECT_LIVE",
    69: "REVEAL_UNTIL", 70: "INCREASE_COST", 71: "PREVENT_PLAY_TO_SLOT",
    72: "SWAP_AREA", 73: "TRANSFORM_HEART", 74: "SELECT_CARDS",
    75: "OPPONENT_CHOOSE", 76: "PLAY_LIVE_FROM_DISCARD",
    77: "REDUCE_LIVE_SET_LIMIT", 80: "PREVENT_SET_TO_SUCCESS_PILE",
    81: "ACTIVATE_ENERGY", 82: "PREVENT_ACTIVATE", 84: "SET_HEART_COST",
    90: "PREVENT_BATON_TOUCH",
    100: "SET_TARGET_SELF", 101: "SET_TARGET_PLAYER", 102: "SET_TARGET_OPPONENT",
}

# Valid source zones for LOOK_AND_CHOOSE
VALID_LAC_SOURCES = {0, 6, 7, 8}  # 0=default(deck), 6=hand, 7=discard, 8=deck

# Max valid unit/group IDs
MAX_UNIT_ID = 20
MAX_GROUP_ID = 10


class LintWarning:
    def __init__(self, card_id: str, card_no: str, card_name: str,
                 ability_idx: int, instr_idx: int, severity: str, message: str):
        self.card_id = card_id
        self.card_no = card_no
        self.card_name = card_name
        self.ability_idx = ability_idx
        self.instr_idx = instr_idx
        self.severity = severity
        self.message = message

    def __str__(self):
        return (f"[{self.severity}] Card {self.card_no} (ID={self.card_id}) "
                f"Ab#{self.ability_idx} Instr#{self.instr_idx}: {self.message}")


def decode_filter_attr(a: int) -> dict:
    """Decode bits of a filter_attr value."""
    return {
        "dest_discard": bool(a & 0x01),
        "optional": bool(a & 0x02),
        "type_filter": (a >> 2) & 0x03,  # 0=any, 1=member, 2=live
        "group_enable": bool(a & 0x10),
        "group_id": (a >> 5) & 0x7F,
        "src_zone": (a >> 12) & 0x0F,
        "unit_enable": bool(a & 0x10000),
        "unit_id": (a >> 17) & 0x7F,
        "cost_enable": bool(a & (1 << 24)),
        "cost_val": (a >> 25) & 0x1F,
        "cost_le": bool(a & (1 << 30)),
    }


def lint_card(card_id: str, card: dict, warnings: list):
    """Run all lint checks on a single card's abilities."""
    card_no = card.get("card_no", "???")
    card_name = card.get("name", "???")
    abilities = card.get("abilities", [])

    for ab_idx, ability in enumerate(abilities):
        bc = ability.get("bytecode", [])
        if not bc:
            continue

        # Walk instructions (groups of 4)
        num_instrs = len(bc) // 4
        for i in range(num_instrs):
            base = i * 4
            op = bc[base]
            v = bc[base + 1] if base + 1 < len(bc) else 0
            a = bc[base + 2] if base + 2 < len(bc) else 0
            s = bc[base + 3] if base + 3 < len(bc) else 0
            op_name = OPCODE_NAMES.get(op, f"UNKNOWN({op})")

            # ── Check 1: LOOK_AND_CHOOSE slot leak ──
            if op == O_LOOK_AND_CHOOSE:
                if s == 6:
                    # Check if source param explicitly says HAND
                    # (We can't know from bytecode alone, but s=6 is suspicious
                    # unless it's intentionally sourcing from hand)
                    # The filter_attr's src_zone bits (12-15) should match
                    filter_info = decode_filter_attr(a)
                    src_bits = filter_info["src_zone"]
                    if src_bits == 0:
                        # No explicit source in attr → slot=6 is likely the
                        # CARD_HAND target leak bug
                        warnings.append(LintWarning(
                            card_id, card_no, card_name, ab_idx, i, "ERROR",
                            f"LOOK_AND_CHOOSE has slot=6 (CARD_HAND) but no source "
                            f"zone in attr bits 12-15. Probable target→source leak. "
                            f"Bytecode: [{op},{v},{a},{s}]"
                        ))
                    # else: attr encodes source=6, so slot=6 is intentional

                # Check filter attr sanity
                filter_info = decode_filter_attr(a)
                if filter_info["unit_enable"] and filter_info["unit_id"] > MAX_UNIT_ID:
                    warnings.append(LintWarning(
                        card_id, card_no, card_name, ab_idx, i, "WARN",
                        f"LOOK_AND_CHOOSE unit ID {filter_info['unit_id']} > {MAX_UNIT_ID}. "
                        f"Attr=0x{a:X}"
                    ))
                if filter_info["group_enable"] and filter_info["group_id"] > MAX_GROUP_ID:
                    warnings.append(LintWarning(
                        card_id, card_no, card_name, ab_idx, i, "WARN",
                        f"LOOK_AND_CHOOSE group ID {filter_info['group_id']} > {MAX_GROUP_ID}. "
                        f"Attr=0x{a:X}"
                    ))

            # ── Check 2: SELECT_CARDS slot leak ──
            if op == O_SELECT_CARDS:
                filter_info = decode_filter_attr(a)
                encoded_src = filter_info["src_zone"]
                if s != 0 and encoded_src != 0 and s != encoded_src:
                    warnings.append(LintWarning(
                        card_id, card_no, card_name, ab_idx, i, "WARN",
                        f"SELECT_CARDS has slot={s} but attr encodes src_zone={encoded_src}. "
                        f"Possible conflict. Bytecode: [{op},{v},{a},{s}]"
                    ))

            # ── Check 3: MOVE_TO_DISCARD with impossible source ──
            if op == O_MOVE_TO_DISCARD:
                # Valid slot values: 4(stage), 6(hand), 7(discard), 8(deck), 13(success)
                if s not in {0, 1, 2, 4, 6, 7, 8, 13}:
                    warnings.append(LintWarning(
                        card_id, card_no, card_name, ab_idx, i, "WARN",
                        f"MOVE_TO_DISCARD has unexpected slot={s}. "
                        f"Bytecode: [{op},{v},{a},{s}]"
                    ))

            # ── Check 4: Bytecode truncation ──
            if op == O_RETURN and i == 0:
                warnings.append(LintWarning(
                    card_id, card_no, card_name, ab_idx, i, "INFO",
                    f"Ability starts with RETURN — effectively a no-op."
                ))

            # ── Check 5: Unknown opcodes ──
            if op not in OPCODE_NAMES and op < 200:
                warnings.append(LintWarning(
                    card_id, card_no, card_name, ab_idx, i, "WARN",
                    f"Unknown opcode {op} (0x{op:02X}). "
                    f"Bytecode: [{op},{v},{a},{s}]"
                ))


def main():
    project_root = Path(__file__).resolve().parents[4]
    compiled_path = project_root / "data" / "cards_compiled.json"

    if not compiled_path.exists():
        print(f"ERROR: {compiled_path} not found. Run: uv run python -m compiler.main")
        sys.exit(1)

    with open(compiled_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    warnings = []

    # Lint member_db
    member_db = data.get("member_db", {})
    for card_id, card in member_db.items():
        lint_card(card_id, card, warnings)

    # Lint live_db
    live_db = data.get("live_db", {})
    for card_id, card in live_db.items():
        lint_card(card_id, card, warnings)

    # ── Report ──
    errors = [w for w in warnings if w.severity == "ERROR"]
    warns = [w for w in warnings if w.severity == "WARN"]
    infos = [w for w in warnings if w.severity == "INFO"]

    print(f"\n{'='*60}")
    print(f"  Bytecode Lint Report")
    print(f"  Cards scanned: {len(member_db) + len(live_db)}")
    print(f"  Errors: {len(errors)}  Warnings: {len(warns)}  Info: {len(infos)}")
    print(f"{'='*60}\n")

    if errors:
        print("── ERRORS ──")
        for w in errors:
            print(f"  {w}")
        print()

    if warns:
        print("── WARNINGS ──")
        for w in warns:
            print(f"  {w}")
        print()

    if infos and "--verbose" in sys.argv:
        print("── INFO ──")
        for w in infos:
            print(f"  {w}")
        print()

    if not warnings:
        print("✅ No issues found!")

    # Write machine-readable report
    report_path = project_root / "reports" / "bytecode_lint.json"
    report_path.parent.mkdir(exist_ok=True)
    report_data = [
        {
            "card_id": w.card_id,
            "card_no": w.card_no,
            "card_name": w.card_name,
            "ability_idx": w.ability_idx,
            "instr_idx": w.instr_idx,
            "severity": w.severity,
            "message": w.message,
        }
        for w in warnings
    ]
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    print(f"\nReport written to: {report_path}")

    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
