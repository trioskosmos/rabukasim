import json
import subprocess
import os
import sys

CONFIG_PATH = "engine_rust_src/sequencer_config.json"
SIM_CMD = "cargo run --bin full_game_sim"

def load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)

def run_simulation():
    print(f"Running simulation: {SIM_CMD}...")
    result = subprocess.run(SIM_CMD, shell=True, capture_output=True, text=True, cwd="engine_rust_src")
    if result.returncode != 0:
        print("Error running simulation:")
        print(result.stderr)
        return None
    return result.stdout

def parse_results(output):
    lines = output.splitlines()
    results = {}
    for line in lines:
        if "Final Score:" in line:
            results["score"] = line.split("Final Score:")[1].strip()
        if "Average Performance:" in line:
            results["performance"] = line.split("Average Performance:")[1].strip()
        if "Winning Player:" in line:
            results["winner"] = line.split("Winning Player:")[1].strip()
    return results

def main():
    if len(sys.argv) < 3:
        print("Usage: python tune_sequencer.py <parameter_name> <new_value>")
        print("Example: python tune_sequencer.py board_presence 2.0")
        print("\nAvailable parameters:")
        config = load_config()
        for k, v in config["weights"].items():
            print(f"  {k}: {v}")
        return

    param = sys.argv[1]
    value = float(sys.argv[2])

    config = load_config()
    if param in config["weights"]:
        old_val = config["weights"][param]
        config["weights"][param] = value
        save_config(config)
        print(f"Updated {param}: {old_val} -> {value}")
    elif param in config["search"]:
        old_val = config["search"][param]
        config["search"][param] = int(value)
        save_config(config)
        print(f"Updated {param}: {old_val} -> {value}")
    else:
        print(f"Parameter {param} not found.")
        return

    output = run_simulation()
    if output:
        results = parse_results(output)
        print("\n--- Simulation Summary ---")
        print(f"Winner: Player {results.get('winner')}")
        print(f"Score: {results.get('score')}")
        print(f"Performance: {results.get('performance')}")
        print("\nFull output saved to reports/tune_result.txt")
        with open("reports/tune_result.txt", "w", encoding="utf-8") as f:
            f.write(output)

if __name__ == "__main__":
    main()
