import subprocess
import json
import os
import shutil
import time

CONFIG_PATH = "engine_rust_src/sequencer_config.json"
BINARY_PATH = "engine_rust_src/target/release/simple_game.exe"
DECKS_DIR = "ai/decks"

def run_benchmark(count=100, seed=1000, deck_p0="ai/decks/liella_cup.txt", deck_p1="ai/decks/liella_cup.txt"):
    cmd = [
        BINARY_PATH,
        "--count", str(count),
        "--seed", str(seed),
        "--silent",
        "--json"
    ]
    if deck_p0:
        cmd.extend(["--deck-p0", deck_p0])
    if deck_p1:
        cmd.extend(["--deck-p1", deck_p1])

    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        print(f"Error running benchmark: {result.stderr}")
        return None
    
    try:
        # Find the start of JSON (sometimes there might be stray prints)
        output = result.stdout
        start_idx = output.find("{")
        if start_idx == -1:
            return None
        return json.loads(output[start_idx:])
    except json.JSONDecodeError:
        print(f"Failed to parse JSON output: {result.stdout[:200]}...")
        return None

def update_weights(weights):
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)
    
    for k, v in weights.items():
        if k in config["weights"]:
            config["weights"][k] = v
    
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)

def main():
    if not os.path.exists(BINARY_PATH):
        print(f"Binary not found: {BINARY_PATH}. Please build it first.")
        return

    # Backup original config
    shutil.copy(CONFIG_PATH, CONFIG_PATH + ".bak")

    configs = [
        ("Baseline", {}),
        ("Higher Board Presence", {"board_presence": 2.5}),
        ("Lower Uncertainty Penalty", {"uncertainty_penalty_pow": 1.1}),
        ("Aggressive Live Multiplier", {"live_ev_multiplier": 25.0}),
        ("High Saturation Bonus", {"saturation_bonus": 5.0}),
    ]

    summary = []

    try:
        for name, weights in configs:
            print(f"\n>>> Running Config: {name}")
            update_weights(weights)
            
            # Run 50 games for a quick benchmark (tuning can do more later)
            data = run_benchmark(count=50)
            if data:
                win_rate = (data["p0_wins"] / data["total_games"]) * 100
                print(f"    Win Rate: {win_rate:.1f}% | Avg Score: {data['avg_score_p0']:.2f}")
                summary.append({
                    "name": name,
                    "win_rate": win_rate,
                    "avg_score": data["avg_score_p0"],
                    "avg_turns": data["avg_turns"]
                })
            else:
                print("    Failed to get data.")

    finally:
        # Restore original config
        shutil.move(CONFIG_PATH + ".bak", CONFIG_PATH)

    print("\n" + "="*40)
    print("FINAL TUNING SUMMARY")
    print("="*40)
    for s in summary:
        print(f"{s['name']:<30} | Win: {s['win_rate']:>5.1f}% | Score: {s['avg_score']:>5.2f} | Turns: {s['avg_turns']:>5.2f}")

if __name__ == "__main__":
    main()
