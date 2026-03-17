import os
import zipfile

import numpy as np

path = "ai/data/alphazero_bootstrapping_current_chk.npz"
if not os.path.exists(path):
    print(f"File not found: {path}")
    exit(1)

print(f"File size: {os.path.getsize(path) / 1024 / 1024:.2f} MB")

try:
    with zipfile.ZipFile(path, "r") as z:
        print("Zip contents:", z.namelist())
        for name in z.namelist():
            info = z.getinfo(name)
            print(f"  {name}: {info.file_size} bytes (compressed: {info.compress_size})")

    # Try actual numpy load
    data = np.load(path)
    print("Numpy keys:", list(data.keys()))
    for k in data.keys():
        try:
            val = data[k]
            print(f"  {k} shape: {val.shape}, dtype: {val.dtype}")
        except Exception as e:
            print(f"  Error loading key {k}: {e}")
except Exception as e:
    print(f"General error: {e}")
