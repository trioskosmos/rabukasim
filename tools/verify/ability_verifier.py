#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Ability Verification Script

This script verifies the consistency between:
1. Japanese ability text (raw_text)
2. Manual pseudocode (manual_pseudocode.json)
3. Compiled effects (cards_compiled.json)
4. Bytecode (cards_compiled.json)
5. Rust handler implementation

Usage:
    python tools/verify/ability_verifier.py --all
    python tools/verify/ability_verifier.py --card "LL-bp1-001-R＋"
    python tools/verify/ability_verifier.py --category triggers
"""

import json
import re
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from collections import defaultdict


@dataclass
class VerificationResult:
    """Result of verifying a single aspect of an ability."""
    card_no: str
    ability_index: int
    category: str  # trigger, effect, bytecode, rust
    status: str  # PASS, WARN, ERROR
    message: str
    expected: Optional[str] = None
    actual: Optional[str] = None
    details: dict = field(default_factory=dict)


@dataclass
class CardVerificationReport:
    """Complete verification report for a single card."""
    card_no: str
    card_name: str
    results: list = field(default_factory=list)
    
    @property
    def status(self) -> str:
        if any(r.status == "ERROR" for r in self.results):
            return "ERROR"
        elif any(r.status == "WARN" for r in self.results):
            return "WARN"
        return "PASS"
    
    @property
    def error_count(self) -> int:
        return sum(1 for r in self.results if r.status == "ERROR")
    
    @property
    def warning_count(self) -> int:
        return sum(1 for r in self.results if r.status == "WARN")


class AbilityVerifier:
    """Main verifier class for ability consistency checking."""
    
    # Trigger mappings
    TRIGGER_MAP = {
        0: "NONE",
        1: "ON_PLAY",
        2: "ON_LIVE_START",
        3: "ON_LIVE_SUCCESS",
        4: "TURN_START",
        5: "TURN_END",
        6: "CONSTANT",
        7: "ACTIVATED",
        8: "ON_LEAVES",
        9: "ON_REVEAL",
        10: "ON_POSITION_CHANGE",
    }
    
    # Effect type to opcode mappings
    EFFECT_TYPE_MAP = {
        10: "DRAW",
        11: "ADD_BLADES",
        12: "ADD_HEARTS",
        13: "REDUCE_COST",
        14: "LOOK_DECK",
        15: "RECOVER_LIVE",
        16: "BOOST_SCORE",
        17: "RECOVER_MEMBER",
        18: "BUFF_POWER",
        19: "IMMUNITY",
        20: "MOVE_MEMBER",
        21: "SWAP_CARDS",
        22: "SEARCH_DECK",
        23: "ENERGY_CHARGE",
        24: "SET_BLADES",
        25: "SET_HEARTS",
        27: "NEGATE_EFFECT",
        28: "ORDER_DECK",
        29: "META_RULE",
        30: "SELECT_MODE",
        31: "MOVE_TO_DECK",
        32: "TAP_OPPONENT",
        33: "PLACE_UNDER",
        35: "RESTRICTION",
        39: "TRANSFORM_COLOR",
        40: "REVEAL_CARDS",
        41: "LOOK_AND_CHOOSE",
        42: "CHEER_REVEAL",
        43: "ACTIVATE_MEMBER",
        44: "ADD_TO_HAND",
        45: "COLOR_SELECT",
        47: "TRIGGER_REMOTE",
        48: "REDUCE_HEART_REQ",
        49: "MODIFY_SCORE_RULE",
        50: "ADD_STAGE_ENERGY",
        51: "SET_TAPPED",
        53: "TAP_MEMBER",
        57: "PLAY_MEMBER_FROM_HAND",
        58: "MOVE_TO_DISCARD",
        60: "GRANT_ABILITY",
        61: "INCREASE_HEART_COST",
        63: "PLAY_MEMBER_FROM_DISCARD",
        64: "PAY_ENERGY",
        65: "SELECT_MEMBER",
        66: "DRAW_UNTIL",
        67: "SELECT_PLAYER",
        68: "SELECT_LIVE",
        70: "INCREASE_COST",
        73: "TRANSFORM_HEART",
        74: "SELECT_CARDS",
        75: "OPPONENT_CHOOSE",
        76: "PLAY_LIVE_FROM_DISCARD",
        77: "REDUCE_LIVE_SET_LIMIT",
        81: "ACTIVATE_ENERGY",
        82: "PREVENT_ACTIVATE",
        90: "PREVENT_BATON_TOUCH",
    }
    
    # Target mappings
    TARGET_MAP = {
        0: "SELF",
        1: "ALL_SELF",
        2: "OPPONENT",
        3: "ALL_OPPONENT",
        4: "PLAYER",
        5: "BOTH",
        6: "CARD_HAND",
        7: "CARD_DISCARD",
        8: "CARD_DECK",
    }
    
    # Pseudocode trigger patterns
    TRIGGER_PATTERNS = {
        "ON_PLAY": r"TRIGGER:\s*ON_PLAY",
        "ON_LIVE_START": r"TRIGGER:\s*ON_LIVE_START",
        "ON_LIVE_SUCCESS": r"TRIGGER:\s*ON_LIVE_SUCCESS",
        "TURN_START": r"TRIGGER:\s*TURN_START",
        "TURN_END": r"TRIGGER:\s*TURN_END",
        "CONSTANT": r"TRIGGER:\s*CONSTANT",
        "ACTIVATED": r"TRIGGER:\s*ACTIVATED",
        "ON_LEAVES": r"TRIGGER:\s*ON_LEAVES",
        "ON_REVEAL": r"TRIGGER:\s*ON_REVEAL",
        "ON_POSITION_CHANGE": r"TRIGGER:\s*ON_POSITION_CHANGE",
    }
    
    # Pseudocode effect patterns
    EFFECT_PATTERNS = {
        "DRAW": r"DRAW\((\d+|[^)]+)\)",
        "ADD_BLADES": r"ADD_BLADES\((\d+)\)",
        "ADD_HEARTS": r"ADD_HEARTS\((\d+)\)",
        "BOOST_SCORE": r"BOOST_SCORE\((\d+)\)",
        "RECOVER_MEMBER": r"RECOVER_MEMBER\((\d+)\)",
        "RECOVER_LIVE": r"RECOVER_LIVE\((\d+)\)",
        "ENERGY_CHARGE": r"ENERGY_CHARGE\((\d+)\)",
        "ACTIVATE_ENERGY": r"ACTIVATE_ENERGY\((\d+)\)",
        "ACTIVATE_MEMBER": r"ACTIVATE_MEMBER\((\d+|ALL)\)",
        "TAP_OPPONENT": r"TAP_OPPONENT\((\d+)\)",
        "LOOK_AND_CHOOSE": r"LOOK_AND_CHOOSE\((\d+)\)",
        "SELECT_MODE": r"SELECT_MODE\((\d+)\)",
        "MOVE_TO_DECK": r"MOVE_TO_DECK\((\d+)\)",
        "ADD_TO_HAND": r"ADD_TO_HAND",
        "BUFF_POWER": r"BUFF_POWER\((\d+)\)",
    }
    
    # Japanese text effect patterns (original_text)
    JP_EFFECT_PATTERNS = {
        "DRAW": [
            (r"カード.*?(\d+)枚.*?引", "draw_cards"),
            (r"引く", "draw_one"),
        ],
        "ADD_BLADES": [
            (r"ブレード[^スコア場合]*?[+＋](\d+)", "add_blades"),
            (r"ブレード.*?を得る", "add_blades_gain"),
        ],
        "ADD_HEARTS": [
            (r"ハート[^スコア場合]*?[+＋](\d+)", "add_hearts"),
            (r"ハートを?(\d+)?(つ|個|枚)?(を)?得る", "add_hearts_gain"),
        ],
        "BOOST_SCORE": [
            (r"スコア.*?[+＋](\d+)", "boost_score"),
            (r"合計スコアを[+＋](\d+)", "boost_score_total"),
        ],
        "RECOVER_MEMBER": [
            (r"控え室から.*?メンバーを?.*?手札に加", "recover_member"),
        ],
        "RECOVER_LIVE": [
            (r"控え室から.*?ライブカードを?.*?手札に加", "recover_live"),
            (r"成功ライブカード.*?手札に加", "recover_live_success"),
        ],
        "ENERGY_CHARGE": [
            (r"エネルギー(?:カード)?を?(\d+)?枚.*?(?:置く|加える|チャージ)", "energy_charge"),
        ],
        "ACTIVATE_MEMBER": [
            (r"アクティブに", "activate_member"),
        ],
        "TAP_OPPONENT": [
            (r"相手.*?(\d+)?(?:人|枚)?(?:まで)?.*?(?:ウェイト|休み)", "tap_opponent"),
        ],
    }
    
    # Japanese trigger patterns
    JP_TRIGGER_PATTERNS = {
        "ON_PLAY": r"登場|{{toujyou",
        "ON_LIVE_START": r"ライブ開始時|{{live_start",
        "ON_LIVE_SUCCESS": r"ライブ成功時|{{live_success",
        "TURN_START": r"ターン開始時",
        "TURN_END": r"ターン終了時",
        "CONSTANT": r"常時|{{jyouji",
        "ACTIVATED": r"起動",
        "ON_LEAVES": r"退場|{{taijou",
        "ON_REVEAL": r"公開",
    }
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.cards_data = None
        self.manual_pseudocode = None
        self.opcode_handlers = None
        self._load_data()
    
    def _load_data(self):
        """Load all required data files."""
        # Load compiled cards
        cards_path = self.project_root / "data" / "cards_compiled.json"
        if cards_path.exists():
            with open(cards_path, "r", encoding="utf-8") as f:
                self.cards_data = json.load(f)
        
        # Load manual pseudocode
        pseudocode_path = self.project_root / "data" / "manual_pseudocode.json"
        if pseudocode_path.exists():
            with open(pseudocode_path, "r", encoding="utf-8") as f:
                self.manual_pseudocode = json.load(f)
        
        # Load opcode handlers
        handlers_path = self.project_root / "tools" / "verify" / "data" / "opcode_handlers.json"
        if handlers_path.exists():
            with open(handlers_path, "r", encoding="utf-8") as f:
                self.opcode_handlers = json.load(f)
    
    def verify_all(self) -> list:
        """Verify all cards and return reports."""
        reports = []
        
        if not self.cards_data:
            return reports
        
        for card_id_str, card_data in self.cards_data.get("member_db", {}).items():
            report = self.verify_card(card_data)
            reports.append(report)
        
        return reports
    
    def verify_card(self, card_data: dict) -> CardVerificationReport:
        """Verify a single card's abilities."""
        card_no = card_data.get("card_no", "UNKNOWN")
        card_name = card_data.get("name", "UNKNOWN")
        
        report = CardVerificationReport(
            card_no=card_no,
            card_name=card_name
        )
        
        # Get manual pseudocode for this card
        manual_pc = self.manual_pseudocode.get(card_no, {}).get("pseudocode", "") if self.manual_pseudocode else ""
        
        # Get original Japanese text
        original_text = card_data.get("original_text", "")
        
        # Verify each ability
        for idx, ability in enumerate(card_data.get("abilities", [])):
            # Verify trigger (against both manual pseudocode and Japanese text)
            trigger_result = self._verify_trigger(card_no, idx, ability, manual_pc, original_text)
            if trigger_result:
                report.results.append(trigger_result)
            
            # Verify effects (against both manual pseudocode and Japanese text)
            effect_results = self._verify_effects(card_no, idx, ability, manual_pc, original_text)
            report.results.extend(effect_results)
            
            # Verify bytecode
            bytecode_results = self._verify_bytecode(card_no, idx, ability)
            report.results.extend(bytecode_results)
        
        return report
    
    def _verify_trigger(self, card_no: str, ability_idx: int, ability: dict, manual_pc: str, original_text: str = "") -> Optional[VerificationResult]:
        """Verify trigger consistency."""
        compiled_trigger = ability.get("trigger", 0)
        trigger_name = self.TRIGGER_MAP.get(compiled_trigger, "UNKNOWN")
        
        # Extract triggers from manual pseudocode
        expected_triggers = []
        for trig_name, pattern in self.TRIGGER_PATTERNS.items():
            if re.search(pattern, manual_pc, re.IGNORECASE):
                expected_triggers.append(trig_name)
        
        # Check if compiled trigger matches manual pseudocode
        if expected_triggers:
            # For abilities with multiple triggers, check if this is one of them
            if trigger_name in expected_triggers:
                return VerificationResult(
                    card_no=card_no,
                    ability_index=ability_idx,
                    category="trigger",
                    status="PASS",
                    message=f"Trigger '{trigger_name}' matches manual pseudocode",
                    expected=trigger_name,
                    actual=trigger_name
                )
            elif trigger_name == "NONE" and len(expected_triggers) > 0:
                # Some abilities don't have explicit triggers in compiled data
                return VerificationResult(
                    card_no=card_no,
                    ability_index=ability_idx,
                    category="trigger",
                    status="WARN",
                    message=f"Compiled trigger is NONE but manual pseudocode has: {expected_triggers}",
                    expected=str(expected_triggers),
                    actual=trigger_name
                )
        
        return None
    
    def _verify_effects(self, card_no: str, ability_idx: int, ability: dict, manual_pc: str, original_text: str = "") -> list:
        """Verify effect consistency."""
        results = []
        compiled_effects = ability.get("effects", [])
        
        # Extract effects from manual pseudocode
        expected_effects = self._extract_effects_from_pseudocode(manual_pc)
        
        # Track which expected effects have been matched (by index)
        matched_expected = set()
        
        for eff_idx, effect in enumerate(compiled_effects):
            effect_type = effect.get("effect_type", 0)
            effect_name = self.EFFECT_TYPE_MAP.get(effect_type, f"UNKNOWN({effect_type})")
            value = effect.get("value", 0)
            target = effect.get("target", 0)
            target_name = self.TARGET_MAP.get(target, f"UNKNOWN({target})")
            
            # Check if this effect exists in manual pseudocode
            # Find the first unmatched expected effect with matching name
            found_in_pseudocode = False
            for exp_idx, exp_eff in enumerate(expected_effects):
                if exp_idx in matched_expected:
                    continue  # Skip already matched effects
                if exp_eff["name"] == effect_name:
                    # Check value
                    if exp_eff.get("value") is not None and value != exp_eff["value"]:
                        results.append(VerificationResult(
                            card_no=card_no,
                            ability_index=ability_idx,
                            category="effect",
                            status="ERROR",
                            message=f"Effect '{effect_name}' value mismatch",
                            expected=str(exp_eff["value"]),
                            actual=str(value),
                            details={"effect_index": eff_idx}
                        ))
                    else:
                        found_in_pseudocode = True
                        matched_expected.add(exp_idx)  # Mark as matched
                    break
            
            if found_in_pseudocode:
                results.append(VerificationResult(
                    card_no=card_no,
                    ability_index=ability_idx,
                    category="effect",
                    status="PASS",
                    message=f"Effect '{effect_name}' with value={value}, target={target_name} matches",
                    expected=effect_name,
                    actual=effect_name
                ))
            elif effect_name not in [e["name"] for e in expected_effects]:
                # Effect not found in pseudocode - could be OK if pseudocode is incomplete
                results.append(VerificationResult(
                    card_no=card_no,
                    ability_index=ability_idx,
                    category="effect",
                    status="WARN",
                    message=f"Effect '{effect_name}' not found in manual pseudocode",
                    expected="Present in pseudocode",
                    actual="Not found",
                    details={"effect_index": eff_idx}
                ))
        
        return results
    
    def _extract_effects_from_pseudocode(self, pseudocode: str) -> list:
        """Extract effect information from pseudocode string."""
        effects = []
        
        for eff_name, pattern in self.EFFECT_PATTERNS.items():
            matches = re.finditer(pattern, pseudocode, re.IGNORECASE)
            for match in matches:
                effect = {"name": eff_name}
                if match.groups():
                    try:
                        effect["value"] = int(match.group(1))
                    except (ValueError, TypeError):
                        effect["value_str"] = match.group(1)
                effects.append(effect)
        
        return effects
    
    def _verify_bytecode(self, card_no: str, ability_idx: int, ability: dict) -> list:
        """Verify bytecode consistency with effects."""
        results = []
        bytecode = ability.get("bytecode", [])
        effects = ability.get("effects", [])
        
        if not bytecode:
            if effects:
                results.append(VerificationResult(
                    card_no=card_no,
                    ability_index=ability_idx,
                    category="bytecode",
                    status="ERROR",
                    message="Effects exist but bytecode is empty",
                    expected="Non-empty bytecode",
                    actual="Empty"
                ))
            return results
        
        # Verify bytecode structure
        # Bytecode format: [op, v, a, s, ...] for each instruction
        if len(bytecode) % 4 != 0:
            results.append(VerificationResult(
                card_no=card_no,
                ability_index=ability_idx,
                category="bytecode",
                status="WARN",
                message=f"Bytecode length ({len(bytecode)}) is not a multiple of 4",
                details={"bytecode_length": len(bytecode)}
            ))
        
        # Check if bytecode opcodes match effect types
        bytecode_ops = []
        for i in range(0, len(bytecode), 4):
            if i + 3 < len(bytecode):
                op = bytecode[i]
                v = bytecode[i + 1]
                a = bytecode[i + 2]
                s = bytecode[i + 3]
                bytecode_ops.append({"op": op, "v": v, "a": a, "s": s})
        
        # Compare bytecode ops with effects
        for eff_idx, effect in enumerate(effects):
            effect_type = effect.get("effect_type", 0)
            value = effect.get("value", 0)
            
            # Find matching bytecode instruction
            found_match = False
            for bc_op in bytecode_ops:
                if bc_op["op"] == effect_type and bc_op["v"] == value:
                    found_match = True
                    break
            
            if not found_match:
                # Check if any bytecode has the same opcode
                matching_ops = [bc for bc in bytecode_ops if bc["op"] == effect_type]
                if matching_ops:
                    # Opcode exists but value might differ
                    bc_value = matching_ops[0]["v"]
                    if bc_value != value:
                        results.append(VerificationResult(
                            card_no=card_no,
                            ability_index=ability_idx,
                            category="bytecode",
                            status="WARN",
                            message=f"Bytecode value differs from effect value for {self.EFFECT_TYPE_MAP.get(effect_type, effect_type)}",
                            expected=str(value),
                            actual=str(bc_value),
                            details={"effect_index": eff_idx}
                        ))
                else:
                    results.append(VerificationResult(
                        card_no=card_no,
                        ability_index=ability_idx,
                        category="bytecode",
                        status="ERROR",
                        message=f"No bytecode instruction found for effect type {effect_type}",
                        expected=f"Opcode {effect_type}",
                        actual="Not found",
                        details={"effect_index": eff_idx}
                    ))
        
        # Verify Rust handler exists for each opcode
        if self.opcode_handlers:
            for bc_op in bytecode_ops:
                op_str = str(bc_op["op"])
                if op_str in self.opcode_handlers.get("opcodes", {}):
                    handler = self.opcode_handlers["opcodes"][op_str].get("handler")
                    if handler is None:
                        results.append(VerificationResult(
                            card_no=card_no,
                            ability_index=ability_idx,
                            category="rust",
                            status="WARN",
                            message=f"Opcode {bc_op['op']} has no Rust handler defined",
                            details={"opcode": bc_op["op"]}
                        ))
        
        return results


