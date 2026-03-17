import os
from pathlib import Path

log_dir = Path("alphazero/logs/loops")
files = sorted(log_dir.glob("*.txt"), key=os.path.getmtime, reverse=True)
if files:
    with open("tmp_latest_log_path.txt", "w") as f:
        f.write(str(files[0].absolute()))
    print(f"Path written: {files[0].name}")
else:
    print("No log files found.")
