import argparse
import glob

import numpy as np


def analyze_distribution(pattern):
    files = glob.glob(pattern)
    if not files:
        print(f"No files found for {pattern}")
        return

    total_samples = 0
    action_counts = {}

    print(f"Analyzing {len(files)} files...")
    for f in files[:20]:  # Check first 20 chunks for quick insight
        data = np.load(f)
        policies = data["policies"]

        # policies is [N, 2000]
        # Get argmax for each sample
        best_actions = np.argmax(policies, axis=1)

        total_samples += len(best_actions)
        unique, counts = np.unique(best_actions, return_counts=True)
        for a, c in zip(unique, counts):
            action_counts[a] = action_counts.get(a, 0) + c

    print(f"\nTotal Samples checked: {total_samples}")
    sorted_actions = sorted(action_counts.items(), key=lambda x: x[1], reverse=True)

    print("\nTop 10 Actions:")
    for action, count in sorted_actions[:10]:
        percentage = (count / total_samples) * 100
        print(f"Action {action:4}: {count:6} samples ({percentage:5.1f}%)")

    # Specifically check Action 0 (End Phase)
    pass_count = action_counts.get(0, 0)
    pass_perc = (pass_count / total_samples) * 100
    print(f"\nAction 0 (Pass/End): {pass_perc:.1f}%")

    # Check "tactical" actions (non-zero)
    tactical_count = total_samples - pass_count
    tactical_perc = (tactical_count / total_samples) * 100
    print(f"Tactical Actions:   {tactical_perc:.1f}%")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, default="ai/data/self_play_0_chunk_*.npz")
    args = parser.parse_args()
    analyze_distribution(args.data)
