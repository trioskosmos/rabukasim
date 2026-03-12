import json
import multiprocessing
import os
import random
import subprocess
import time
from pathlib import Path

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
BINARY_PATH = WORKSPACE_ROOT / "engine_rust_src" / "target" / "release" / "simple_game.exe"
RESULTS_PATH = WORKSPACE_ROOT / "tuning_results.json"

WEIGHT_RANGES = {
    "board_presence": (0.5, 5.0),
    "blades": (0.5, 3.0),
    "hearts": (0.5, 3.0),
    "saturation_bonus": (1.0, 10.0),
    "energy_penalty": (0.0, 2.0),
    "live_ev_multiplier": (5.0, 30.0),
    "uncertainty_penalty_pow": (1.0, 2.0),
    "liveset_placement_bonus": (0.0, 10.0),
    "max_dfs_depth": (8, 10),
}

TOTAL_ITERATIONS = 24
GAMES_PER_ITER = 2
CPU_COUNT = max(1, os.cpu_count() or 1)
CONCURRENT_CONFIGS = max(1, min(8, CPU_COUNT // 2))
RAYON_THREADS_PER_WORKER = max(1, CPU_COUNT // CONCURRENT_CONFIGS)

DECK_P0 = "ai/decks/liella_cup.txt"
DECK_P1 = "ai/decks/liella_cup.txt"


def coerce_weight_value(key, value):
    low, high = WEIGHT_RANGES[key]
    clipped = max(low, min(high, value))
    if key == "max_dfs_depth":
        return int(round(clipped))
    return round(clipped, 3)


def generate_random_weights(rng):
    return {key: coerce_weight_value(key, rng.uniform(low, high)) for key, (low, high) in WEIGHT_RANGES.items()}


def generate_candidate(best_config, rng):
    if not best_config or rng.random() < 0.35:
        return generate_random_weights(rng)

    candidate = {}
    for key, (low, high) in WEIGHT_RANGES.items():
        base = best_config[key]
        if key == "max_dfs_depth":
            delta = rng.randint(-2, 2)
            candidate[key] = coerce_weight_value(key, base + delta)
            continue

        window = (high - low) * 0.2
        candidate[key] = coerce_weight_value(key, rng.uniform(base - window, base + window))
    return candidate


def build_worker_env():
    env = os.environ.copy()
    env["RAYON_NUM_THREADS"] = str(RAYON_THREADS_PER_WORKER)
    return env


def config_sort_key(entry):
    return (entry["win_rate"], entry["avg_score"], entry["sqps"])


def run_benchmark(weights):
    """Run a batch of games for one exhaustive-DFS config."""
    seed = random.randint(0, 2**32 - 1)

    cmd = [
        str(BINARY_PATH),
        "--count",
        str(GAMES_PER_ITER),
        "--seed",
        str(seed),
        "--silent",
        "--json",
        "--deck-p0",
        DECK_P0,
        "--deck-p1",
        DECK_P1,
    ]

    for key, value in weights.items():
        cmd.extend(["--weight", f"{key}={value}"])

    try:
        started = time.perf_counter()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd=WORKSPACE_ROOT,
            env=build_worker_env(),
            timeout=180,
        )
        elapsed = time.perf_counter() - started
        if result.returncode != 0:
            return None

        output = result.stdout
        start_idx = output.find("{")
        if start_idx == -1:
            return None

        data = json.loads(output[start_idx:])

        if data.get("total_games", 0) > 0:
            data["p0_win_rate"] = (data["p0_wins"] / data["total_games"]) * 100
        else:
            data["p0_win_rate"] = 0.0

        if "total_evaluations" not in data:
            data["total_evaluations"] = 0
        data["elapsed_secs"] = round(elapsed, 3)
        data["sqps"] = data["total_evaluations"] / elapsed if elapsed > 0 else 0.0
        data["seed"] = seed

        return data
    except Exception:
        return None


def run_tuning():
    if not BINARY_PATH.exists():
        print(f"Binary not found: {BINARY_PATH}. Please build it first.")
        return

    rng = random.Random(int(time.time()))

    print(f"Starting Exhaustive-DFS Tuning ({TOTAL_ITERATIONS} configs, {GAMES_PER_ITER} games each)")
    print(f"Workers: {CONCURRENT_CONFIGS} | Rayon threads/worker: {RAYON_THREADS_PER_WORKER}")

    results = []
    start_time = time.time()
    total_evals = 0
    best_config = None

    pbar = None
    if tqdm:
        pbar = tqdm(total=TOTAL_ITERATIONS, desc="Tuning Progress")

    with multiprocessing.Pool(processes=CONCURRENT_CONFIGS, maxtasksperchild=32) as pool:
        for i in range(0, TOTAL_ITERATIONS, CONCURRENT_CONFIGS):
            batch_size = min(CONCURRENT_CONFIGS, TOTAL_ITERATIONS - i)
            configs = [generate_candidate(best_config, rng) for _ in range(batch_size)]
            batch_results = pool.map(run_benchmark, configs)

            for config, res in zip(configs, batch_results):
                if not res:
                    continue

                entry = {
                    "config": config,
                    "win_rate": res["p0_win_rate"],
                    "avg_score": res["avg_score_p0"],
                    "avg_turns": res.get("avg_turns", 0),
                    "evals": res.get("total_evaluations", 0),
                    "sqps": round(res.get("sqps", 0.0), 2),
                    "elapsed_secs": res.get("elapsed_secs", 0.0),
                    "seed": res.get("seed"),
                }
                results.append(entry)
                total_evals += entry["evals"]

                if best_config is None or config_sort_key(entry) > config_sort_key(results[0]):
                    best_config = config

            results.sort(key=config_sort_key, reverse=True)
            if results:
                best_config = results[0]["config"]

            elapsed = time.time() - start_time
            sqps = total_evals / elapsed if elapsed > 0 else 0

            if pbar:
                pbar.update(batch_size)
                if results:
                    pbar.set_postfix(
                        {
                            "best_wr": f"{results[0]['win_rate']:.1f}%",
                            "sqps": f"{sqps:.0f}",
                        }
                    )
            elif results:
                current = min(i + CONCURRENT_CONFIGS, TOTAL_ITERATIONS)
                print(f"[{current}/{TOTAL_ITERATIONS}] Best WR: {results[0]['win_rate']:.1f}% | SQPS: {sqps:.0f}")

            with RESULTS_PATH.open("w", encoding="utf-8") as handle:
                json.dump(results, handle, indent=2)

    if pbar:
        pbar.close()

    print("\n--- Tuning Complete ---")
    print("Top 5 Configurations:")
    for r in results[:5]:
        print(
            f"Win Rate: {r['win_rate']:.1f}% | Avg Score: {r['avg_score']:.2f} "
            f"| SQPS: {r['sqps']:.0f} | Config: {r['config']}"
        )


if __name__ == "__main__":
    multiprocessing.freeze_support()
    run_tuning()
