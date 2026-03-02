from pathlib import Path
import os
import re

log_dir = Path("alphazero/logs/loops")
files = sorted(log_dir.glob("*.txt"), key=os.path.getmtime, reverse=True)

print(f"{'Filename':<55} | {'Total':<8} | {'Turn':<8} | {'Snapshot'}")
print("-" * 90)

for f in files:
    try:
        content = f.read_text(encoding='utf-8')
        total_match = re.search(r"Total Steps: (\d+)", content)
        turn_match = re.search(r"Turn Steps: (\d+)", content)
        snapshot = "YES" if "--- Board State Snapshot ---" in content else "NO"
        
        total = total_match.group(1) if total_match else "?"
        turn = turn_match.group(1) if turn_match else "?"
        if int(turn) > 100 or snapshot == "YES":
            print(f"{f.name:<55} | {total:<8} | {turn:<8} | {snapshot}")
    except:
        pass
