import os

print("Disabling Numba CUDA...")
os.environ["NUMBA_DISABLE_CUDA"] = "1"
print("Attempting import numba...")
try:
    import numba

    print(f"Numba imported! Version: {numba.__version__}")
except Exception as e:
    print(f"Failed even with CUDA disabled: {e}")
