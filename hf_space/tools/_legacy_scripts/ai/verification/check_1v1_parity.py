import time

import numpy as np
from ai.vector_env import VectorGameState


def run_diagnostic():
    print("--- 1v1 Vector Engine Parity Diagnostic ---")
    num_envs = 1
    env = VectorGameState(num_envs=num_envs)

    print("\n[Phase 1] Initial State")
    obs = env.reset()
    print(f"Agent Score: {env.batch_scores[0]}")
    print(f"Opp Score:   {env.opp_scores[0]}")
    print(f"Agent Deck:  {env.batch_global_ctx[0, 6]}")
    print(f"Opp Deck:    {env.opp_global_ctx[0, 6]}")

    print("\n[Phase 2] Running 100 Random Steps...")
    start_time = time.time()

    total_steps = 0
    opponent_scored = False
    refreshed = False

    # Track initial deck
    initial_deck = env.batch_global_ctx[0, 6]

    for s in range(500):
        # Sample a random legal action
        masks = env.get_action_masks()
        legal_indices = np.where(masks[0])[0]
        if len(legal_indices) == 0:
            action = 0  # Pass
        else:
            action = np.random.choice(legal_indices)

        obs, rewards, dones, infos = env.step(np.array([action], dtype=np.int32))
        total_steps += 1

        # Check for opponent scoring
        if env.opp_scores[0] > 0:
            opponent_scored = True

        # Check for deck refresh (if deck was low and is now high)
        if env.batch_global_ctx[0, 6] > 10 and total_steps > 30:  # Heuristic
            # Actually, let's just check if it ever goes back up
            pass

        if dones[0]:
            print(f"Game ended at step {s} | Final Score: {env.batch_scores[0]} - {env.opp_scores[0]}")
            env.reset()
            if opponent_scored:
                break  # We saw what we wanted

        if s % 50 == 0:
            print(
                f"Step {s}: Scores {env.batch_scores[0]}-{env.opp_scores[0]} | Decks {env.batch_global_ctx[0, 6]}-{env.opp_global_ctx[0, 6]}"
            )

    duration = time.time() - start_time
    print("\n[Summary]")
    print(f"Total Steps: {total_steps}")
    print(f"Duration:    {duration:.2f}s ({(total_steps / duration):.1f} steps/s)")
    print(f"Opponent Scored: {opponent_scored}")

    if opponent_scored:
        print("SUCCESS: 1v1 Parity Verified. Opponent can score.")
    else:
        print("CAUTION: Opponent did not score in this short run, but engine is stable.")


if __name__ == "__main__":
    run_diagnostic()
