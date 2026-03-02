#!/usr/bin/env python3
"""
Extract CPU tests from Rust source files and generate GPU parity test code.

This script parses Rust test files and extracts:
- Test function names
- Bytecode vectors
- Setup code patterns
- Assertion patterns

Output: Generated Rust code for test_gpu_parity_suite.rs
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class ExtractedTest:
    """Represents an extracted CPU test."""

    name: str
    source_file: str
    bytecode: List[int]
    setup_code: str
    assertions: List[str]
    uses_real_db: bool
    has_interaction: bool
    opcode: str


# Regex patterns for parsing
TEST_FN_PATTERN = re.compile(r"#\[test\]\s*\n\s*fn (test_opcode_\w+)\s*\([^)]*\)\s*\{")
BYTECODE_PATTERN = re.compile(r"let\s+bc\s*=\s*vec!\[([^\]]+)\]")
BYTECODE_ALT_PATTERN = re.compile(r"vec!\[([O_\w]+,\s*\d+,\s*\d+,\s*\d+,[^\]]+)\]")
OPCODE_PATTERN = re.compile(r"O_[A-Z_]+")
RESOLVE_BYTECODE_PATTERN = re.compile(r"state\.resolve_bytecode\s*\(\s*&db\s*,\s*&bc\s*,\s*&ctx\s*\)")
CREATE_TEST_DB_PATTERN = re.compile(r"create_test_db\(\)")
LOAD_REAL_DB_PATTERN = re.compile(r"load_real_db\(\)")
SUSPEND_INTERACTION_PATTERN = re.compile(r"suspend_interaction|interaction_stack|choice_index")


def extract_bytecode(content: str, start_pos: int, end_pos: int) -> Optional[List[int]]:
    """Extract bytecode vector from test function body."""
    body = content[start_pos:end_pos]

    # Try standard bytecode pattern
    match = BYTECODE_PATTERN.search(body)
    if match:
        bc_str = match.group(1)
        # Parse the bytecode values
        values = []
        for token in bc_str.split(","):
            token = token.strip()
            if token.startswith("O_"):
                # This is an opcode constant, keep as-is for Rust
                values.append(token)
            elif token.isdigit() or (token.startswith("-") and token[1:].isdigit()):
                values.append(int(token))
            elif token:
                # Could be an expression, keep as-is
                values.append(token)
        return values

    return None


def extract_opcode_from_bytecode(bytecode: List) -> Optional[str]:
    """Extract the primary opcode from bytecode vector."""
    for val in bytecode:
        if isinstance(val, str) and val.startswith("O_"):
            return val
    return None


def has_interaction(content: str, start_pos: int, end_pos: int) -> bool:
    """Check if test involves interaction/choice handling."""
    body = content[start_pos:end_pos]
    return bool(SUSPEND_INTERACTION_PATTERN.search(body))


def extract_assertions(content: str, start_pos: int, end_pos: int) -> List[str]:
    """Extract assertion statements from test function body."""
    body = content[start_pos:end_pos]
    assertions = []

    # Match assert_eq! and assert! patterns
    assert_patterns = [
        re.compile(r"assert_eq!\s*\([^;]+\);"),
        re.compile(r"assert!\s*\([^;]+\);"),
    ]

    for pattern in assert_patterns:
        for match in pattern.finditer(body):
            assertions.append(match.group(0))

    return assertions


def parse_test_file(filepath: Path) -> List[ExtractedTest]:
    """Parse a Rust test file and extract tests."""
    content = filepath.read_text(encoding="utf-8")
    tests = []

    for match in TEST_FN_PATTERN.finditer(content):
        test_name = match.group(1)
        fn_start = match.end()

        # Find matching closing brace
        brace_count = 1
        pos = fn_start
        while pos < len(content) and brace_count > 0:
            if content[pos] == "{":
                brace_count += 1
            elif content[pos] == "}":
                brace_count -= 1
            pos += 1
        fn_end = pos - 1

        # Extract test components
        bytecode = extract_bytecode(content, fn_start, fn_end)
        if not bytecode:
            continue  # Skip tests without bytecode

        opcode = extract_opcode_from_bytecode(bytecode)
        if not opcode:
            continue

        uses_real_db = bool(LOAD_REAL_DB_PATTERN.search(content[fn_start:fn_end]))
        has_inter = has_interaction(content, fn_start, fn_end)
        assertions = extract_assertions(content, fn_start, fn_end)

        # Extract setup code (simplified - just get lines before resolve_bytecode)
        setup_lines = []
        for line in content[fn_start:fn_end].split("\n"):
            if "resolve_bytecode" in line:
                break
            if line.strip() and not line.strip().startswith("//"):
                setup_lines.append(line)

        test = ExtractedTest(
            name=test_name,
            source_file=str(filepath),
            bytecode=bytecode,
            setup_code="\n".join(setup_lines),
            assertions=assertions,
            uses_real_db=uses_real_db,
            has_interaction=has_inter,
            opcode=opcode,
        )
        tests.append(test)

    return tests


def generate_parity_test_code(test: ExtractedTest, card_id: int) -> str:
    """Generate GPU parity test code for an extracted test."""
    lines = []

    # Skip tests with interactions for now
    if test.has_interaction:
        lines.append(f"    // {test.name}: SKIPPED (interaction-based)")
        lines.append("    // TODO: Implement choice propagation")
        return "\n".join(lines)

    # Skip tests using real DB for now
    if test.uses_real_db:
        lines.append(f"    // {test.name}: SKIPPED (uses real DB)")
        lines.append("    // TODO: Map card IDs for production test")
        return "\n".join(lines)

    # Generate card definition - remove duplicate O_RETURN if present
    bc_values = list(test.bytecode)
    # Check if bytecode already ends with O_RETURN sequence
    while len(bc_values) >= 4 and bc_values[-4] == "O_RETURN":
        bc_values = bc_values[:-4]

    bc_str = ", ".join(str(v) for v in bc_values)
    lines.append(f"    // {test.name}")
    lines.append(f"    let bc_{card_id} = vec![{bc_str}, O_RETURN, 0, 0, 0];")
    lines.append(
        f'    add_card(&mut unit_db, {card_id}, "{test.name}", vec![], vec![(TriggerType::OnPlay, bc_{card_id}, vec![])]);'
    )

    return "\n".join(lines)


def generate_test_runner(test: ExtractedTest, card_id: int, test_num: int) -> str:
    """Generate test runner code."""
    if test.has_interaction or test.uses_real_db:
        return ""

    lines = []
    lines.append(f"    // Run {test.name}")
    lines.append("    let mut state = create_test_state();")
    lines.append(f"    state.core.players[0].hand = vec![{card_id}].into();")
    lines.append("    state.core.players[0].energy_zone = (10..30).collect::<Vec<i32>>().into();")
    lines.append(
        f'    if !run_parity_check(&unit_manager, &unit_db, &state, Action::PlayMember {{ hand_idx: 0, slot_idx: 0 }}.id(), "U{test_num} {test.name}") {{ mismatch_count += 1; }}'
    )

    return "\n".join(lines)


def main():
    """Main entry point."""
    # Find test files
    rust_src = Path("engine_rust_src/src")
    test_files = [
        "opcode_tests.rs",
        "mechanics_tests.rs",
        "untested_opcode_tests.rs",
        "opcode_missing_tests.rs",
    ]

    all_tests = []
    for tf in test_files:
        filepath = rust_src / tf
        if filepath.exists():
            tests = parse_test_file(filepath)
            all_tests.extend(tests)
            print(f"Extracted {len(tests)} tests from {tf}")

    print(f"\nTotal tests extracted: {len(all_tests)}")

    # Categorize tests
    simple_tests = [t for t in all_tests if not t.has_interaction and not t.uses_real_db]
    interaction_tests = [t for t in all_tests if t.has_interaction]
    real_db_tests = [t for t in all_tests if t.uses_real_db]

    print(f"Simple tests (can convert): {len(simple_tests)}")
    print(f"Interaction tests (need special handling): {len(interaction_tests)}")
    print(f"Real DB tests (need ID mapping): {len(real_db_tests)}")

    # Generate output
    output_lines = []
    output_lines.append("// Auto-generated GPU parity test code")
    output_lines.append("// Generated by tools/extract_parity_tests.py")
    output_lines.append("")
    output_lines.append("// === CARD DEFINITIONS ===")

    card_id = 3000
    test_num = 20
    for test in simple_tests:
        output_lines.append(generate_parity_test_code(test, card_id))
        card_id += 1

    output_lines.append("")
    output_lines.append("// === TEST RUNNERS ===")

    card_id = 3000
    for test in simple_tests:
        output_lines.append(generate_test_runner(test, card_id, test_num))
        card_id += 1
        test_num += 1

    # Write output
    output_path = Path("engine_rust_src/src/bin/generated_parity_tests.rs")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(output_lines), encoding="utf-8")
    print(f"\nGenerated code written to {output_path}")


if __name__ == "__main__":
    main()
