import os
import sys

import numpy as np

# Ensure path is correct
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.vector_env import VectorGameState


def trace_game():
    print("=" * 60)
    print(" NUMBA ENGINE DETAILED TRACE ")
    print("=" * 60)

    # 1env, compressed for readability
    os.environ["OBS_MODE"] = "COMPRESSED"
    env = VectorGameState(num_envs=1)
    env.reset()

    # Check Order
    is_second = env.batch_global_ctx[0, 10]
    print(f"Agent Order: {'P2 (Second)' if is_second else 'P1 (First)'}")
    print(f"Initial Phase: {env.batch_global_ctx[0, 8]}")
    print(f"Initial Hand: {env.batch_global_ctx[0, 3]} cards")
    print(f"Initial Energy: {env.batch_global_ctx[0, 5]}")

    done = False
    turn = 1

    # Run through the game with a simpler "Play First Legal Action" logic
    # but specifically looking for Turn 2+ and Energy changes.

    step_count = 0
    while not done and step_count < 200:
        step_count += 1
        mask = env.get_action_masks()[0]
        legal = np.where(mask == 1)[0]

        ph = env.batch_global_ctx[0, 8]

        # LOGIC:
        # If in Mulligan (-1 or 0), after 5 steps force action 0 (Pass)
        # Otherwise pick random legal non-zero action if possible
        if ph <= 0:
            if step_count % 5 == 0:
                action = 0
            else:
                action = np.random.choice(legal)
        else:
            if len(legal) > 1:
                # Avoid passing early in main phase to see plays
                moves = legal[legal != 0]
                action = np.random.choice(moves)
            else:
                action = legal[0]

        prev_phase = env.batch_global_ctx[0, 8]
        prev_energy = env.batch_global_ctx[0, 5]
        prev_scores = env.batch_scores[0]

        obs, rewards, dones, infos = env.step(np.array([action], dtype=np.int32))

        current_phase = env.batch_global_ctx[0, 8]
        current_energy = env.batch_global_ctx[0, 5]
        current_scores = env.batch_scores[0]
        current_turn = env.batch_global_ctx[0, 54]

        # LOG INTERESTING CHANGES
        print(f"[Step {step_count:03}] Action: {action:3}")

        if current_turn > turn:
            print(f" >>> TURN TRANSITION: {turn} -> {current_turn} <<<")
            # Verify Turn 2 resets (No cards should be tapped or 'played this turn')
            # Check indices 120-125 (mull flags) too if relevant, but Tapped is key.
            tapped_sum = np.sum(env.batch_tapped[0])
            print(f" [Verify] Turn {current_turn} Start Tapped Sum: {tapped_sum} (Expected 0)")
            turn = current_turn

        if current_phase != prev_phase:
            print(f" [Phase] {prev_phase} -> {current_phase}")

        if current_energy != prev_energy:
            print(f" [Energy] {prev_energy} -> {current_energy}")

        if current_scores != prev_scores:
            print(f" [Score] {prev_scores} -> {current_scores} | REWARD: {rewards[0]}")

        if rewards[0] != -0.05 and not np.isclose(rewards[0], -0.05):
            print(f" [Reward] Event Reward: {rewards[0]:.2f}")

        done = dones[0]

    print("=" * 60)
    print(" TRACE COMPLETE ")
    print(f"Final Reward: {rewards[0]}")
    print("=" * 60)


if __name__ == "__main__":
    trace_game()
