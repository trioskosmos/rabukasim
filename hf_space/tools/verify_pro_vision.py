import os
import sys

# Add project root
sys.path.append(os.getcwd())

from ai.environments.vector_env import VectorGameState


def verify_pro_vision():
    # Force IMAX mode as it's the most robust for this check
    os.environ["OBS_MODE"] = "IMAX"
    env = VectorGameState(num_envs=1)
    obs = env.reset()

    obs_tensor = obs[0]

    print("\n=== PRO VISION VERIFICATION REPORT ===")

    # 1. Energy Projection
    # Index 80 in IMAX/STANDARD
    energy_proj = obs_tensor[80] * 12.0
    print(f"Energy Projection (Index 80): {energy_proj:.1f}")

    # 2. Heart Distribution
    # Indices 63-69
    colors = ["Pink", "Red", "Yellow", "Green", "Blue", "Purple", "Any"]
    total_found = 0.0
    print("\nDeck Heart Distribution (Indices 63-69):")
    for i, color in enumerate(colors):
        val = obs_tensor[63 + i]
        print(f"  {color:7}: {val:.1%}")
        total_found += val

    print(f"\nTotal heart sum: {total_found:.1%}")

    # 3. Metadata sanity checks
    print("\nMetadata Check:")
    print(f"  Phase Flag (Index 4/5): {obs_tensor[4]}/{obs_tensor[5]}")
    print(f"  Turn Scalar (Index 6): {obs_tensor[6]:.2f}")

    if energy_proj > 0 or total_found > 0:
        print("\n[SUCCESS] Pro Vision data detected in observation tensor!")
    else:
        print("\n[FAILURE] Pro Vision data is all zeros. Check kernel integration.")


if __name__ == "__main__":
    verify_pro_vision()
