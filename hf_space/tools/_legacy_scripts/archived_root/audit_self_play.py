import glob

import numpy as np

files = glob.glob("ai/data/self_play_*.npz")
for f in files:
    data = np.load(f)
    print(f"File: {f}")
    print(f"Samples: {len(data['states'])}")

    winners = data["winners"]
    # Check distribution: -1.0 = loss, 0.0 = draw, 1.0 = win
    print(f"Value mean: {np.mean(winners):.3f}")
    print(f"Value std: {np.std(winners):.3f}")
    print(f"Min/Max: {np.min(winners):.2f} / {np.max(winners):.2f}")

    # Histogram
    wins = np.sum(winners == 1.0)
    losses = np.sum(winners == -1.0)
    draws = np.sum(winners == 0.0)
    print(f"Distribution: Wins={wins}, Losses={losses}, Draws={draws}")

    # Check policy distribution - is it just all Pass?
    policies = data["policies"]
    action_0_mean = np.mean(policies[:, 0])
    print(f"Policy Action 0 (Pass) mean prob: {action_0_mean:.3f}")
    print()
