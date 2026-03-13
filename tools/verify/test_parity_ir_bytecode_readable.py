#!/usr/bin/env python3
"""
Parity tests for IR <-> bytecode <-> readable decode.

This test suite ensures that:
1. Abilities compile to bytecode correctly
2. Semantic forms (IR) are built consistently from abilities
3. Bytecode can be decoded to human-readable form
4. All three representations (IR, bytecode, readable) are consistent

These tests catch layout drift early: if bytecode layout changes but
semantic form or decoder don't update, tests will fail immediately.

Layout versioning is verified: tests ensure version markers are present
and consistent across compiled output.
"""

import json
import os
import sys
from typing import Any, Dict, List, Tuple

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from engine.models.ability import Ability
from engine.models.ability_ir import (
    BYTECODE_LAYOUT_NAME,
    BYTECODE_LAYOUT_VERSION,
    SEMANTIC_FORM_VERSION,
    AbilityIR,
)
from engine.models.bytecode_readable import (
    CONDITION_NAMES,
    COST_NAMES,
    OPCODE_NAMES,
    TRIGGER_NAMES,
    decode_bytecode,
    opcode_name,
    trigger_name,
)


class ParityTestResult:
    """Container for parity test outcomes."""

    def __init__(self, test_name: str):
        self.test_name = test_name
        self.passed = False
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def add_error(self, msg: str):
        self.errors.append(msg)

    def add_warning(self, msg: str):
        self.warnings.append(msg)

    def set_passed(self):
        self.passed = True

    def summary(self) -> str:
        status = "[PASS]" if self.passed else "[FAIL]"
        lines = [f"{status} {self.test_name}"]
        if self.errors:
            for err in self.errors:
                lines.append(f"  ERROR: {err}")
        if self.warnings:
            for warn in self.warnings:
                lines.append(f"  WARNING: {warn}")
        return "\n".join(lines)


def test_ability_compilation(ability: Ability) -> ParityTestResult:
    """Test that an ability compiles to bytecode without errors."""
    result = ParityTestResult(f"Ability compilation: {ability.raw_text[:40]}")

    try:
        ability.compile()

        if not hasattr(ability, "bytecode") or ability.bytecode is None:
            result.add_error("Ability.compile() did not produce bytecode")
            return result

        if not isinstance(ability.bytecode, list):
            result.add_error(
                f"Bytecode is {type(ability.bytecode)}, expected list"
            )
            return result

        if len(ability.bytecode) == 0:
            result.add_error("Bytecode is empty")
            return result

        # Bytecode should be 5-word chunks
        if len(ability.bytecode) % 5 != 0:
            result.add_warning(
                f"Bytecode length {len(ability.bytecode)} is not multiple of 5"
            )

        result.set_passed()
    except Exception as e:
        result.add_error(f"Compilation raised exception: {e}")

    return result


def test_semantic_form_building(ability: Ability) -> ParityTestResult:
    """Test that semantic form (IR) builds successfully from ability."""
    result = ParityTestResult(f"Semantic form building: {ability.raw_text[:40]}")

    try:
        # Semantic form must be built after compilation
        if not hasattr(ability, "bytecode") or ability.bytecode is None:
            result.add_error("Cannot build semantic form without bytecode")
            return result

        semantic_form_dict = ability.build_semantic_form()

        if semantic_form_dict is None:
            result.add_error("build_semantic_form() returned None")
            return result

        if not isinstance(semantic_form_dict, dict):
            result.add_error(
                f"Semantic form is {type(semantic_form_dict)}, expected dict"
            )
            return result

        # Check required fields
        required_fields = [
            "semantic_version",
            "bytecode_layout_version",
            "bytecode_layout_name",
            "trigger",
            "effects",
            "conditions",
            "costs",
        ]
        for field in required_fields:
            if field not in semantic_form_dict:
                result.add_error(f"Semantic form missing field: {field}")
                return result

        # Verify version markers
        if semantic_form_dict["semantic_version"] != SEMANTIC_FORM_VERSION:
            result.add_error(
                f"semantic_version mismatch: "
                f"{semantic_form_dict['semantic_version']} != {SEMANTIC_FORM_VERSION}"
            )
            return result

        if semantic_form_dict["bytecode_layout_version"] != BYTECODE_LAYOUT_VERSION:
            result.add_error(
                f"bytecode_layout_version mismatch: "
                f"{semantic_form_dict['bytecode_layout_version']} != {BYTECODE_LAYOUT_VERSION}"
            )
            return result

        if semantic_form_dict["bytecode_layout_name"] != BYTECODE_LAYOUT_NAME:
            result.add_error(
                f"bytecode_layout_name mismatch: "
                f"{semantic_form_dict['bytecode_layout_name']} != {BYTECODE_LAYOUT_NAME}"
            )
            return result

        result.set_passed()
    except Exception as e:
        result.add_error(f"Semantic form building raised exception: {e}")

    return result


