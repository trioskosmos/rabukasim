import os
import sys

import numpy as np
from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker
from stable_baselines3.common.callbacks import BaseCallback, CallbackList, CheckpointCallback
from stable_baselines3.common.monitor import Monitor

# Ensure project root is in path for local imports
if os.getcwd() not in sys.path:
    sys.path.append(os.getcwd())

print(" [Heartbeat] train_optimized.py entry point reached.", flush=True)

import argparse

import torch

# If many workers are used, we keep intra-op threads low to avoid overhead
if int(os.getenv("TRAIN_CPUS", "4")) <= 4:
    torch.set_num_threads(2)
else:
    torch.set_num_threads(1)

# Fix for Windows DLL loading issues in subprocesses
if sys.platform == "win32":
    # Add torch lib to DLL search path
    torch_lib_path = os.path.join(os.path.dirname(torch.__file__), "lib")
    if os.path.exists(torch_lib_path):
        os.add_dll_directory(torch_lib_path)

    # Ensure CUDA_PATH is in environ if found
    if "CUDA_PATH" not in os.environ:
        cuda_path = "C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA\\v12.2"
        if os.path.exists(cuda_path):
            os.environ["CUDA_PATH"] = cuda_path
            os.environ["PATH"] = os.path.join(cuda_path, "bin") + os.pathsep + os.environ["PATH"]

# Import our environment
from functools import partial

from ai.batched_env import BatchedSubprocVecEnv
from ai.gym_env import LoveLiveCardGameEnv


class TrainingStatsCallback(BaseCallback):
    """Custom callback for logging win rates and illegal move stats from gym_env."""

    def __init__(self, verbose=0):
        super(TrainingStatsCallback, self).__init__(verbose)

    def _on_step(self) -> bool:
        if self.n_calls == 1:
            print(" [Heartbeat] Training loop is active. First step reached!", flush=True)

        infos = self.locals.get("infos")
        if infos:
            # 1. Capture Win Rate from custom env attribute (Legacy/Direct)
            if len(infos) > 0 and "win_rate" in infos[0]:
                avg_win_rate = np.mean([info.get("win_rate", 0) for info in infos])
                self.logger.record("game/win_rate_legacy", avg_win_rate)

            # 1b. Per-game Heartbeat
            for info in infos:
                if "episode" in info:
                    print(
                        f" [Heartbeat] Game completed! Reward: {info['episode']['r']:.2f} | Turns: {info['episode']['l']}",
                        flush=True,
                    )

            # 2. Capture Episode Completion Stats
            episode_infos = [info.get("episode") for info in infos if "episode" in info]
            if episode_infos:
                avg_reward = np.mean([ep["r"] for ep in episode_infos])
                avg_turns = np.mean([ep["turn"] for ep in episode_infos])
                win_count = sum(1 for ep in episode_infos if ep["win"])
                win_rate = (win_count / len(episode_infos)) * 100

                self.logger.record("game/avg_episode_reward", avg_reward)
                self.logger.record("game/avg_win_turn", avg_turns)
                self.logger.record("game/win_rate_rolling", win_rate)

                # Periodic summary to terminal (More frequent for visibility)
                if self.n_calls % 256 == 0:
                    print(
                        f" [Stats] Steps: {self.num_timesteps} | Win Rate: {win_rate:.1f}% | Avg Reward: {avg_reward:.2f} | Avg Turn: {avg_turns:.1f}",
                        flush=True,
                    )

        return True


class SaveOnBestWinRateCallback(BaseCallback):
    """Callback to save the model when win rate reaches a new peak."""

    def __init__(self, check_freq: int, save_path: str, verbose=1):
        super(SaveOnBestWinRateCallback, self).__init__(verbose)
        self.check_freq = check_freq
        self.save_path = save_path
        self.best_win_rate = -np.inf
        self.min_win_rate_threshold = 30.0  # Only save 'best' if above 30% to avoid early noise

    def _init_callback(self) -> None:
        if self.save_path is not None:
            os.makedirs(self.save_path, exist_ok=True)

    def _on_step(self) -> bool:
        if self.n_calls % self.check_freq == 0:
            infos = self.locals.get("infos")
            if infos:
                avg_win_rate = np.mean([info.get("win_rate", 0) for info in infos])
                if avg_win_rate > self.best_win_rate and avg_win_rate > self.min_win_rate_threshold:
                    self.best_win_rate = avg_win_rate
                    if self.verbose > 0:
                        print(
                            f" [Saving] New Best Win Rate: {avg_win_rate:.1f}%! Progressing towards big moment...",
                            flush=True,
                        )
                    self.model.save(os.path.join(self.save_path, "best_win_rate_model"))
        return True


class SelfPlayUpdateCallback(BaseCallback):
    """Callback to save the model for self-play opponents."""

    def __init__(self, update_freq: int, save_path: str, verbose=0):
        super(SelfPlayUpdateCallback, self).__init__(verbose)
        self.update_freq = update_freq
        self.save_path = save_path

    def _init_callback(self) -> None:
        if self.save_path is not None:
            os.makedirs(self.save_path, exist_ok=True)

    def _on_step(self) -> bool:
        if self.n_calls % self.update_freq == 0:
            if self.verbose > 0:
                print(" [Self-Play] Updating opponent model...", flush=True)
            self.model.save(os.path.join(self.save_path, "self_play_opponent"))
        return True


