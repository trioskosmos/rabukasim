#!/usr/bin/env python3
"""
Analyze GPU parity test failures and categorize them by pattern.

This tool reads test output and categorizes failures into common patterns
to help identify root causes and prioritize fixes.

Usage:
    python tools/analyze_parity_failures.py
    python tools/analyze_parity_failures.py --input reports/test_output.txt
    python tools/analyze_parity_failures.py --json reports/failures.json
"""

import json
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple


@dataclass
class TestFailure:
    """Represents a single test failure."""

    card_id: str
    ability_idx: int
    test_name: str
    error_type: str
    expected: str
    actual: str
    raw_line: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class FailurePattern:
    """Represents a category of failures."""

    name: str
    description: str
    examples: List[str] = field(default_factory=list)
    count: int = 0
    likely_cause: str = ""
    suggested_fix: str = ""

    # Value analysis for numeric failures
    expected_values: List[int] = field(default_factory=list)
    actual_values: List[int] = field(default_factory=list)
    diffs: List[int] = field(default_factory=list)


def parse_test_output(output_path: str) -> Tuple[List[str], List[TestFailure], int]:
    """Parse test output file and extract failures."""
    # Try multiple encodings
    content = None
    for encoding in ["utf-8", "utf-8-sig", "cp932", "shift_jis", "latin-1"]:
        try:
            with open(output_path, "r", encoding=encoding) as f:
                content = f.read()
            break
        except UnicodeDecodeError:
            continue

    if content is None:
        # Fall back to binary read and decode with errors='replace'
        with open(output_path, "rb") as f:
            content = f.read().decode("utf-8", errors="replace")

    lines = content.split("\n")
    failures = []
    pass_lines = []
    skip_count = 0

    # Pattern: [FAIL] CARD_ID:AB0: Error message
    fail_pattern = re.compile(r"\[FAIL\]\s+([^:]+):AB(\d+):\s+(.+)")
    pass_pattern = re.compile(r"\[PASS\]\s+(.+)")
    skip_pattern = re.compile(r"\[SKIP\]")

    for line in lines:
        line = line.strip()
        if "[PASS]" in line:
            pass_lines.append(line)
        elif "[FAIL]" in line:
            match = fail_pattern.search(line)
            if match:
                card_id = match.group(1)
                ability_idx = int(match.group(2))
                error_msg = match.group(3)

                # Parse error type
                error_type = "UNKNOWN"
                expected = ""
                actual = ""

                if "Hand delta mismatch" in error_msg:
                    error_type = "HAND_DELTA"
                elif "Discard delta mismatch" in error_msg:
                    error_type = "DISCARD_DELTA"
                elif "Energy tap delta mismatch" in error_msg:
                    error_type = "ENERGY_TAP_DELTA"
                elif "Member tap expected" in error_msg:
                    error_type = "MEMBER_TAP"
                elif "Deck delta mismatch" in error_msg:
                    error_type = "DECK_DELTA"
                elif "Score delta mismatch" in error_msg:
                    error_type = "SCORE_DELTA"
                elif "Blade delta mismatch" in error_msg:
                    error_type = "BLADE_DELTA"
                elif "Energy delta mismatch" in error_msg:
                    error_type = "ENERGY_DELTA"

                # Extract expected/actual values
                vals = re.findall(r"(-?\d+)", error_msg)
                if len(vals) >= 2:
                    expected = vals[0]
                    actual = vals[1]

                failures.append(
                    TestFailure(
                        card_id=card_id,
                        ability_idx=ability_idx,
                        test_name=f"{card_id}:AB{ability_idx}",
                        error_type=error_type,
                        expected=expected,
                        actual=actual,
                        raw_line=line,
                    )
                )
        elif "[SKIP]" in line:
            skip_count += 1

    return pass_lines, failures, skip_count


