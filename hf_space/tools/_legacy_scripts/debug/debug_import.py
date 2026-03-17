import os
import sys
import time

sys.path.insert(0, os.getcwd())


def test_import(name):
    print(f"DEBUG: Importing {name}...")
    start = time.time()
    try:
        __import__(name)
        print(f"DEBUG: {name} imported in {time.time() - start:.2f}s")
    except Exception as e:
        print(f"DEBUG: {name} failed: {e}")


test_import("numpy")
test_import("numba")
test_import("engine.game.numba_utils")

print("DEBUG: All diagnostic imports finished.")