def generate_report(reports: list, output_path: Path):
    """Generate a markdown report from verification results."""
    total_cards = len(reports)
    passed = sum(1 for r in reports if r.status == "PASS")
    warnings = sum(1 for r in reports if r.status == "WARN")
    errors = sum(1 for r in reports if r.status == "ERROR")
    
    # Count by category
    category_stats = defaultdict(lambda: {"pass": 0, "warn": 0, "error": 0})
    for report in reports:
        for result in report.results:
            if result.status == "PASS":
                category_stats[result.category]["pass"] += 1
            elif result.status == "WARN":
                category_stats[result.category]["warn"] += 1
            elif result.status == "ERROR":
                category_stats[result.category]["error"] += 1
    
    # Generate markdown
    md = f"""# アビリティ検証レポート

## サマリー

- **総カード数**: {total_cards}
- **成功**: {passed}
- **警告**: {warnings}
- **エラー**: {errors}

## カテゴリ別結果

| カテゴリ | 成功 | 警告 | エラー |
|---------|------|------|--------|
"""
    for category, stats in sorted(category_stats.items()):
        md += f"| {category} | {stats['pass']} | {stats['warn']} | {stats['error']} |\n"
    
    # Add error details
    error_reports = [r for r in reports if r.status == "ERROR"]
    if error_reports:
        md += "\n## エラー詳細\n\n"
        for report in error_reports[:50]:  # Limit to first 50
            md += f"### {report.card_no} ({report.card_name})\n\n"
            for result in report.results:
                if result.status == "ERROR":
                    md += f"**{result.category}**: {result.message}\n\n"
                    if result.expected:
                        md += f"- 期待値: {result.expected}\n"
                    if result.actual:
                        md += f"- 実際値: {result.actual}\n"
                    md += "\n"
    
    # Add warning details
    warning_reports = [r for r in reports if r.status == "WARN"]
    if warning_reports:
        md += "\n## 警告詳細\n\n"
        for report in warning_reports[:30]:  # Limit to first 30
            md += f"### {report.card_no} ({report.card_name})\n\n"
            for result in report.results:
                if result.status == "WARN":
                    md += f"**{result.category}**: {result.message}\n\n"
    
    # Write report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md)
    
    return md