def categorize_failures(failures: List[TestFailure]) -> Dict[str, FailurePattern]:
    """Categorize failures into patterns."""
    patterns = {
        "HAND_DELTA": FailurePattern(
            name="Hand Delta Mismatch",
            description="Hand count change doesn't match expected",
            likely_cause="GPU not correctly applying draw/discard effects, or semantic truth has wrong delta values",
            suggested_fix="Check DRAW/DISCARD opcode implementation in WGSL; verify semantic truth generation",
        ),
        "DISCARD_DELTA": FailurePattern(
            name="Discard Delta Mismatch",
            description="Discard pile count change doesn't match expected",
            likely_cause="Discard opcodes not executing or wrong cards being discarded",
            suggested_fix="Check DISCARD opcode in WGSL; verify cost payment flow",
        ),
        "ENERGY_TAP_DELTA": FailurePattern(
            name="Energy Tap Delta Mismatch",
            description="Energy tap count doesn't match expected",
            likely_cause="Energy payment not happening or wrong amount being tapped",
            suggested_fix="Check PAY_ENERGY opcode; verify energy zone setup in test",
        ),
        "MEMBER_TAP": FailurePattern(
            name="Member Tap Not Detected",
            description="Expected member tap didn't occur",
            likely_cause="TAP_MEMBER opcode not implemented or wrong targeting",
            suggested_fix="Check TAP_MEMBER opcode in WGSL; verify moved_flags tracking",
        ),
        "DECK_DELTA": FailurePattern(
            name="Deck Delta Mismatch",
            description="Deck count change doesn't match expected",
            likely_cause="Draw effects not properly reducing deck",
            suggested_fix="Check DRAW opcode; verify deck/hand synchronization",
        ),
        "SCORE_DELTA": FailurePattern(
            name="Score Delta Mismatch",
            description="Score change doesn't match expected",
            likely_cause="Score effects not applying correctly",
            suggested_fix="Check SCORE opcode implementation",
        ),
        "BLADE_DELTA": FailurePattern(
            name="Blade Delta Mismatch",
            description="Blade buff change doesn't match expected",
            likely_cause="Blade buff effects not applying correctly",
            suggested_fix="Check BLADE_BUFF opcode implementation",
        ),
        "ENERGY_DELTA": FailurePattern(
            name="Energy Delta Mismatch",
            description="Energy count change doesn't match expected",
            likely_cause="Energy gain/loss effects not applying",
            suggested_fix="Check energy zone management",
        ),
        "UNKNOWN": FailurePattern(
            name="Unknown Error",
            description="Uncategorized error type",
            likely_cause="Needs investigation",
            suggested_fix="Manual analysis required",
        ),
    }

    for f in failures:
        patterns[f.error_type].count += 1
        patterns[f.error_type].examples.append(f.test_name)

        # Track values for numeric analysis
        if f.expected and f.actual:
            try:
                exp = int(f.expected)
                act = int(f.actual)
                diff = act - exp
                patterns[f.error_type].expected_values.append(exp)
                patterns[f.error_type].actual_values.append(act)
                patterns[f.error_type].diffs.append(diff)
            except ValueError:
                pass

    return patterns


def find_multi_error_cards(failures: List[TestFailure]) -> Dict[str, List[TestFailure]]:
    """Find cards with multiple error types."""
    card_errors = defaultdict(list)
    for f in failures:
        card_errors[f.card_id].append(f)

    # Filter to cards with multiple different error types
    multi_error = {}
    for card_id, errors in card_errors.items():
        error_types = set(e.error_type for e in errors)
        if len(error_types) > 1:
            multi_error[card_id] = errors

    return multi_error


def compute_value_statistics(pattern: FailurePattern) -> Dict:
    """Compute statistics for numeric failures."""
    if not pattern.diffs:
        return {}

    diffs = pattern.diffs
    return {
        "count": len(diffs),
        "avg_diff": round(sum(diffs) / len(diffs), 2),
        "min_diff": min(diffs),
        "max_diff": max(diffs),
        "common_diff": Counter(diffs).most_common(1)[0][0] if diffs else 0,
        "diff_distribution": dict(Counter(diffs).most_common(10)),
    }


