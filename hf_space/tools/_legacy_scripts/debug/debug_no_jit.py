import os
import sys
import time

# Disable Numba JIT before importing anything that might use it
os.environ["NUMBA_DISABLE_JIT"] = "1"
print("DEBUG: Setting NUMBA_DISABLE_JIT = 1")

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
test_import("engine.game.game_state")

print("DEBUG: Calling initialize_game(use_real_data=True)...")
from engine.game.game_state import initialize_game

start_time = time.time()
try:
    state = initialize_game(use_real_data=True)
    duration = time.time() - start_time
    print(f"DEBUG: initialize_game finished in {duration:.2f} seconds.")
except Exception as e:
    print(f"DEBUG: initialize_game failed: {e}")

print("DEBUG: All diagnostic steps finished.")
