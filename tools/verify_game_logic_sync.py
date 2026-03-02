#!/usr/bin/env python3
"""
WGSL-Rust Game Logic Synchronization Verification Tool

This tool verifies that game logic (legal actions, ability activations,
game states) is synchronized between CPU (Rust) and GPU (WGSL).

Usage:
    python tools/verify_game_logic_sync.py [--report]

Features:
    - Compares opcode implementation coverage
    - Compares condition implementation coverage
    - Analyzes legal action generation parity
    - Checks phase handling consistency
    - Generates detailed sync report
"""

import json
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class OpcodeInfo:
    """Information about an opcode implementation."""

    name: str
    value: int
    rust_implemented: bool = False
    wgsl_implemented: bool = False
    rust_source: str = ""
    wgsl_source: str = ""


@dataclass
class ConditionInfo:
    """Information about a condition implementation."""

    name: str
    value: int
    rust_implemented: bool = False
    wgsl_implemented: bool = False
    rust_source: str = ""
    wgsl_source: str = ""


@dataclass
class PhaseInfo:
    """Information about a phase implementation."""

    name: str
    value: int
    rust_handler: bool = False
    wgsl_handler: bool = False


@dataclass
class SyncReport:
    """Complete synchronization report."""

    opcodes: Dict[str, OpcodeInfo] = field(default_factory=dict)
    conditions: Dict[str, ConditionInfo] = field(default_factory=dict)
    phases: Dict[str, PhaseInfo] = field(default_factory=dict)

    # Summary stats
    opcode_coverage: float = 0.0
    condition_coverage: float = 0.0
    phase_coverage: float = 0.0

    # Critical sync issues
    critical_issues: List[dict] = field(default_factory=list)

    # Recommendations
    recommendations: List[str] = field(default_factory=list)


def load_metadata(metadata_path: str) -> dict:
    """Load metadata.json."""
    with open(metadata_path, "r", encoding="utf-8") as f:
        return json.load(f)


def find_rust_opcode_handlers(rust_dir: str) -> Dict[str, str]:
    """Find Rust opcode handler implementations."""
    handlers = {}

    # Patterns to match opcode handlers
    patterns = [
        r"O_(\w+)\s*=>",  # Match arm pattern
        r"Opcode::(\w+)\s*=>",  # Enum match pattern
        r"fn (?:handle_|execute_)(\w+)",  # Handler function pattern
    ]

    for root, dirs, files in os.walk(rust_dir):
        for file in files:
            if file.endswith(".rs"):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                        for pattern in patterns:
                            for match in re.finditer(pattern, content):
                                opcode_name = match.group(1).upper()
                                handlers[opcode_name] = filepath
                except Exception as e:
                    print(f"Warning: Could not read {filepath}: {e}")

    return handlers


