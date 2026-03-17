import glob
import os

import numpy as np

files = glob.glob("ai/data/*.npz")
print(f"{'Filename':50} | {'Size(MB)':>10} | {'Samples':>10}")
print("-" * 75)

for f in sorted(files):
    size = os.path.getsize(f) / (1024 * 1024)
    samples = "N/A"
    try:
        # Just check shape of 'states' to get sample count without loading everything
        with np.load(f) as data:
            if "states" in data.keys():
                samples = len(data["states"])
    except:
        samples = "CORRUPT"

    print(f"{os.path.basename(f):50} | {size:10.2f} | {samples:>10}")
