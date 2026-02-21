import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.server import create_room_internal, rust_serializer
from engine.game.enums import Phase


def debug_mulligan():
    print("--- Debugging Mulligan Phase State ---")

    # Initialize DBs (normally done by server.py on import)
    # We rely on server.py having done this or do it manually if needed.
    # rust_serializer is initialized in server.py load_game_data()
    # But checking server.py, it does load_game_data() on import.

    # Create a Rust room
    print("Creating Rust Room...")
    room = create_room_internal("DEBUG_ROOM", mode="pve", deck_type="normal")
    gs = room["state"]

    print(f"Room Created. Phase: {gs.phase} (Expected: {int(Phase.MULLIGAN_P1)})")
    print(f"Current Player: {gs.current_player}")

    # Serialize State for Player 0 (Assuming P0 perspective)
    print("\nSerializing State for Player 0...")
    serialized = rust_serializer.serialize_state(gs, viewer_idx=0)

    # Check for 'mode'
    if "mode" in serialized:
        print(f"PASS: 'mode' found in state: {serialized['mode']}")
    else:
        print("FAIL: 'mode' NOT found in state!")

    # Check legal actions
    legal = serialized.get("legal_actions", [])
    print(f"\nLegal Actions ({len(legal)}):")
    for a in legal:
        print(f"  ID: {a['id']} Type: {a.get('type')} HandIdx: {a.get('hand_idx')}")

    if not legal:
        print("FAIL: No legal actions found for Player 0!")
    else:
        print("PASS: Legal actions present.")


if __name__ == "__main__":
    debug_mulligan()
