import os
import sys

import numpy as np

# Ensure root is in path
sys.path.append(os.getcwd())

from ai.vector_env import VectorGameState


def check_indices_long():
    print("=== Checking Indices Long Run ===")
    gs = VectorGameState(num_envs=1)
    gs.reset()

    for step in range(100):
        # Get Mask
        masks = gs.get_action_masks()[0]
        legal = np.where(masks)[0]
        action = np.random.choice(legal)

        ctx_pre = gs.batch_global_ctx[0].copy()
        obs, rewards, dones, infos = gs.step(np.array([action], dtype=np.int32))

        # Log if score > 0
        if gs.batch_scores[0] > 0 or dones[0]:
            print(
                f"[Step {step}] Action: {action}, Score: {gs.batch_scores[0]}, Opp: {gs.opp_scores[0]}, Done: {dones[0]}, Ph: {gs.batch_global_ctx[0, 8]}"
            )
            if dones[0]:
                print(f"TERMINAL at Step {step}. DK: {gs.batch_global_ctx[0, 6]} (Before: {ctx_pre[6]})")
                # Reset counts
                if gs.batch_scores[0] < 3 and gs.opp_scores[0] < 3 and gs.batch_global_ctx[0, 6] > 0:
                    print("!!! ANOMALY DETECTED !!! Score 0 but Done=True")
                break


if __name__ == "__main__":
    check_indices_long()
