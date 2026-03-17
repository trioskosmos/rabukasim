import os
import sys
import time

# Ensure project root is in path
sys.path.insert(0, os.getcwd())

print("DIAGNOSTIC: Starting script...")

try:
    print("DIAGNOSTIC: Importing numpy...")
    print("DIAGNOSTIC: Importing numba...")
    from numba import njit

    print("DIAGNOSTIC: Testing simple njit...")

    @njit
    def add(a, b):
        return a + b

    print(f"DIAGNOSTIC: Numba Test Result: {add(1, 2)}")

    print("DIAGNOSTIC: Importing VectorGameState from ai.vector_env...")
    start = time.time()
    from ai.vector_env import VectorGameState

    print(f"DIAGNOSTIC: Import successful in {time.time() - start:.2f}s")

    print("DIAGNOSTIC: Initializing VectorGameState(1)...")
    start = time.time()
    vgs = VectorGameState(1)
    print(f"DIAGNOSTIC: Initialization successful in {time.time() - start:.2f}s")

    print("DIAGNOSTIC: Success!")
except Exception as e:
    print(f"DIAGNOSTIC: FAILED with error: {e}")
    import traceback

    traceback.print_exc()