def find_wgsl_opcode_handlers(wgsl_dir: str) -> Dict[str, str]:
    """Find WGSL opcode handler implementations."""
    handlers = {}

    # WGSL uses case statements in execute_opcode function
    patterns = [
        r"case\s+O_(\w+):",  # Switch case pattern: case O_DRAW:
        r"case\s+(\d+)",  # Numeric case: case 11, 18:
        r"if\s*\(\s*opcode\s*==\s*O_(\w+)\)",  # If comparison pattern
        r"if\s*\(\s*op\s*==\s*(\d+)",  # Numeric comparison: if (op == 11)
        r"const\s+O_(\w+):\s*i32\s*=\s*\d+\s*;\s*//\s*IMPLEMENTED",  # Marked as implemented
    ]

    # Opcode value to name mapping (from metadata)
    opcode_values = {
        0: "NOP",
        1: "RETURN",
        2: "JUMP",
        3: "JUMP_IF_FALSE",
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
        26: "FORMATION_CHANGE",
        27: "NEGATE_EFFECT",
        28: "ORDER_DECK",
        29: "META_RULE",
        30: "SELECT_MODE",
        31: "MOVE_TO_DECK",
        32: "TAP_OPPONENT",
        33: "PLACE_UNDER",
        35: "RESTRICTION",
        36: "BATON_TOUCH_MOD",
        37: "SET_SCORE",
        38: "SWAP_ZONE",
        39: "TRANSFORM_COLOR",
        40: "REVEAL_CARDS",
        41: "LOOK_AND_CHOOSE",
        42: "CHEER_REVEAL",
        43: "ACTIVATE_MEMBER",
        44: "ADD_TO_HAND",
        45: "COLOR_SELECT",
        46: "REPLACE_EFFECT",
        47: "TRIGGER_REMOTE",
        48: "REDUCE_HEART_REQ",
        49: "MODIFY_SCORE_RULE",
        50: "ADD_STAGE_ENERGY",
        51: "SET_TAPPED",
        52: "ADD_CONTINUOUS",
        53: "TAP_MEMBER",
        57: "PLAY_MEMBER_FROM_HAND",
        58: "MOVE_TO_DISCARD",
        60: "GRANT_ABILITY",
        61: "INCREASE_HEART_COST",
        62: "REDUCE_YELL_COUNT",
        63: "PLAY_MEMBER_FROM_DISCARD",
        64: "PAY_ENERGY",
        65: "SELECT_MEMBER",
        66: "DRAW_UNTIL",
        67: "SELECT_PLAYER",
        68: "SELECT_LIVE",
        69: "REVEAL_UNTIL",
        70: "INCREASE_COST",
        71: "PREVENT_PLAY_TO_SLOT",
        72: "SWAP_AREA",
        73: "TRANSFORM_HEART",
        74: "SELECT_CARDS",
        75: "OPPONENT_CHOOSE",
        76: "PLAY_LIVE_FROM_DISCARD",
        77: "REDUCE_LIVE_SET_LIMIT",
        80: "PREVENT_SET_TO_SUCCESS_PILE",
        81: "ACTIVATE_ENERGY",
        82: "PREVENT_ACTIVATE",
        83: "SET_HEART_COST",
        90: "PREVENT_BATON_TOUCH",
        91: "LOOK_DECK_DYNAMIC",
        92: "REDUCE_SCORE",
        93: "REPEAT_ABILITY",
        94: "LOSE_EXCESS_HEARTS",
        95: "SKIP_ACTIVATE_PHASE",
        96: "PAY_ENERGY_DYNAMIC",
        97: "PLACE_ENERGY_UNDER_MEMBER",
    }

    for root, dirs, files in os.walk(wgsl_dir):
        for file in files:
            if file.endswith(".wgsl"):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()

                        # Pattern 1: case O_NAME:
                        for match in re.finditer(r"case\s+O_(\w+):", content):
                            opcode_name = match.group(1).upper()
                            handlers[opcode_name] = filepath

                        # Pattern 2: const O_NAME: i32 = N; // IMPLEMENTED
                        for match in re.finditer(r"const\s+O_(\w+):\s*i32\s*=\s*\d+\s*;\s*//\s*IMPLEMENTED", content):
                            opcode_name = match.group(1).upper()
                            handlers[opcode_name] = filepath

                        # Pattern 3: case N, M: (numeric cases)
                        for match in re.finditer(r"case\s+(\d+)\s*,", content):
                            value = int(match.group(1))
                            if value in opcode_values:
                                handlers[opcode_values[value]] = filepath

                        # Pattern 4: if (op == N)
                        for match in re.finditer(r"if\s*\(\s*op\s*==\s*(\d+)", content):
                            value = int(match.group(1))
                            if value in opcode_values:
                                handlers[opcode_values[value]] = filepath

                except Exception as e:
                    print(f"Warning: Could not read {filepath}: {e}")

    return handlers


def find_rust_condition_handlers(rust_dir: str) -> Dict[str, str]:
    """Find Rust condition handler implementations."""
    handlers = {}

    patterns = [
        r"C_(\w+)\s*=>",  # Match arm pattern
        r"ConditionType::(\w+)\s*=>",  # Enum match pattern
        r"fn check_(\w+)",  # Checker function pattern
    ]

    for root, dirs, files in os.walk(rust_dir):
        for file in files:
            if file.endswith(".rs"):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                        for pattern in patterns:
                            for match in re.finditer(pattern, content):
                                cond_name = match.group(1).upper()
                                handlers[cond_name] = filepath
                except Exception as e:
                    print(f"Warning: Could not read {filepath}: {e}")

    return handlers


def find_wgsl_condition_handlers(wgsl_dir: str) -> Dict[str, str]:
    """Find WGSL condition handler implementations."""
    handlers = {}

    patterns = [
        r"case\s+C_(\w+):",  # Switch case pattern
        r"if\s*\(\s*cond\s*==\s*C_(\w+)\)",  # If comparison pattern
        r"C_(\w+)\s*:",  # Case label pattern (without 'case' keyword)
    ]

    for root, dirs, files in os.walk(wgsl_dir):
        for file in files:
            if file.endswith(".wgsl"):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                        for pattern in patterns:
                            for match in re.finditer(pattern, content):
                                cond_name = match.group(1).upper()
                                handlers[cond_name] = filepath
                except Exception as e:
                    print(f"Warning: Could not read {filepath}: {e}")

    return handlers


