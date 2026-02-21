import os
import sys
import traceback

# Add current directory to path
sys.path.append(os.getcwd())

print(f"CWD: {os.getcwd()}")
print(f"Path: {sys.path}")

try:
    from game.game_state import GameState

    print("Import GameState successful")
    gs = GameState()
    print("GameState init successful")
except Exception:
    traceback.print_exc()
