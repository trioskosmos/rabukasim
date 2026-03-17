import os
import sys

# Ensure project root is in path
sys.path.append(os.getcwd())

import time

import torch
from ai.vec_env_adapter import VectorEnvAdapter
from stable_baselines3 import PPO


def benchmark_config(num_envs, n_steps, batch_size):
    """
    Runs a short training burst and returns the SPS.
    """
    print(f"\n [Test] Envs: {num_envs} | Steps: {n_steps} | Batch: {batch_size}", flush=True)

    try:
        print("  - Initializing VectorEnvAdapter...", flush=True)
        env = VectorEnvAdapter(num_envs=num_envs)

        print("  - Initializing PPO model...", flush=True)
        # Benchmarking with CUDA
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"  - Using device: {device}", flush=True)

        model = PPO("MlpPolicy", env, n_steps=n_steps, batch_size=batch_size, verbose=1, device=device)

        # Warmup
        print("  - Warming up (2 indices)...", flush=True)
        try:
            model.learn(total_timesteps=num_envs * 2)
        except Exception as e:
            print(f"  - [Error during Warmup] {e}", flush=True)
            import traceback

            traceback.print_exc()
            return -2

        # Benchmark
        print("  - Benchmarking (1 full rollout)...", flush=True)
        start_time = time.time()
        steps_to_run = num_envs * n_steps
        try:
            model.learn(total_timesteps=steps_to_run)
        except Exception as e:
            print(f"  - [Error during Benchmark] {e}", flush=True)
            import traceback

            traceback.print_exc()
            return -2

        end_time = time.time()

        duration = end_time - start_time
        sps = steps_to_run / duration

        print(f"  - Result: {sps:,.0f} SPS", flush=True)

        # Cleanup
        env.close()
        del model
        torch.cuda.empty_cache()

        return sps

    except RuntimeError as e:
        if "out of memory" in str(e).lower():
            print("  - [OOM] Out of Memory! Skipping this config.")
            # Clear cache immediately
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            return -1
        else:
            print(f"  - [Error] Benchmarking crashed: {e}")
            return -2
    except Exception as e:
        print(f"  - [Error] Unexpected error: {e}")
        return -2


def main():
    try:
        print("========================================================")
        print(" LovecaSim - Performance Optimization & Benchmarking    ")
        print("========================================================")

        # Search Grid
        envs_list = [4096, 8192, 16384]
        steps_list = [64, 128]
        batch_list = [16384, 32768]

        results = []

        for n_envs in envs_list:
            for n_steps in steps_list:
                for b_size in batch_list:
                    # Basic constraint: batch_size <= num_envs * n_steps
                    if b_size > (n_envs * n_steps):
                        continue

                    sps = benchmark_config(n_envs, n_steps, b_size)
                    if sps > 0:
                        results.append({"envs": n_envs, "steps": n_steps, "batch": b_size, "sps": sps})

        # Sort results
        results.sort(key=lambda x: x["sps"], reverse=True)

        print("\n\n" + "=" * 56)
        print(" SUMMARY OF TOP CONFIGURATIONS")
        print("=" * 56)
        print(f"{'Envs':<8} | {'Steps':<8} | {'Batch':<10} | {'SPS':<12}")
        print("-" * 56)

        for r in results[:5]:
            print(f"{r['envs']:<8} | {r['steps']:<8} | {r['batch']:<10} | {r['sps']:,.0f}")

        if results:
            best = results[0]
            print("\n[RECOMMENDATION]")
            print(f" Best Configuration found: Envs={best['envs']}, n_steps={best['steps']}, Batch={best['batch']}")
            print(f" Projected Speed: {best['sps']:,.0f} SPS")
            print("\n Update your .bat or environment variables with these values for maximum throughput.")
        else:
            print("\n[FAILURE] No successful benchmarks recorded.")
    except Exception:
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