def analyze_phase_handlers(rust_dir: str, wgsl_dir: str, phases: dict) -> Dict[str, PhaseInfo]:
    """Analyze phase handling in Rust and WGSL."""
    phase_infos = {}

    for name, value in phases.items():
        info = PhaseInfo(name=name, value=value)

        # Check Rust handlers
        rust_patterns = [
            rf"Phase::{name}\s*=>",
            rf"handle_{name.lower()}",
            rf"do_{name.lower()}_phase",
        ]

        for root, dirs, files in os.walk(rust_dir):
            for file in files:
                if file.endswith(".rs"):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            content = f.read()
                            for pattern in rust_patterns:
                                if re.search(pattern, content, re.IGNORECASE):
                                    info.rust_handler = True
                                    break
                    except Exception:
                        pass

        # Check WGSL handlers
        wgsl_patterns = [
            rf"PHASE_{name}\s*\)",
            rf"phase\s*==\s*PHASE_{name}",
        ]

        for root, dirs, files in os.walk(wgsl_dir):
            for file in files:
                if file.endswith(".wgsl"):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            content = f.read()
                            for pattern in wgsl_patterns:
                                if re.search(pattern, content):
                                    info.wgsl_handler = True
                                    break
                    except Exception:
                        pass

        phase_infos[name] = info

    return phase_infos


def generate_sync_report(metadata_path: str, rust_dir: str, wgsl_dir: str) -> SyncReport:
    """Generate complete synchronization report."""
    report = SyncReport()

    # Load metadata
    metadata = load_metadata(metadata_path)

    # Find implementations
    rust_opcodes = find_rust_opcode_handlers(rust_dir)
    wgsl_opcodes = find_wgsl_opcode_handlers(wgsl_dir)
    rust_conditions = find_rust_condition_handlers(rust_dir)
    wgsl_conditions = find_wgsl_condition_handlers(wgsl_dir)

    # Analyze opcodes
    for name, value in metadata.get("opcodes", {}).items():
        info = OpcodeInfo(
            name=name,
            value=value,
            rust_implemented=name in rust_opcodes,
            wgsl_implemented=name in wgsl_opcodes,
            rust_source=rust_opcodes.get(name, ""),
            wgsl_source=wgsl_opcodes.get(name, ""),
        )
        report.opcodes[name] = info

    # Analyze conditions
    for name, value in metadata.get("conditions", {}).items():
        info = ConditionInfo(
            name=name,
            value=value,
            rust_implemented=name in rust_conditions,
            wgsl_implemented=name in wgsl_conditions,
            rust_source=rust_conditions.get(name, ""),
            wgsl_source=wgsl_conditions.get(name, ""),
        )
        report.conditions[name] = info

    # Analyze phases
    report.phases = analyze_phase_handlers(rust_dir, wgsl_dir, metadata.get("phases", {}))

    # Calculate coverage
    total_opcodes = len(report.opcodes)
    wgsl_opcodes_implemented = sum(1 for o in report.opcodes.values() if o.wgsl_implemented)
    report.opcode_coverage = wgsl_opcodes_implemented / total_opcodes if total_opcodes > 0 else 0

    total_conditions = len(report.conditions)
    wgsl_conditions_implemented = sum(1 for c in report.conditions.values() if c.wgsl_implemented)
    report.condition_coverage = wgsl_conditions_implemented / total_conditions if total_conditions > 0 else 0

    total_phases = len(report.phases)
    wgsl_phases_implemented = sum(1 for p in report.phases.values() if p.wgsl_handler)
    report.phase_coverage = wgsl_phases_implemented / total_phases if total_phases > 0 else 0

    # Identify critical issues
    for name, info in report.opcodes.items():
        if info.rust_implemented and not info.wgsl_implemented:
            report.critical_issues.append(
                {
                    "type": "opcode_missing_in_wgsl",
                    "name": name,
                    "severity": "high" if info.value < 100 else "medium",
                    "rust_source": info.rust_source,
                }
            )

    for name, info in report.conditions.items():
        if info.rust_implemented and not info.wgsl_implemented:
            report.critical_issues.append(
                {
                    "type": "condition_missing_in_wgsl",
                    "name": name,
                    "severity": "medium",
                    "rust_source": info.rust_source,
                }
            )

    # Generate recommendations
    if report.opcode_coverage < 1.0:
        missing = [n for n, o in report.opcodes.items() if o.rust_implemented and not o.wgsl_implemented]
        if missing:
            report.recommendations.append(
                f"Implement missing WGSL opcodes: {', '.join(missing[:5])}{'...' if len(missing) > 5 else ''}"
            )

    if report.condition_coverage < 1.0:
        missing = [n for n, c in report.conditions.items() if c.rust_implemented and not c.wgsl_implemented]
        if missing:
            report.recommendations.append(
                f"Implement missing WGSL conditions: {', '.join(missing[:5])}{'...' if len(missing) > 5 else ''}"
            )

    report.recommendations.append("Run parity tests regularly to catch sync issues early")
    report.recommendations.append("Use sync_metadata.py to keep constants synchronized")

    return report


