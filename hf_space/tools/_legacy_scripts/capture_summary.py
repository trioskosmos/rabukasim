import subprocess

with open("batch2_summary.txt", "w", encoding="utf-8") as f:
    subprocess.run(["uv", "run", "python", "scripts/analyze_failures.py"], stdout=f)
