import os
import sys

import numpy as np

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def inspect_observation(obs_tensor):
    """
    Decodes and prints a human-readable summary of an IMAX observation tensor.
    """
    print("=== AI OBSERVATION INSPECTOR (IMAX) ===")

    # Metadata
    print(f"Phase Indicators (Indices 5-11): {obs_tensor[5:12]}")
    print(f"Turn Number (Index 6): {obs_tensor[6] * 20.0}")

    # Global Scores
    avg_score_scale = 9.0
    print(f"My Score (Index 8000): {obs_tensor[8000] * avg_score_scale}")
    print(f"Opp Score (Index 8001): {obs_tensor[8001] * avg_score_scale}")

    # Card Counting (Indices 63-69)
    print("\n--- Deck Heart Distribution (Pro Vision) ---")
    colors = ["Pink", "Red", "Yellow", "Green", "Blue", "Purple", "Any"]
    for i, color in enumerate(colors):
        print(f"  {color:7}: {obs_tensor[63 + i]:.1%}")

    # Energy Projection (Index 80)
    print(f"\nNext Turn Energy Projection (Index 80): {obs_tensor[80] * 12.0:.1f}")

    # My Universe (Cards)
    STRIDE = 80
    MY_UNIVERSE_START = 100
    print("\n--- My Universe (Entities) ---")
    for i in range(10):  # Show first 10 for brevity
        base = MY_UNIVERSE_START + i * STRIDE
        if obs_tensor[base] > 0.5:  # Exists
            cid = int(obs_tensor[base + 1] * 2000.0)
            loc = obs_tensor[base + 79]
            loc_str = "Hand" if loc == 1.0 else ("Stage" if loc >= 2.0 and loc < 3.0 else "Live")
            print(
                f" Slot {i}: Card ID {cid:4} | Location {loc_str:6} | Cost {obs_tensor[base + 3] * 10.0:2.1f} | Tapped {obs_tensor[base + 2]}"
            )

    print("\n--- Opponent Stage ---")
    OPP_START = 6500
    for i in range(3):
        base = OPP_START + i * STRIDE
        if obs_tensor[base] > 0.5:
            cid = int(obs_tensor[base + 1] * 2000.0)
            print(f" Slot {i}: Card ID {cid:4} | Tapped {obs_tensor[base + 2]}")


if __name__ == "__main__":
    # Smoke test with a dummy vector
    dummy_obs = np.zeros(8192, dtype=np.float32)
    # Mock some data
    dummy_obs[5 + 4] = 1.0  # Main Phase
    dummy_obs[6] = 0.5  # Turn 10
    dummy_obs[100] = 1.0  # Card 1 exists
    dummy_obs[101] = 123 / 2000.0  # Card 123
    dummy_obs[179] = 1.0  # Hand

    inspect_observation(dummy_obs)
