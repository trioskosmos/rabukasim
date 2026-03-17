import os
import sys

# Force root
root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root not in sys.path:
    sys.path.insert(0, root)

import traceback

import numpy as np
from ai.vector_env import VectorGameState


def diagnostic():
    print(f"--- Engine Diagnostic (Root: {root}) ---")
    try:
        print("Initializing VectorGameState(num_envs=1)...")
        gs = VectorGameState(1)

        print("Resetting Engine...")
        gs.reset()

        print("Initial State:")
        hand = [int(c) for c in gs.batch_hand[0] if c > 0]
        print(f"  Hand: {hand}")
        print(f"  Phase: {gs.batch_global_ctx[0, 8]}")
        print(f"  Turn: {gs.batch_global_ctx[0, 54]}")

        print("\nPerforming 5 random steps...")
        for i in range(5):
            masks = gs.get_action_masks()
            # Pick first legal action
            action = np.zeros(1, dtype=np.int32)
            legal_ids = np.where(masks[0])[0]
            if len(legal_ids) > 0:
                action[0] = legal_ids[min(1, len(legal_ids) - 1)]  # Try to play if possible

            print(f"Step {i} | Action: {action[0]}")
            gs.step(action)

        print("\nEngine diagnostic complete. SUCCESS.")

    except Exception:
        print("\n!!! ENGINE CRASH !!!")
        traceback.print_exc()


if __name__ == "__main__":
    diagnostic()