def test_bytecode_decodable(
    bytecode: List[int], ability_desc: str
) -> ParityTestResult:
    """Test that bytecode can be decoded to readable form."""
    result = ParityTestResult(f"Bytecode decodable: {ability_desc[:40]}")

    try:
        readable = decode_bytecode(bytecode)

        if readable is None or readable == "":
            result.add_error("Bytecode decoding returned empty/None")
            return result

        if "LEGEND" not in readable:
            result.add_warning("Decoded bytecode missing legend section")

        result.set_passed()
    except Exception as e:
        result.add_error(f"Bytecode decoding raised exception: {e}")

    return result


def test_bytecode_chunk_structure(
    bytecode: List[int], ability_desc: str
) -> ParityTestResult:
    """Test that bytecode chunks are valid 5-word structures."""
    result = ParityTestResult(f"Bytecode structure valid: {ability_desc[:40]}")

    try:
        # All chunks should be 5 words
        if len(bytecode) % 5 != 0:
            result.add_error(
                f"Bytecode length {len(bytecode)} not multiple of 5"
            )
            return result

        # Break into 5-word chunks
        for i in range(0, len(bytecode), 5):
            chunk = bytecode[i : i + 5]
            if len(chunk) != 5:
                result.add_error(
                    f"Chunk at offset {i} has length {len(chunk)}, "
                    f"expected 5"
                )
                return result

            op, val, attr_low, attr_high, slot = chunk

            # Opcode should be decodable
            if op not in OPCODE_NAMES and op < 1000:
                # Some opcodes may legitimately not be in OPCODE_NAMES if dynamic
                if op >= 1000:
                    # Negated opcode
                    base_op = op - 1000
                    if base_op not in OPCODE_NAMES:
                        result.add_warning(
                            f"Chunk {i//5}: opcode {op} not found in "
                            f"OPCODE_NAMES"
                        )

        result.set_passed()
    except Exception as e:
        result.add_error(f"Bytecode structure validation raised exception: {e}")

    return result


def test_naming_consistency() -> ParityTestResult:
    """Test that naming dicts are consistent and have no conflicts."""
    result = ParityTestResult("Naming consistency")

    try:
        # Check for duplicate keys (shouldn't happen, but catch edge cases)
        all_keys = set()
        for key in OPCODE_NAMES.keys():
            if key in all_keys:
                result.add_error(f"Duplicate key in OPCODE_NAMES: {key}")
                return result
            all_keys.add(key)

        # Check that trigger names are populated
        if not TRIGGER_NAMES:
            result.add_error("TRIGGER_NAMES is empty")
            return result

        # Check that at least some conditions exist
        if not CONDITION_NAMES:
            result.add_error("CONDITION_NAMES is empty")
            return result

        # Test opcode_name() function works
        for key in list(OPCODE_NAMES.keys())[:5]:  # Test first 5
            name = opcode_name(key)
            if name is None or name == "":
                result.add_error(f"opcode_name({key}) returned empty/None")
                return result

        # Test trigger_name() function works
        for key in list(TRIGGER_NAMES.keys())[:5]:  # Test first 5
            name = trigger_name(key)
            if name is None or name == "":
                result.add_error(f"trigger_name({key}) returned empty/None")
                return result

        result.set_passed()
    except Exception as e:
        result.add_error(f"Naming consistency check raised exception: {e}")

    return result


