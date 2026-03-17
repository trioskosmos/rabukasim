import json
import sys


def analyze_report(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return

    output = []

    performances = data.get("performance_history", [])
    if not performances:
        for key, value in data.items():
            if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                if "lives" in value[0] and "yell_cards" in value[0]:
                    performances = value
                    break

    if not performances:
        print("Could not find performances list.")
        return

    players = data.get("players", [])
    final_success = [{c.get("id"): c.get("name") for c in p.get("success_lives", [])} for p in players]
    final_discard = [{c.get("id"): c.get("name") for c in p.get("discard", [])} for p in players]

    # Dictionary: turn -> {0: score, 1: score, lives: {pid: [lives]}}
    turn_data = {}
    for step in performances:
        turn = step.get("turn")
        pid = step.get("player_id")
        if turn not in turn_data:
            turn_data[turn] = {0: 0, 1: 0, "lives": {0: [], 1: []}}

        turn_data[turn][pid] = step.get("total_score", 0)
        turn_data[turn]["lives"][pid] = step.get("lives", [])

    output.append("=== DETAILED TURN ANALYSIS ===")
    for turn in sorted(turn_data.keys()):
        d = turn_data[turn]
        s0, s1 = d[0], d[1]
        is_tie = s0 == s1
        winner = -1
        if s0 > s1:
            winner = 0
        elif s1 > s0:
            winner = 1

        output.append(f"\n[Turn {turn}] Scores: P0={s0}, P1={s1} (Winner: {winner if winner >= 0 else 'TIE'})")

        for pid in [0, 1]:
            lives = d["lives"][pid]
            if not lives:
                continue

            output.append(f"  Player {pid} Performance:")
            for live in lives:
                lid = live.get("id")
                lname = live.get("name")
                passed = live.get("passed")

                status = "PASSED" if passed else "FAILED"
                result = "DISCARDED"
                if lid in final_success[pid]:
                    # We need to know if THIS instance moved.
                    # Since we don't have per-turn success_lives list,
                    # we use a heuristic: if passed and pid won/tied,
                    # and it's in final success zone.
                    result = "SUCCESS_ZONE (Final)"

                output.append(f"    - {lname} (ID: {lid}): {status} -> {result}")

                if passed:
                    # Explain why it might be discarded
                    if winner >= 0 and pid != winner:
                        output.append(f"      [EXPLANATION] LOST: Player {pid} lost the judgement.")
                    elif is_tie:
                        output.append("      [EXPLANATION] TIE: Checking Rule 8.4.7.1 (Catch-up).")
                    elif len(lives) > 1 and result == "DISCARDED":
                        output.append(
                            "      [EXPLANATION] SELECTION: Player had multiple passed lives, only one moved."
                        )
                    elif result == "DISCARDED":
                        output.append(
                            "      [EXPLANATION] UNKNOWN: Passed alone but discarded. (Hearts re-check failure?)"
                        )

    with open("turn_by_turn_analysis.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(output))
    print("Turn-by-turn analysis written to turn_by_turn_analysis.txt")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze.py <json_file>")
    else:
        analyze_report(sys.argv[1])