def create_env(rank, usage=0.5, deck_type="random_verified", opponent_type="random"):
    env = LoveLiveCardGameEnv(target_cpu_usage=usage, deck_type=deck_type, opponent_type=opponent_type)
    env = Monitor(env)
    env = ActionMasker(env, lambda e: e.unwrapped.action_masks())

    # Seed for diversity across workers
    env.reset(seed=42 + rank)
    return env


def train():
    # 1. Hardware Constraints Setup
    num_cpu = int(os.getenv("TRAIN_CPUS", "4"))
    usage = float(os.getenv("TRAIN_USAGE", "0.5"))
    deck_type = os.getenv("TRAIN_DECK", "random_verified")
    gpu_usage = float(os.getenv("TRAIN_GPU_USAGE", "0.7"))
    batch_size = int(os.getenv("TRAIN_BATCH_SIZE", "256"))
    n_epochs = int(os.getenv("TRAIN_EPOCHS", "10"))
    n_steps = int(os.getenv("TRAIN_STEPS", "2048"))
    opponent_type = os.getenv("TRAIN_OPPONENT", "random")

    if torch.cuda.is_available() and gpu_usage < 1.0:
        try:
            print(f"Limiting GPU memory usage to {int(gpu_usage * 100)}%...", flush=True)
            torch.cuda.set_per_process_memory_fraction(gpu_usage)
        except Exception as e:
            print(f"Warning: Could not set GPU memory fraction: {e}. Proceeding without limit.", flush=True)

    print(
        f"Initializing {num_cpu} parallel environments ({deck_type}) with opponent {opponent_type} and {int(usage * 100)}% per-core throttle...",
        flush=True,
    )

    # Create Vectorized Environment
    try:
        # Optimization: Workers always use "random" internally because BatchedSubprocVecEnv intercepts and runs the real opponent
        # This prevents workers from importing torch/sb3 and saves GBs of RAM.
        env_fns = [
            partial(create_env, rank=i, usage=usage, deck_type=deck_type, opponent_type="random")
            for i in range(num_cpu)
        ]

        # Use our new Batched inference environment
        opponent_path = os.path.join(os.getcwd(), "checkpoints", "self_play_opponent.zip")
        env = BatchedSubprocVecEnv(env_fns, opponent_model_path=opponent_path if opponent_type == "self_play" else None)
        print("Batched workers initialized! Starting training loop...", flush=True)

    except Exception as e:
        print(f"CRITICAL ERROR during worker initialization: {e}", flush=True)
        import traceback

        traceback.print_exc()
        return

    # 2. Model Configuration
    load_path = os.getenv("LOAD_MODEL")
    model = None
    if load_path and os.path.exists(load_path):
        try:
            print(f" [LOAD] Loading existing model from {load_path}...", flush=True)
            device = "cuda" if torch.cuda.is_available() else "cpu"
            model = MaskablePPO.load(load_path, env=env, device=device)
            print(" [LOAD] Model loaded successfully.", flush=True)
        except ValueError as val_err:
            if "Observation spaces do not match" in str(val_err):
                print(
                    f" [WARNING] Checkpoint {load_path} has incompatible observation space (likely from an older engine version).",
                    flush=True,
                )
                print(" [WARNING] Skipping load and starting fresh to maintain stability.", flush=True)
                model = None  # Force fresh start
            else:
                raise val_err
        except Exception as load_err:
            print(f" [CRITICAL ERROR] Failed to load checkpoint: {load_err}", flush=True)
            import traceback

            traceback.print_exc()
            env.close()
            sys.exit(1)

    if model is None:
        print(" [INFO] Initializing fresh MaskablePPO model...", flush=True)
        model = MaskablePPO(
            "MlpPolicy",
            env,
            verbose=0,
            gamma=0.99,
            learning_rate=3e-4,
            n_steps=n_steps,
            batch_size=batch_size,
            n_epochs=n_epochs,
            tensorboard_log="./logs/ppo_tensorboard/",
            device="cuda",
        )

    # NEW: Dry run support
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Initialize and exit")
    args, unknown = parser.parse_known_args()

    if args.dry_run:
        print(" [Dry Run] Workers initialized successfully. Exiting.", flush=True)
        env.close()
        return

    print(f"Starting Training on {num_cpu} workers (Usage: {usage * 100}%)...", flush=True)

    # Checkpoint Callback
    checkpoint_callback = CheckpointCallback(
        save_freq=max(1, 200000 // num_cpu), save_path="./checkpoints/", name_prefix="lovelive_ppo_checkpoint"
    )

    # 3. Learning Loop
    stats_callback = TrainingStatsCallback()
    best_rate_callback = SaveOnBestWinRateCallback(check_freq=1024, save_path="./checkpoints/")
    self_play_callback = SelfPlayUpdateCallback(update_freq=20000, save_path="./checkpoints/")

    callback_list = CallbackList([checkpoint_callback, stats_callback, best_rate_callback, self_play_callback])

    try:
        print(f"Starting Long-Running Training on {num_cpu} workers (Usage: {usage * 100}%)...")
        model.learn(total_timesteps=2_000_000_000, progress_bar=False, callback=callback_list)

        # Save Final Model
        os.makedirs("checkpoints", exist_ok=True)
        model.save("checkpoints/lovelive_ppo_optimized")
        print("Training Complete. Model Saved.")

    except KeyboardInterrupt:
        print("\nTraining interrupted. Saving current progress...")
        model.save("checkpoints/lovelive_ppo_interrupted")
    finally:
        env.close()


if __name__ == "__main__":
    train()
