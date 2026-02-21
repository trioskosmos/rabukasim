import time

import numpy as np
from ai.vector_env import VectorGameState


def benchmark_performance():
    NUM_ENVS = 64
    STEPS = 1000
    WARMUP = 10

    print("--- High-Performance Vector Engine Benchmark ---")
    print(f"Configuration: {NUM_ENVS} Environments, {STEPS} Steps")

    env = VectorGameState(num_envs=NUM_ENVS)
    env.reset()

    print("\n[Warmup] Compiling Numba kernels...")
    # Run once to trigger JIT
    actions = np.zeros(NUM_ENVS, dtype=np.int32)
    start_warm = time.time()
    for _ in range(WARMUP):
        env.step(actions)
    print(f"Warmup complete in {time.time() - start_warm:.2f}s")

    print(f"\n[Benchmark] Running {STEPS} vectorized steps...")
    start_time = time.time()

    total_steps = 0
    games_finished = 0
    t0 = time.time()

    for s in range(STEPS):
        # Random valid actions (simulated by mask computation overhead + random choice)
        # To measure pure engine speed, we can just pass random ints or zeros
        # But let's do a realistic "random policy" overhead equivalent
        masks = env.get_action_masks()  # (N, 2000)

        # Fast random action selection provided by checking masks is slow in python loop
        # For pure engine throughput, let's just use action 0 (Pass) or random
        # But wait, we want to prove it works fast *with* logic.

        # Let's just generate random actions [0, 450]
        actions = np.random.randint(0, 450, size=NUM_ENVS, dtype=np.int32)

        obs, rewards, dones, infos = env.step(actions)
        total_steps += NUM_ENVS
        games_finished += np.sum(dones)

        if s % 100 == 0 and s > 0:
            dt = time.time() - t0
            fps = (100 * NUM_ENVS) / dt
            print(f" Step {s}: {fps:.1f} steps/s | Games Finished: {games_finished}")
            t0 = time.time()

    total_duration = time.time() - start_time
    fps = total_steps / total_duration

    print("\n[Results]")
    print(f"Total Steps: {total_steps}")
    print(f"Duration:    {total_duration:.2f}s")
    print(f"Throughput:  {fps:.1f} steps/s")
    print(f"Games Done:  {games_finished}")

    # Print a sample finished game stats if avail
    print("\n[Sample Final State (Env 0)]")
    print(f"Score: {env.batch_scores[0]} - {env.opp_scores[0]}")
    print(f"Deck:  {env.batch_global_ctx[0, 6]}")
    print(f"Phase: {env.batch_global_ctx[0, 8]}")


if __name__ == "__main__":
    benchmark_performance()
