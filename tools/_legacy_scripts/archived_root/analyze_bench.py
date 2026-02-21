import glob

import numpy as np

files = glob.glob("ai/data/test_*.npz")
print("File, Games, Samples")
for f in sorted(files):
    try:
        data = np.load(f)
        samples = len(data["states"])
        # For our data gen, winners array len should equal samples
        print(f"{f}, 5, {samples}")
    except Exception as e:
        print(f"{f}, Error: {e}")
