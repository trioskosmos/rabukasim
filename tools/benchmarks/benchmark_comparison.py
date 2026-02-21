import os
import sys
import time

import numpy as np

# Ensure path
sys.path.append(os.getcwd())


def run_benchmark(mode, steps=100, num_envs=1024, opp_mode=0, mcts_sims=50):
    print(f"\n[Benchmark] Setting up {mode} Engine (Envs={num_envs}, OppMode={opp_mode}, Sims={mcts_sims})...")
    if mode == "RUST":
        os.environ["USE_RUST_ENGINE"] = "1"
    else:
        os.environ["USE_RUST_ENGINE"] = "0"

    os.environ["MCTS_SIMS"] = str(mcts_sims)

    # Reload adapter to pick up env var
    import importlib

    import ai.vec_env_adapter

    importlib.reload(ai.vec_env_adapter)
    from ai.vec_env_adapter import VectorEnvAdapter

    try:
        start_init = time.time()
        env = VectorEnvAdapter(num_envs=num_envs, opp_mode=opp_mode)
        obs = env.reset()
        print(f"[Benchmark] Init Time: {time.time() - start_init:.2f}s")

        print(f"[Benchmark] Running {steps} steps...")
        start = time.time()
        for i in range(steps):
            # Random actions
            actions = np.random.randint(0, 2000, size=num_envs)
            env.step(actions)
            if i % 10 == 0:
                print(".", end="", flush=True)
        end = time.time()
        print()

        duration = end - start
        total_steps = steps * num_envs
        sps = total_steps / duration
        print(f"--- RESULTS ({mode}, Opp={opp_mode}, Sims={mcts_sims}) ---")
        print(f"Total Steps: {total_steps}")
        print(f"Total Time:  {duration:.4f}s")
        print(f"SPS:         {sps:,.0f} steps/sec")
        return sps
    except Exception as e:
        print(f"Error running {mode}: {e}")
        import traceback

        traceback.print_exc()
        return 0


if __name__ == "__main__":
    # Rust Benchmark - MCTS 10 Sims
    run_benchmark("RUST", steps=50, num_envs=512, opp_mode=1, mcts_sims=10)

    # Rust Benchmark - MCTS 50 Sims
    run_benchmark("RUST", steps=50, num_envs=512, opp_mode=1, mcts_sims=50)

    # Rust Benchmark - MCTS 100 Sims
    run_benchmark("RUST", steps=50, num_envs=512, opp_mode=1, mcts_sims=100)
