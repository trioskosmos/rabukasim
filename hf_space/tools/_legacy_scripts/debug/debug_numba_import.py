try:
    import numpy

    print(f"Numpy version: {numpy.__version__}")
except ImportError:
    print("Numpy not found")

try:
    import numba

    print(f"Numba version: {numba.__version__}")
except Exception as e:
    print(f"Error importing numba: {type(e).__name__}: {e}")
    import traceback

    traceback.print_exc()
