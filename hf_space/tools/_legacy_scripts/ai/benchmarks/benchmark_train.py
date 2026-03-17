import os
import sys
import time
import warnings
from datetime import datetime

import numpy as np
import torch

# Filter Numba warning
warnings.filterwarnings("ignore", category=RuntimeWarning, message="nopython is set for njit")

# Ensure project root is in path
sys.path.append(os.getcwd())

from ai.vec_env_adapter import VectorEnvAdapter
from sb3_contrib import MaskablePPO
from stable_baselines3.common.callbacks import BaseCallback


class BenchmarkCallback(BaseCallback):
    """
    Logs performance metrics for benchmarking.
    """

    def __init__(self, verbose=0):
        super().__init__(verbose)
        self.collection_times = []
        self.optimization_times = []
        self.rollout_start = 0.0
        self.optimization_start = 0.0
        self.peak_vram = 0.0

    def _on_rollout_start(self) -> None:
        self.rollout_start = time.time()
        # End of optimization (if not first rollout)
        if self.optimization_start > 0:
            self.optimization_times.append(time.time() - self.optimization_start)

    def _on_rollout_end(self) -> None:
        # End of collection
        duration = time.time() - self.rollout_start
        self.collection_times.append(duration)

        # Check VRAM
        if torch.cuda.is_available():
            allocated = torch.cuda.memory_allocated() / 1024**3
            reserved = torch.cuda.memory_reserved() / 1024**3
            current_peak = max(allocated, reserved)
            self.peak_vram = max(self.peak_vram, current_peak)

        self.optimization_start = time.time()

    def _on_step(self) -> bool:
        return True


def main():
    print("========================================================")
    print(" LovecaSim - BENCHMARK MODE                             ")
    print("========================================================")

    # Configuration from Environment Variables
    BATCH_SIZE = int(os.getenv("TRAIN_BATCH_SIZE", "8192"))
    NUM_ENVS = int(os.getenv("TRAIN_ENVS", "1024"))
    N_STEPS = int(os.getenv("TRAIN_N_STEPS", "128"))
    DURATION_SEC = int(os.getenv("BENCH_DURATION_SEC", "45"))
    PROFILE_NAME = os.getenv("BENCH_PROFILE_NAME", "Unknown")

    print(f" [Bench] Profile:   {PROFILE_NAME}")
    print(f" [Bench] Config:    Envs={NUM_ENVS}, Steps={N_STEPS}, Batch={BATCH_SIZE}")

    try:
        # 1. Create Environment
        env = VectorEnvAdapter(num_envs=NUM_ENVS)

        # Warmup
        print(" [Bench] Compiling Numba...")
        env.reset()
        env.step(np.zeros(NUM_ENVS, dtype=np.int32))

        # 2. Create Model
        model = MaskablePPO(
            "MlpPolicy",
            env,
            verbose=1,
            learning_rate=3e-4,
            n_steps=N_STEPS,
            batch_size=BATCH_SIZE,
            n_epochs=2,  # Low epochs for quick benchmarking
            device="cuda" if torch.cuda.is_available() else "cpu",
        )

        # 3. Run Benchmark
        print(f" [Bench] Running training for ~{DURATION_SEC} seconds...")
        callback = BenchmarkCallback()

        # Calculate steps needed for approx duration
        # Assume roughly 1s per update for safety, but we'll limit by wall time mostly if we could
        # SB3 doesn't have time limit, so we set huge steps and rely on manual kill or just fixed steps
        # Let's just run for fixed total timesteps that equate to a few updates
        # 1 update = n_steps * num_envs
        steps_per_update = N_STEPS * NUM_ENVS
        estimated_fps = 50000  # conservative guess
        total_steps = int(estimated_fps * DURATION_SEC)
        # Ensure at least 2 updates
        total_steps = max(total_steps, steps_per_update * 2)

        start_time = time.time()
        model.learn(total_timesteps=total_steps, callback=callback)
        total_time = time.time() - start_time

        # 4. Analyze Results
        avg_collection = np.mean(callback.collection_times) if callback.collection_times else 0
        avg_optim = np.mean(callback.optimization_times) if callback.optimization_times else 0

        # Calculate rates
        collection_fps = (NUM_ENVS * N_STEPS) / avg_collection if avg_collection > 0 else 0
        optim_sps = (NUM_ENVS * N_STEPS) / avg_optim if avg_optim > 0 else 0  # logical steps per sec during optim
        total_sps = total_steps / total_time

        print("-" * 40)
        print(f" [Result] Profile:    {PROFILE_NAME}")
        print(f" [Result] Coll FPS:   {collection_fps:.0f}")
        print(f" [Result] Optim SPS:  {optim_sps:.0f}")
        print(f" [Result] Total SPS:  {total_sps:.0f}")
        print(f" [Result] VRAM Peak:  {callback.peak_vram:.2f} GB")
        print("-" * 40)

        # 5. Save to CSV
        results_file = "benchmark_results.csv"
        file_exists = os.path.isfile(results_file)

        with open(results_file, "a") as f:
            if not file_exists:
                f.write("Timestamp,Profile,Envs,Steps,Batch,CollFPS,OptimSPS,TotalSPS,PeakVRAM_GB,Status\n")

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(
                f"{timestamp},{PROFILE_NAME},{NUM_ENVS},{N_STEPS},{BATCH_SIZE},{collection_fps:.0f},{optim_sps:.0f},{total_sps:.0f},{callback.peak_vram:.2f},SUCCESS\n"
            )

    except Exception as e:
        print(f" [Error] Benchmark failed: {e}")
        # Log failure
        with open("benchmark_results.csv", "a") as f:
            if not os.path.isfile("benchmark_results.csv"):
                f.write("Timestamp,Profile,Envs,Steps,Batch,CollFPS,OptimSPS,TotalSPS,PeakVRAM_GB,Status\n")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{timestamp},{PROFILE_NAME},{NUM_ENVS},{N_STEPS},{BATCH_SIZE},0,0,0,0,FAILED_{e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
