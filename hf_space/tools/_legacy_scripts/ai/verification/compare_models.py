import time

import torch
from ai.vec_env_adapter import VectorEnvAdapter as NewEnv
from ai.vec_env_adapter_legacy import VectorEnvAdapter as LegacyEnv
from sb3_contrib import MaskablePPO


def evaluate_model(env_class, model_path, name, num_games=1000):
    print(f"\n--- Evaluating {name} ---")
    try:
        # Load Model first to get its obs_dim
        model = MaskablePPO.load(model_path, device="cuda" if torch.cuda.is_available() else "cpu")
        obs_dim = model.observation_space.shape[0]
        print(f"Model loaded from {model_path} (Obs Dim: {obs_dim})")

        # 1. Setup Env with matching obs_dim
        # We need to tell the adapter what dimension to use
        num_envs = 100
        env = env_class(num_envs=num_envs, observation_space_dim=obs_dim)

        # Stats
        total_wins = 0
        total_scores = 0
        games_played = 0

        obs = env.reset()  # (N, dim)

        start_time = time.time()

        while games_played < num_games:
            # Get Action Masks
            # Legacy might not have get_action_masks?
            # Check if env has it.
            if hasattr(env, "get_action_masks"):
                action_masks = env.get_action_masks()
                # SB3 predict needs valid masks if deterministic
                actions, _ = model.predict(obs, action_masks=action_masks, deterministic=True)
            else:
                # Fallback for really old legacy if no mask (unlikely, I added masking earlier)
                # But let's assume it has it or we just predict without mask validation (risky).
                # Actually, MaskablePPO REQUIRES masks.
                # If legacy env lacks get_action_masks, this will fail.
                # Let's hope it has it (it was added recently).
                # If not, we can't eval easily with MaskablePPO.
                print("Warning: Env missing get_action_masks. Using raw predict.")
                actions, _ = model.predict(obs, deterministic=True)

            # Step
            obs, rewards, dones, infos = env.step(actions)

            # Count wins/scores
            # VectorEnv returns batch_scores in 'infos' or we track locally?
            # 'rewards' are delta based.
            # We can use 'env.batch_scores' directly if accessible.

            # Check for dones
            for i in range(num_envs):
                if dones[i]:
                    # Win check: Score >= 10?
                    # VectorEnv logic: if batch_scores[i] >= 10: win
                    # We can peek at internal state or rely on reward?
                    # Reward usually has +5 bonus on win.
                    if env.batch_scores[i] >= 10 and env.batch_scores[i] > env.opp_scores[i]:
                        total_wins += 1

                    total_scores += env.batch_scores[i]
                    games_played += 1

                    if games_played >= num_games:
                        break

        elapsed = time.time() - start_time
        avg_score = total_scores / games_played
        win_rate = total_wins / games_played * 100.0

        print(f"Results for {name}:")
        print(f"  Games: {games_played}")
        print(f"  Win Rate: {win_rate:.1f}%")
        print(f"  Avg Score: {avg_score:.2f}")
        print(f"  Time: {elapsed:.1f}s ({games_played / elapsed:.1f} fps)")

        return win_rate, avg_score

    except Exception as e:
        print(f"Failed to evaluate {name}: {e}")
        return 0, 0


if __name__ == "__main__":
    # USER: Set paths here
    LEGACY_MODEL = "checkpoints/legacy_best_model.zip"  # Replace with actual
    NEW_MODEL = "checkpoints/best_model.zip"

    # Check for legacy file existence
    import os

    if not os.path.exists("ai/vector_env_legacy.py"):
        print("Error: ai/vector_env_legacy.py not found. Restore it first.")
        exit()

    print("Comparing Models...")

    # 1. New Model
    if os.path.exists(NEW_MODEL):
        evaluate_model(NewEnv, NEW_MODEL, "New Model (2048-dim)")
    else:
        print(f"New model not found at {NEW_MODEL}")

    # 2. Legacy Model
    if os.path.exists(LEGACY_MODEL):
        evaluate_model(LegacyEnv, LEGACY_MODEL, "Legacy Model (320-dim)")
    else:
        print(f"Legacy model not found at {LEGACY_MODEL}")
