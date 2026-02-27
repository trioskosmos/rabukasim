from pathlib import Path
import os

log_dir = Path("alphazero/logs/loops")
files = sorted(log_dir.glob("*.txt"), key=os.path.getmtime, reverse=True)
if files:
    latest_file = files[0]
    print(f"Reading headers: {latest_file.name}")
    with open(latest_file, "r", encoding="utf-8") as f:
        for _ in range(5):
            print(f.readline().strip())
else:
    print("No log files found.")
