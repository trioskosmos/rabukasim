"""Analyze test failures and categorize them."""

import re
import subprocess
from collections import defaultdict


def analyze_failures():
    # Run pytest with verbose output to capture failure details
    result = subprocess.run(
        ["uv", "run", "pytest", "engine/tests/cards/batches/test_auto_generated_strict_v2.py", "-v", "--tb=line", "-q"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    output = result.stdout + result.stderr

    # Extract failed tests
    failed_tests = re.findall(r"FAILED (.+?) - (.+?)$", output, re.MULTILINE)

    # Categorize by error message
    categories = defaultdict(list)
    for test_name, error in failed_tests:
        # Extract card ID from test name
        card_match = re.search(r"test_strict_(.+)", test_name.split("::")[-1])
        card_id = card_match.group(1) if card_match else test_name

        # Categorize by error type
        if "Ability count mismatch" in error:
            categories["Ability Count Mismatch"].append(card_id)
        elif "Condition count mismatch" in error:
            categories["Condition Count Mismatch"].append(card_id)
        elif "Effect count mismatch" in error:
            categories["Effect Count Mismatch"].append(card_id)
        elif "Trigger mismatch" in error:
            categories["Trigger Mismatch"].append(card_id)
        elif "Effect type mismatch" in error:
            categories["Effect Type Mismatch"].append(card_id)
        elif "Condition type mismatch" in error:
            categories["Condition Type Mismatch"].append(card_id)
        else:
            categories[f"Other: {error[:50]}"].append(card_id)

    # Print summary
    print(f"\n{'=' * 60}")
    print(f"FAILURE ANALYSIS: {len(failed_tests)} total failures")
    print(f"{'=' * 60}\n")

    for category, cards in sorted(categories.items(), key=lambda x: -len(x[1])):
        print(f"\n## {category} ({len(cards)} cards)")
        print("-" * 40)
        for card in sorted(cards)[:10]:  # Show first 10
            print(f"  - {card}")
        if len(cards) > 10:
            print(f"  ... and {len(cards) - 10} more")


if __name__ == "__main__":
    analyze_failures()
