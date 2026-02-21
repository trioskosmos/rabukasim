import os
import sys
import time


def test_import(name):
    print(f"DEBUG: Attempting to import {name}...")
    start = time.time()
    try:
        if name in sys.modules:
            del sys.modules[name]
        __import__(name)
        print(f"DEBUG: {name} imported in {time.time() - start:.2f}s")
    except Exception as e:
        print(f"DEBUG: {name} failed: {e}")


# Check for Numba environment variables
print("--- Numba Env Vars ---")
for k, v in os.environ.items():
    if "NUMBA" in k or "CUDA" in k:
        print(f"{k} = {v}")
print("----------------------")

test_import("numpy")
test_import("numba.core.config")
test_import("numba.core.entrypoints")
test_import("numba.np.ufunc")
test_import("numba.cuda")  # Often the culprit
test_import("numba")

print("DEBUG: Diagnostic finished.")
