import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai.vector_env import compute_action_masks


def test_mask():
    num_envs = 1
    batch_hand = np.zeros((1, 60), dtype=np.int32)
    batch_hand[0, 0] = 100  # Card ID 100
    batch_stage = np.full((1, 3), -1, dtype=np.int32)
    batch_tapped = np.zeros((1, 16), dtype=np.bool_)
    batch_global_ctx = np.zeros((1, 128), dtype=np.int32)
    batch_global_ctx[0, 8] = 3  # Phase
    batch_global_ctx[0, 9] = 3  # EC
    batch_live = np.zeros((1, 12), dtype=np.int32)
    card_stats = np.zeros((2000, 80), dtype=np.float32)
    card_stats[100, 0] = 0.0  # Cost 0

    masks = compute_action_masks(
        num_envs, batch_hand, batch_stage, batch_tapped, batch_global_ctx, batch_live, card_stats
    )

    actions = np.where(masks[0])[0]
    print(f"Legal Actions: {actions}")
    if 3 in actions:
        print("Slot 2 is WORKING!")
    else:
        print("Slot 2 is BLOCKED!")


if __name__ == "__main__":
    test_mask()
