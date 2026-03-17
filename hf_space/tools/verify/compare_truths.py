import json


def compare_truths(v1_path, v2_path):
    with open(v1_path, "r", encoding="utf-8") as f:
        v1 = json.load(f)
    with open(v2_path, "r", encoding="utf-8") as f:
        v2 = json.load(f)

    conflicts = []
    matches = 0
    missing_in_v2 = 0

    for cid, c1 in v1.items():
        if cid not in v2:
            missing_in_v2 += 1
            continue

        c2 = v2[cid]
        for i, (ab1, ab2) in enumerate(zip(c1["abilities"], c2["abilities"])):

            def get_cumulative(seq):
                res = {}
                for segment in seq:
                    for d in segment["deltas"]:
                        tag = d["tag"]
                        val = d["value"]
                        # Handle both numbers and flags
                        if isinstance(val, (int, float)):
                            res[tag] = res.get(tag, 0) + val
                        else:
                            res[tag] = val
                return sorted([f"{k}:{v}" for k, v in res.items()])

            d1 = get_cumulative(ab1["sequence"])
            d2 = get_cumulative(ab2["sequence"])

            if d1 == d2:
                matches += 1
            else:
                conflicts.append(
                    {
                        "card_id": cid,
                        "ability_idx": i,
                        "text": ab1["sequence"][0]["text"] if ab1["sequence"] else "N/A",
                        "v1_expected": ab1["sequence"],
                        "v2_actual": ab2["sequence"],
                    }
                )

    print("--- Truth Comparison Summary ---")
    print(f"Total Ability Pairs Checked: {matches + len(conflicts)}")
    print(f"Total Matches: {matches}")
    print(f"Total Conflicts: {len(conflicts)}")
    print(f"Missing in V2: {missing_in_v2}")
    print("--------------------------------")

    # Group conflicts by "Type of error" for easier analysis
    print("\n--- Sample Conflicts ---")
    for conflict in conflicts[:15]:
        print(f"[{conflict['card_id']} Ab{conflict['ability_idx']}] {conflict['text'][:60]}...")
        print(f"  V1 (Exp): {conflict['v1_expected']}")
        print(f"  V2 (Act): {conflict['v2_actual']}")
        print("-" * 20)

    # Save full report
    with open("reports/truth_conflicts.json", "w", encoding="utf-8") as f:
        json.dump(conflicts, f, indent=2, ensure_ascii=False)
    print("\nFull conflict report saved to reports/truth_conflicts.json")


if __name__ == "__main__":
    compare_truths("reports/semantic_truth.json", "reports/semantic_truth_v2.json")
