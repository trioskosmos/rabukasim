import glob

import numpy as np

files = glob.glob("ai/data/alphazero_nightly_chunk_*.npz")
all_actions = []

print("Analyzing action distribution...")
for f in sorted(files[:5]):  # Check first 5 chunks for speed
    data = np.load(f)
    policies = data["policies"]
    # Get the argmax (the action the MCTS preferred)
    best_actions = np.argmax(policies, axis=1)
    all_actions.extend(best_actions)

all_actions = np.array(all_actions)
total = len(all_actions)
unique, counts = np.unique(all_actions, return_counts=True)
dist = dict(zip(unique, counts))

print(f"\nTotal Samples Analyzed: {total}")
print(f"Action 0 (Pass) Frequency: {dist.get(0, 0) / total * 100:.1f}%")
print(f"Unique Non-Zero Actions in Data: {len(unique) - (1 if 0 in unique else 0)}")

# Top 5 actions
top_indices = np.argsort(counts)[::-1][:6]
print("\nTop 5 Actions by Frequency:")
for i in top_indices:
    print(f"  Action {unique[i]:>4}: {counts[i] / total * 100:>5.1f}%")
