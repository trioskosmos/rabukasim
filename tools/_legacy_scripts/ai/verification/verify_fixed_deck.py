import os
import sys

import numpy as np

# Add project root to path
sys.path.append(os.getcwd())

os.environ["USE_FIXED_DECK"] = "ai/vanilla_deck.md"
os.environ["OBS_MODE"] = "COMPRESSED"

from ai.vector_env import VectorGameState


def verify_fixed_deck():
    print("Initializing VectorGameState with USE_FIXED_DECK=ai/vanilla_deck.md")
    env = VectorGameState(num_envs=1)

    print(f"Ability Member IDs: {len(env.ability_member_ids)}")
    print(f"Ability Live IDs: {len(env.ability_live_ids)}")

    # Check counts
    assert len(env.ability_member_ids) == 48, f"Expected 48 members, got {len(env.ability_member_ids)}"
    assert len(env.ability_live_ids) == 12, f"Expected 12 lives, got {len(env.ability_live_ids)}"

    # Check uniqueness (should be 12 unique members and 4 unique lives based on vanilla_deck.md)
    unique_members = np.unique(env.ability_member_ids)
    unique_lives = np.unique(env.ability_live_ids)

    print(f"Unique Members: {len(unique_members)}")
    print(f"Unique Lives: {len(unique_lives)}")

    assert len(unique_members) == 12, f"Expected 12 unique members, got {len(unique_members)}"
    assert len(unique_lives) == 4, f"Expected 4 unique lives, got {len(unique_lives)}"

    print("Verification Successful!")


if __name__ == "__main__":
    verify_fixed_deck()