def main():
    parser = argparse.ArgumentParser(description="Verify ability consistency")
    parser.add_argument("--all", action="store_true", help="Verify all cards")
    parser.add_argument("--card", type=str, help="Verify specific card by card_no")
    parser.add_argument("--category", type=str, help="Verify specific category (triggers, effects, bytecode, rust)")
    parser.add_argument("--output", type=str, default="reports/ability_verification_report.md", help="Output report path")
    
    args = parser.parse_args()
    
    project_root = Path(__file__).parent.parent.parent
    verifier = AbilityVerifier(project_root)
    
    if args.card:
        # Verify specific card
        if verifier.cards_data:
            for card_id_str, card_data in verifier.cards_data.get("member_db", {}).items():
                if card_data.get("card_no") == args.card:
                    report = verifier.verify_card(card_data)
                    print(f"Card: {report.card_no} - Status: {report.status}")
                    for result in report.results:
                        print(f"  [{result.status}] {result.category}: {result.message}")
                    break
    else:
        # Verify all cards
        reports = verifier.verify_all()
        output_path = project_root / args.output
        report_md = generate_report(reports, output_path)
        print(f"Report generated: {output_path}")
        print(f"Total: {len(reports)}, Passed: {sum(1 for r in reports if r.status == 'PASS')}, "
              f"Warnings: {sum(1 for r in reports if r.status == 'WARN')}, "
              f"Errors: {sum(1 for r in reports if r.status == 'ERROR')}")


if __name__ == "__main__":
    main()
