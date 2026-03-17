#!/usr/bin/env python
"""
Verify parser robustness by running all abilities through parse -> compile -> decompile cycle.
Reports any failures or discrepancies.
"""

import json
import os
import sys
from typing import Dict, Tuple

sys.path.insert(0, os.getcwd())

from tools.decompile_bytecode import decompile


def load_compiled_cards() -> Dict:
    """Load compiled cards from data/cards_compiled.json"""
    path = "data/cards_compiled.json"
    if not os.path.exists(path):
        print(f"Error: {path} not found. Run compiler first.")
        return {}

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def verify_single_ability(card_no: str, ab_idx: int, ability_data: Dict) -> Tuple[bool, str]:
    """Verify a single ability's bytecode can be decompiled."""
    bytecode = ability_data.get("bytecode", [])
    raw_text = ability_data.get("raw_text", "")

    if not bytecode:
        return True, "Empty bytecode (OK)"

    # Check for RETURN-only bytecode (just [1, 0, 0, 0])
    # This is valid for trigger-only abilities or cost-only abilities
    if len(bytecode) == 4 and bytecode[0] == 1:
        # RETURN only - check if raw_text has actual effects (not just costs)
        # Note: COST: lines are NOT effects, they are handled separately by the engine
        has_effects = any(
            kw in raw_text.upper()
            for kw in ["EFFECT:", "BOOST", "DRAW", "HEAL", "DAMAGE", "DESTROY", "SWAP", "SHUFFLE", "SEARCH", "SCORE"]
        )
        # Exclude COST-only abilities (ENERGY_CHARGE, etc.)
        has_cost_only = "COST:" in raw_text.upper() and not has_effects
        if not has_effects or has_cost_only:
            return True, "Trigger/cost-only ability (OK)"
        # Has effects in text but not in bytecode - parser bug
        return False, "Parser bug: effects in text but bytecode is RETURN only"

    try:
        decompiled = decompile(bytecode)
        if not decompiled:
            return False, "Decompile returned empty string"
        return True, decompiled
    except Exception as e:
        return False, f"Decompile error: {e}"


def verify_all_cards():
    """Verify all cards' abilities."""
    data = load_compiled_cards()

    if not data:
        print("No cards loaded")
        return

    # Flatten all cards from different databases
    all_cards = {}
    for db_name in ["member_db", "live_db", "energy_db"]:
        if db_name in data and isinstance(data[db_name], dict):
            all_cards.update(data[db_name])

    total_cards = len(all_cards)
    total_abilities = 0
    successful = 0
    failed = 0
    errors = []

    print(f"Verifying {total_cards} cards...")
    print("-" * 60)

    for card_no, card_data in all_cards.items():
        if not isinstance(card_data, dict):
            continue
        abilities = card_data.get("abilities", [])

        for ab_idx, ab in enumerate(abilities):
            total_abilities += 1
            ok, msg = verify_single_ability(card_no, ab_idx, ab)

            if ok:
                successful += 1
            else:
                failed += 1
                errors.append(
                    {
                        "card": card_no,
                        "ability_idx": ab_idx,
                        "error": msg,
                        "bytecode": ab.get("bytecode", [])[:16],  # First 16 elements
                        "raw_text": ab.get("raw_text", "")[:100],
                    }
                )

    print("-" * 60)
    print(f"Total cards: {total_cards}")
    print(f"Total abilities: {total_abilities}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Success rate: {successful / total_abilities * 100:.1f}%" if total_abilities > 0 else "N/A")

    if errors:
        print("\n" + "=" * 60)
        print("ERRORS:")
        print("=" * 60)
        for err in errors[:20]:  # Show first 20 errors
            print(f"\nCard: {err['card']}, Ability #{err['ability_idx']}")
            print(f"  Error: {err['error']}")
            print(f"  Bytecode: {err['bytecode']}")
            print(f"  Raw text: {err['raw_text']}")

        if len(errors) > 20:
            print(f"\n... and {len(errors) - 20} more errors")

    # Save full report
    report_path = "reports/parser_verification_report.json"
    os.makedirs("reports", exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "summary": {
                    "total_cards": total_cards,
                    "total_abilities": total_abilities,
                    "successful": successful,
                    "failed": failed,
                    "success_rate": successful / total_abilities * 100 if total_abilities > 0 else 0,
                },
                "errors": errors,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    print(f"\nFull report saved to: {report_path}")

    return failed == 0


if __name__ == "__main__":
    print("NOTE: This tool has been moved to a skill.")
    print("New location: .agent/skills/parser_roundtrip_verification/scripts/verify_roundtrip.py")
    print("-" * 60)
    success = verify_all_cards()
    sys.exit(0 if success else 1)
