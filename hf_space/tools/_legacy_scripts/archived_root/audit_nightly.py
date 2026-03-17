import glob
import os

import numpy as np

files = glob.glob("ai/data/alphazero_nightly_chunk_*.npz")
print(f"{'Filename':40} | {'Samples':>8} | {'Keys'}")
print("-" * 65)

total = 0
for f in sorted(files):
    try:
        data = np.load(f)
        samples = len(data["states"])
        keys = list(data.keys())
        print(f"{os.path.basename(f):40} | {samples:>8} | {keys}")
        total += samples
    except Exception as e:
        print(f"{os.path.basename(f):40} | ERROR    | {e}")

print("-" * 65)
print(f"Total Combined Samples: {total}")
