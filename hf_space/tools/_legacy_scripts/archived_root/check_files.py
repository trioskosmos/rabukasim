import glob
import os

files = glob.glob("ai/data/alphazero*.npz")
for f in sorted(files):
    size_mb = os.path.getsize(f) / (1024 * 1024)
    print(f"PATH_START|{f}|{size_mb:.2f} MB|PATH_END")