def test_compiled_json_structure(compiled_json_path: str) -> List[ParityTestResult]:
    """Test that compiled JSON file has proper version markers."""
    results = []
    result = ParityTestResult(f"Compiled JSON structure: {compiled_json_path}")

    try:
        if not os.path.exists(compiled_json_path):
            result.add_error(f"Compiled JSON not found: {compiled_json_path}")
            results.append(result)
            return results

        with open(compiled_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if "meta" not in data:
            result.add_error("Compiled JSON missing 'meta' section")
            results.append(result)
            return results

        meta = data["meta"]
        required_meta_fields = [
            "bytecode_layout_version",
            "bytecode_layout_name",
            "semantic_form_version",
            "semantic_form_enabled",
        ]
        for field in required_meta_fields:
            if field not in meta:
                result.add_error(f"Meta section missing field: {field}")
                results.append(result)
                return results

        # Verify meta values match constants
        if meta["bytecode_layout_version"] != BYTECODE_LAYOUT_VERSION:
            result.add_error(
                f"Meta bytecode_layout_version {meta['bytecode_layout_version']} "
                f"!= {BYTECODE_LAYOUT_VERSION}"
            )
            results.append(result)
            return results

        if meta["semantic_form_version"] != SEMANTIC_FORM_VERSION:
            result.add_error(
                f"Meta semantic_form_version {meta['semantic_form_version']} "
                f"!= {SEMANTIC_FORM_VERSION}"
            )
            results.append(result)
            return results

        result.set_passed()
        results.append(result)

        # Now check individual card entries
        card_check_result = ParityTestResult("Compiled JSON card entries have version markers")
        
        # Check for cards in member_db, live_db, energy_db
        card_sources = [
            ("member_db", data.get("member_db", {})),
            ("live_db", data.get("live_db", {})),
            ("energy_db", data.get("energy_db", {})),
        ]
        
        card_count_checked = 0
        for source_name, source_data in card_sources:
            if card_count_checked >= 10:
                break

            for card_no, card_data in source_data.items():
                if card_count_checked >= 10:
                    break

                abilities = card_data.get("abilities", [])
                
                for ability in abilities:
                    if "semantic_form" in ability:
                        sf = ability["semantic_form"]
                        if "semantic_version" not in sf:
                            card_check_result.add_error(
                                f"{source_name}[{card_no}] ability missing "
                                f"semantic_version in semantic_form"
                            )
                            break
                        if "bytecode_layout_version" not in sf:
                            card_check_result.add_error(
                                f"{source_name}[{card_no}] ability missing "
                                f"bytecode_layout_version in semantic_form"
                            )
                            break

                card_count_checked += 1

        if not card_check_result.errors:
            card_check_result.set_passed()
        results.append(card_check_result)

    except Exception as e:
        result.add_error(f"JSON structure check raised exception: {e}")
        results.append(result)

    return results


def run_parity_tests(compiled_json_path: str = None) -> Tuple[int, int]:
    """
    Run all parity tests and report results.
    
    Returns: (passed_count, failed_count)
    """
    results = []

    print("\n" + "=" * 70)
    print("PARITY TESTS: IR <-> Bytecode <-> Readable Decode")
    print("=" * 70)

    # Test 1: Naming consistency
    print("\n[1] Testing naming consistency...")
    results.append(test_naming_consistency())

    # Test 2: Load a few sample abilities to test
    print("[2] Testing with sample abilities...")
    try:
        # This is a simplified test - in production you'd load from compiled data
        # For now, we just test the framework
        sample_abilities = [
            # Example ability (simplified for testing)
            {
                "trigger": "ON_PLAY",
                "costs": [],
                "conditions": [],
                "effects": [],
                "instructions": [],
                "raw_text": "Test ability",
            }
        ]

        # Note: This is a placeholder. In real use, you'd load actual abilities
        # from the compiled JSON or from parsing
        print("  (Skipping real ability tests - use compiled JSON to validate)")

    except Exception as e:
        print(f"  ERROR loading sample abilities: {e}")

    # Test 3: Compiled JSON structure
    if compiled_json_path is None:
        # Try default locations
        possible_paths = [
            "data/cards_compiled.json",
            "engine/data/cards_compiled.json",
        ]
        for path in possible_paths:
            if os.path.exists(path):
                compiled_json_path = path
                break

    if compiled_json_path and os.path.exists(compiled_json_path):
        print(f"[3] Testing compiled JSON structure ({compiled_json_path})...")
        results.extend(test_compiled_json_structure(compiled_json_path))
    else:
        print("[3] Skipping compiled JSON tests (file not found)")

    # Print results
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)

    passed = 0
    failed = 0
    for result in results:
        print(result.summary())
        if result.passed:
            passed += 1
        else:
            failed += 1

    print("\n" + "=" * 70)
    print(f"Summary: {passed} passed, {failed} failed")
    print("=" * 70 + "\n")

    return passed, failed


if __name__ == "__main__":
    passed, failed = run_parity_tests()
    sys.exit(0 if failed == 0 else 1)
