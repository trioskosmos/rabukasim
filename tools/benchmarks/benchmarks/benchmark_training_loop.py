import os
import sys
import time
import warnings

# Filter warnings
warnings.filterwarnings("ignore")

# Add project root to path
sys.path.append(os.getcwd())

from ai.vec_env_adapter import VectorEnvAdapter
from sb3_contrib import MaskablePPO


def benchmark_training():
    print("========================================================")
    print(" BENCHMARKING TRAINING LOOP (VectorEnv + PPO)")
    print("========================================================")

    # Config matching "Balanced/High" profile
    NUM_ENVS = 1024
    BATCH_SIZE = 8192
    N_STEPS = 128  # Short rollout for benchmark speed
    TOTAL_STEPS = NUM_ENVS * N_STEPS * 2  # 2 Updates

    print(f" [Config] Num Envs:   {NUM_ENVS}")
    print(f" [Config] Batch Size: {BATCH_SIZE}")
    print(" [Config] Device:     Determined by PPO")

    # 1. Init Env
    print("\n [Init] Creating VectorEnvAdapter...")
    start_init = time.time()
    env = VectorEnvAdapter(num_envs=NUM_ENVS)
    print(f" [Init] Env Created in {time.time() - start_init:.2f}s")

    # 2. Init Model
    print(" [Init] Creating PPO Model...")
    model = MaskablePPO(
        "MlpPolicy", env, verbose=1, learning_rate=3e-4, n_steps=N_STEPS, batch_size=BATCH_SIZE, device="auto"
    )
    print(f" [Init] Model Device: {model.device}")

    # 3. Benchmark Loop
    print(f"\n [Bench] Running {TOTAL_STEPS:,} steps (2 Rollout Cycles)...")
    start_train = time.time()

    model.learn(total_timesteps=TOTAL_STEPS)

    end_train = time.time()
    duration = end_train - start_train
    sps = TOTAL_STEPS / duration

    print("\n" + "=" * 40)
    print(" TRAINING LOOP RESULTS")
    print("=" * 40)
    print(f" Total Steps: {TOTAL_STEPS:,}")
    print(f" Time Taken:  {duration:.2f} seconds")
    print(f" Throughput:  {sps:,.0f} steps/sec")
    print("=" * 40)

    env.close()


if __name__ == "__main__":
    benchmark_training()
