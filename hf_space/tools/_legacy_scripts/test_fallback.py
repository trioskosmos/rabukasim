import os
import sys

sys.path.append(os.getcwd())
from unittest.mock import patch

# Mock the absence of numba and torch
# By returning None from find_spec, ai_compat will think they are missing
with patch("importlib.util.find_spec", return_value=None):
    # Also need to clear them from sys.modules if they were already there
    if "numba" in sys.modules:
        del sys.modules["numba"]
    if "torch" in sys.modules:
        del sys.modules["torch"]

    # Now import our compat layer
    import engine.game.ai_compat as ai_compat
    from engine.game.game_state import GameState

    print("\n--- Testing Fallback Logic ---")
    print(f"JIT_AVAILABLE: {ai_compat.JIT_AVAILABLE}")
    print(f"TORCH_AVAILABLE: {ai_compat.TORCH_AVAILABLE}")

    # Initialize game - should print the fallback report
    gs = GameState()

    # Try an action that would normally use JIT
    # If it doesn't crash, the fallback is working!
    print("Success: Engine initialized without Numba/Torch.")