def generate_report(output_path: str, report_path: str, json_path: str):
    """Generate comprehensive failure analysis report."""
    pass_lines, failures, skip_count = parse_test_output(output_path)
    patterns = categorize_failures(failures)
    multi_error = find_multi_error_cards(failures)

    total_tests = len(pass_lines) + len(failures)
    pass_rate = len(pass_lines) / total_tests * 100 if total_tests > 0 else 0

    # Build report
    report_lines = [
        "# GPU Parity Test Failure Analysis",
        "",
        f"**Generated from:** `{output_path}`",
        "",
        "## Summary",
        "",
        f"- **Total Tests:** {total_tests}",
        f"- **Passed:** {len(pass_lines)}",
        f"- **Failed:** {len(failures)}",
        f"- **Skipped:** {skip_count}",
        f"- **Pass Rate:** {pass_rate:.1f}%",
        "",
        "## Failure Patterns",
        "",
        "| Pattern | Count | % of Failures | Description |",
        "|---------|-------|---------------|-------------|",
    ]

    for pattern_name, pattern in sorted(patterns.items(), key=lambda x: -x[1].count):
        if pattern.count > 0:
            pct = pattern.count / len(failures) * 100 if failures else 0
            report_lines.append(f"| {pattern.name} | {pattern.count} | {pct:.1f}% | {pattern.description} |")

    report_lines.extend(
        [
            "",
            "## Detailed Pattern Analysis",
            "",
        ]
    )

    for pattern_name, pattern in sorted(patterns.items(), key=lambda x: -x[1].count):
        if pattern.count == 0:
            continue

        report_lines.extend(
            [
                f"### {pattern.name}",
                "",
                f"**Count:** {pattern.count}",
                "",
                f"**Likely Cause:** {pattern.likely_cause}",
                "",
                f"**Suggested Fix:** {pattern.suggested_fix}",
                "",
            ]
        )

        # Value analysis if available
        stats = compute_value_statistics(pattern)
        if stats:
            report_lines.extend(
                [
                    "**Value Analysis:**",
                    "",
                    f"- Average diff: {stats['avg_diff']}",
                    f"- Min diff: {stats['min_diff']}",
                    f"- Max diff: {stats['max_diff']}",
                    f"- Most common diff: {stats['common_diff']}",
                    "",
                    "**Diff Distribution:**",
                    "",
                ]
            )
            for diff, count in stats["diff_distribution"].items():
                report_lines.append(f"- Diff {diff}: {count} occurrences")
            report_lines.append("")

        # Examples (limit to 15)
        report_lines.append("**Examples:**")
        report_lines.append("")
        for ex in pattern.examples[:15]:
            report_lines.append(f"- `{ex}`")
        if len(pattern.examples) > 15:
            report_lines.append(f"- ... and {len(pattern.examples) - 15} more")
        report_lines.append("")

    # Multi-error cards
    if multi_error:
        report_lines.extend(
            [
                "## Cards with Multiple Error Types",
                "",
                f"Found **{len(multi_error)}** cards with failures in multiple categories.",
                "These should be investigated first as they may reveal fundamental issues.",
                "",
                "| Card ID | Error Types | Failure Count |",
                "|---------|-------------|---------------|",
            ]
        )

        for card_id, errors in sorted(multi_error.items(), key=lambda x: -len(x[1]))[:30]:
            error_types = sorted(set(e.error_type for e in errors))
            report_lines.append(f"| `{card_id}` | {', '.join(error_types)} | {len(errors)} |")

    report_lines.extend(
        [
            "",
            "## Recommendations",
            "",
            "### Priority 1: High Impact Fixes",
            "",
        ]
    )

    # Sort by count for recommendations
    sorted_patterns = sorted(patterns.items(), key=lambda x: -x[1].count)
    priority = 1
    for pattern_name, pattern in sorted_patterns[:5]:
        if pattern.count > 0:
            report_lines.append(f"{priority}. **Fix {pattern.name}** ({pattern.count} failures)")
            report_lines.append(f"   - {pattern.suggested_fix}")
            priority += 1

    report_lines.extend(
        [
            "",
            "### Priority 2: Investigation Needed",
            "",
            "Cards with multiple error types should be investigated first.",
            "",
        ]
    )

    # Write report
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    print(f"Report written to: {report_path}")

    # Build JSON summary
    summary = {
        "total_tests": total_tests,
        "passed": len(pass_lines),
        "failed": len(failures),
        "skipped": skip_count,
        "pass_rate": round(pass_rate, 1),
        "patterns": {},
        "multi_error_cards": len(multi_error),
        "failures": [f.to_dict() for f in failures[:100]],  # First 100 for JSON
    }

    for pattern_name, pattern in patterns.items():
        stats = compute_value_statistics(pattern)
        summary["patterns"][pattern_name] = {"count": pattern.count, "examples": pattern.examples[:10], "stats": stats}

    # Write JSON summary
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"JSON summary written to: {json_path}")

    return summary


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Analyze GPU parity test failures")
    parser.add_argument("--input", "-i", default="reports/test_output.txt", help="Input test output file")
    parser.add_argument("--output", "-o", default="reports/failure_analysis.md", help="Output report file")
    parser.add_argument("--json", "-j", default="reports/failure_analysis.json", help="Output JSON summary")

    args = parser.parse_args()

    # Check input exists
    if not Path(args.input).exists():
        print(f"Error: Input file not found: {args.input}")
        return 1

    # Generate report
    summary = generate_report(args.input, args.output, args.json)

    print(f"\n{'=' * 50}")
    print(f"Summary: {summary['passed']}/{summary['total_tests']} passed ({summary['pass_rate']}%)")
    print("Failures by pattern:")
    for name, data in sorted(summary["patterns"].items(), key=lambda x: -x[1]["count"]):
        if data["count"] > 0:
            print(f"  - {name}: {data['count']}")

    return 0


if __name__ == "__main__":
    exit(main())
