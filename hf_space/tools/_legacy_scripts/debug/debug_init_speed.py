import os
import sys
import time

# Add project root to path
sys.path.append(os.getcwd())

print("DEBUG: Importing GameState...")
start_import = time.time()
from engine.game.game_state import initialize_game

print(f"DEBUG: Import took {time.time() - start_import:.2f}s")

print("DEBUG: Calling initialize_game()...")
start_init = time.time()
try:
    game = initialize_game(deck_type="training")
    print(f"DEBUG: initialize_game took {time.time() - start_init:.2f}s")
    print(f"DEBUG: Loaded {len(game.member_db)} members, {len(game.live_db)} lives")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback

    traceback.print_exc()

print("DEBUG: Done.")
