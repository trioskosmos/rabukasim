import glob
import json
import os


def check_level3():
    files = glob.glob("replays/*.json")
    opt_files = [f for f in files if "_opt.json" in f]

    if not opt_files:
        print("No optimized files found.")
        return

    # Sort by time
    opt_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    last_opt = opt_files[0]
    std_file = last_opt.replace("_opt.json", ".json")

    if os.path.exists(std_file):
        size_std = os.path.getsize(std_file)
        size_opt = os.path.getsize(last_opt)
        savings = (1 - size_opt / size_std) * 100

        print(f"File: {os.path.basename(std_file)}")
        print(f"Original: {size_std / 1024:.2f} KB")
        print(f"Optimized: {size_opt / 1024:.2f} KB")
        print(f"Reduction: {savings:.2f}%")

        # Check integrity
        with open(last_opt, "r", encoding="utf-8") as f:
            d = json.load(f)
            if d.get("level") == 3:
                print("PASS: Level 3 (Action Log) Detected.")
                if "action_log" in d:
                    print(f"Action Log Length: {len(d['action_log'])}")
                if "seed" in d:
                    print(f"Seed: {d['seed']}")
            else:
                print(f"FAIL: Not Level 3 (Found Level {d.get('level', 2)})")
    else:
        print(f"Could not find match for {last_opt}")


if __name__ == "__main__":
    check_level3()
