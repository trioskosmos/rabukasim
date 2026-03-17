#!/usr/bin/env python3
"""Analyze GPU test failures and categorize them."""

import re
from collections import Counter


def analyze_failures(failure_file: str):
    """Analyze GPU test failures."""

    with open(failure_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract all failure lines
    failures = re.findall(r"\[FAIL\] ([^\n]+)", content)

    # Categorize failures
    error_types = Counter()
    trigger_types = Counter()
    delta_types = Counter()

    for fail in failures:
        # Extract error type
        if "Blade delta mismatch" in fail:
            error_types["Blade delta mismatch"] += 1
            delta_types["BLADE_DELTA"] += 1
        elif "Hand delta mismatch" in fail:
            error_types["Hand delta mismatch"] += 1
            delta_types["HAND_DELTA"] += 1
        elif "Discard delta mismatch" in fail:
            error_types["Discard delta mismatch"] += 1
            delta_types["DISCARD_DELTA"] += 1
        elif "Score delta mismatch" in fail:
            error_types["Score delta mismatch"] += 1
            delta_types["SCORE_DELTA"] += 1
        elif "Member tap expected" in fail:
            error_types["Member tap expected"] += 1
            delta_types["MEMBER_TAP"] += 1
        else:
            error_types["Other"] += 1

        # Extract trigger type
        trigger_match = re.search(r"\((ON_[A-Z_]+)\)", fail)
        if trigger_match:
            trigger_types[trigger_match.group(1)] += 1
        else:
            trigger_types["NO_TRIGGER_SPECIFIED"] += 1

    print("=" * 60)
    print("GPU TEST FAILURE ANALYSIS")
    print("=" * 60)
    print(f"\nTotal failures: {len(failures)}")

    print("\n--- Error Types ---")
    for error, count in error_types.most_common():
        print(f"  {error}: {count}")

    print("\n--- Trigger Types ---")
    for trigger, count in trigger_types.most_common():
        print(f"  {trigger}: {count}")

    print("\n--- Delta Types ---")
    for delta, count in delta_types.most_common():
        print(f"  {delta}: {count}")

    # Calculate potential wins
    print("\n" + "=" * 60)
    print("POTENTIAL WINS ANALYSIS")
    print("=" * 60)

    total_failures = len(failures)

    # Big win 1: Blade delta issues
    blade_failures = error_types.get("Blade delta mismatch", 0)
    print(f"\n1. FIX BLADE DELTA ISSUES: {blade_failures} failures ({blade_failures / total_failures * 100:.1f}%)")
    print("   - Likely cause: ADD_BLADES opcode not working correctly")
    print("   - Affected triggers: ON_PLAY, ON_LIVE_START, ON_LIVE_SUCCESS")

    # Big win 2: Hand delta issues
    hand_failures = error_types.get("Hand delta mismatch", 0)
    print(f"\n2. FIX HAND DELTA ISSUES: {hand_failures} failures ({hand_failures / total_failures * 100:.1f}%)")
    print("   - Likely cause: DRAW/DISCARD opcodes not working correctly")
    print("   - Affected triggers: ON_PLAY, ON_LIVE_START, ON_LIVE_SUCCESS")

    # Big win 3: Member tap issues
    tap_failures = error_types.get("Member tap expected", 0)
    print(f"\n3. FIX MEMBER TAP ISSUES: {tap_failures} failures ({tap_failures / total_failures * 100:.1f}%)")
    print("   - Likely cause: TAP_OPPONENT opcode not working correctly")
    print("   - Affected triggers: ON_PLAY, ON_LIVE_START")

    # Big win 4: Score delta issues
    score_failures = error_types.get("Score delta mismatch", 0)
    print(f"\n4. FIX SCORE DELTA ISSUES: {score_failures} failures ({score_failures / total_failures * 100:.1f}%)")
    print("   - Likely cause: BOOST_SCORE opcode not working correctly")
    print("   - Affected triggers: ON_LIVE_START, ON_LIVE_SUCCESS")

    # Big win 5: Discard delta issues
    discard_failures = error_types.get("Discard delta mismatch", 0)
    print(
        f"\n5. FIX DISCARD DELTA ISSUES: {discard_failures} failures ({discard_failures / total_failures * 100:.1f}%)"
    )
    print("   - Likely cause: MOVE_TO_DISCARD opcode not working correctly")
    print("   - Affected triggers: ON_PLAY, ON_LIVE_START")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY: PRIORITY ORDER")
    print("=" * 60)

    priorities = [
        ("Hand delta", hand_failures),
        ("Blade delta", blade_failures),
        ("Member tap", tap_failures),
        ("Score delta", score_failures),
        ("Discard delta", discard_failures),
    ]

    priorities.sort(key=lambda x: x[1], reverse=True)

    for i, (name, count) in enumerate(priorities, 1):
        if count > 0:
            print(f"{i}. {name}: {count} failures ({count / total_failures * 100:.1f}%)")

    return error_types, trigger_types, delta_types


if __name__ == "__main__":
    analyze_failures("reports/gpu_test_failures.txt")