def print_report(report: SyncReport):
    """Print human-readable report."""
    print("\n" + "=" * 70)
    print("WGSL-RUST GAME LOGIC SYNC VERIFICATION REPORT")
    print("=" * 70)

    print("\n### COVERAGE SUMMARY ###")
    print(
        f"  Opcodes:    {report.opcode_coverage * 100:.1f}% ({sum(1 for o in report.opcodes.values() if o.wgsl_implemented)}/{len(report.opcodes)})"
    )
    print(
        f"  Conditions: {report.condition_coverage * 100:.1f}% ({sum(1 for c in report.conditions.values() if c.wgsl_implemented)}/{len(report.conditions)})"
    )
    print(
        f"  Phases:     {report.phase_coverage * 100:.1f}% ({sum(1 for p in report.phases.values() if p.wgsl_handler)}/{len(report.phases)})"
    )

    if report.critical_issues:
        print("\n### CRITICAL ISSUES ###")
        for issue in report.critical_issues[:10]:
            print(f"  [{issue['severity'].upper()}] {issue['type']}: {issue['name']}")
            if issue.get("rust_source"):
                print(f"    Rust source: {issue['rust_source']}")

    if report.recommendations:
        print("\n### RECOMMENDATIONS ###")
        for rec in report.recommendations:
            print(f"  - {rec}")

    print("\n" + "=" * 70)

    if report.opcode_coverage >= 0.95 and report.condition_coverage >= 0.9:
        print("RESULT: GOOD SYNC STATUS")
        return 0
    elif report.opcode_coverage >= 0.8 and report.condition_coverage >= 0.8:
        print("RESULT: ACCEPTABLE SYNC STATUS (some gaps)")
        return 0
    else:
        print("RESULT: SYNC ISSUES DETECTED")
        return 1


def to_dict(report: SyncReport) -> dict:
    """Convert report to dictionary for JSON serialization."""
    return {
        "opcode_coverage": report.opcode_coverage,
        "condition_coverage": report.condition_coverage,
        "phase_coverage": report.phase_coverage,
        "opcodes": {
            name: {
                "value": info.value,
                "rust_implemented": info.rust_implemented,
                "wgsl_implemented": info.wgsl_implemented,
                "rust_source": info.rust_source,
                "wgsl_source": info.wgsl_source,
            }
            for name, info in report.opcodes.items()
        },
        "conditions": {
            name: {
                "value": info.value,
                "rust_implemented": info.rust_implemented,
                "wgsl_implemented": info.wgsl_implemented,
                "rust_source": info.rust_source,
                "wgsl_source": info.wgsl_source,
            }
            for name, info in report.conditions.items()
        },
        "phases": {
            name: {"value": info.value, "rust_handler": info.rust_handler, "wgsl_handler": info.wgsl_handler}
            for name, info in report.phases.items()
        },
        "critical_issues": report.critical_issues,
        "recommendations": report.recommendations,
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Verify WGSL-Rust game logic synchronization")
    parser.add_argument("--metadata", default="data/metadata.json", help="Path to metadata.json")
    parser.add_argument("--rust-dir", default="engine_rust_src/src", help="Path to Rust source directory")
    parser.add_argument("--wgsl-dir", default="engine_rust_src/src/core", help="Path to WGSL shader directory")
    parser.add_argument("--report", default="reports/game_logic_sync_report.json", help="Path to output JSON report")
    parser.add_argument("--quiet", action="store_true", help="Only print errors")

    args = parser.parse_args()

    report = generate_sync_report(args.metadata, args.rust_dir, args.wgsl_dir)

    # Write JSON report
    if args.report:
        os.makedirs(os.path.dirname(args.report) or ".", exist_ok=True)
        with open(args.report, "w", encoding="utf-8") as f:
            json.dump(to_dict(report), f, indent=2)
        print(f"Report written to: {args.report}")

    if not args.quiet:
        exit_code = print_report(report)
    else:
        exit_code = 1 if report.opcode_coverage < 0.8 or report.condition_coverage < 0.8 else 0

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
