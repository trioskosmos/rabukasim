import os
import sys
import time

import numpy as np

# Ensure project root is in path
sys.path.append(os.getcwd())

from functools import partial

from ai.batched_env import BatchedSubprocVecEnv
from ai.train_optimized import create_env


def run_benchmark():
    num_cpu = 4
    os.environ["TRAIN_CPUS"] = str(num_cpu)

    print(f"Initializing Manual Benchmark with {num_cpu} workers...")
    env_fns = [
        partial(create_env, rank=i, usage=1.0, deck_type="random_verified", opponent_type="random")
        for i in range(num_cpu)
    ]
    env = BatchedSubprocVecEnv(env_fns)

    print("Resetting environments...")
    obs = env.reset()

    steps_target = 4000
    start_time = time.time()
    steps_total = 0

    print(f"Running {steps_target} steps...")

    t_opp = 0.0
    t_eng = 0.0
    t_obs = 0.0
    t_tot = 0.0

    for _ in range(0, steps_target, num_cpu):
        # Get random legal actions
        masks = env.env_method("action_masks")  # This is slow via IPC, but ok for now
        actions = []
        for m in masks:
            idx = np.where(m)[0]
            if len(idx) > 0:
                actions.append(np.random.choice(idx))
            else:
                actions.append(0)

        res = env.step(np.array(actions))
        if len(res) == 5:
            obs, rews, terms, truncs, infos = res
        else:
            obs, rews, terms, infos = res
        steps_total += num_cpu

        # Accumulate timings
        if len(infos) > 0:
            info = infos[0]
            t_opp += info.get("t_opp_batch", 0)
            t_eng += info.get("t_worker_eng_avg", 0)
            t_obs += info.get("t_worker_obs_avg", 0)
            t_tot += info.get("t_total_batch", 0)

        if steps_total % 400 == 0:
            print(f" Progress: {steps_total}/{steps_target}", end="\r")

    elapsed = time.time() - start_time
    fps = steps_total / elapsed

    iters = steps_total / num_cpu
    avg_opp = (t_opp / iters) * 1000
    avg_eng = (t_eng / iters) * 1000
    avg_obs = (t_obs / iters) * 1000
    avg_tot = (t_tot / iters) * 1000

    print("\n" + "=" * 40)
    print(f"BENCHMARK RESULTS ({num_cpu} Workers)")
    print(f"Total Steps: {steps_total}")
    print(f"Total Time:  {elapsed:.2f}s")
    print(f"Throughput:  {fps:.2f} Steps/Second")
    print(f"Per Core:    {fps / num_cpu:.2f} Steps/Second")
    print("-" * 40)
    print(" TIMING BREAKDOWN (Per Batch Step)")
    print(f" Total Batch Time: {avg_tot:.2f} ms")
    print(f"  > Engine (CPU):  {avg_eng:.2f} ms")
    print(f"  > Obs (CPU):     {avg_obs:.2f} ms")
    print(f"  > Opponent (GPU):{avg_opp:.2f} ms")
    print(f"  > IPC/Wait:      {avg_tot - avg_eng - avg_obs - avg_opp:.2f} ms")
    print("=" * 40)

    elapsed = time.time() - start_time
    fps = steps_total / elapsed

    print("\n" + "=" * 40)
    print(f"BENCHMARK RESULTS ({num_cpu} Workers)")
    print(f"Total Steps: {steps_total}")
    print(f"Total Time:  {elapsed:.2f}s")
    print(f"Throughput:  {fps:.2f} Steps/Second")
    print(f"Per Core:    {fps / num_cpu:.2f} Steps/Second")
    print("=" * 40)

    env.close()


if __name__ == "__main__":
    run_benchmark()
