import os
import sys

print("Starting diagnostics...")
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")

try:
    import numpy as np

    print(f"Numpy version: {np.__version__}")
    print(f"Numpy path: {np.__file__}")
except Exception as e:
    print(f"Error importing numpy: {e}")

try:
    print("Attempting to import llvmlite...")
    import llvmlite

    print(f"llvmlite version: {llvmlite.__version__}")
except Exception as e:
    print(f"Error importing llvmlite: {e}")

try:
    print("Attempting to import numba (this might hang)...")
    import numba

    print(f"Numba version: {numba.__version__}")
    print(f"Numba path: {numba.__file__}")
except Exception as e:
    print(f"Error importing numba: {type(e).__name__}: {e}")
    import traceback

    traceback.print_exc()

print("Diagnostics finished.")
