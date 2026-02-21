import os

os.environ["NUMBA_DEBUG"] = "1"
os.environ["NUMBA_DEBUG_FRONTEND"] = "1"

print("Starting debug import...")
try:
    import numba

    print(f"Numba imported: {numba.__version__}")
except Exception as e:
    print(f"Import failed: {e}")
