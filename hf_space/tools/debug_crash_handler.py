import os
import sys
import traceback

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.rust_serializer import RustGameStateSerializer
from backend.server import ROOMS, app, create_room_internal, game_lock


def simulate_crash():
    print("--- Simulating 500 Error Crash Handler ---")

    # Create Room
    room_id = "CRASH_TEST"
    with game_lock:
        ROOMS[room_id] = create_room_internal(room_id, mode="pve", deck_type="normal")

    # Mock request context
    with app.test_request_context(
        "/api/action", headers={"X-Room-Id": room_id}, json={"action_id": 99999}
    ):  # Invalid Action ID usually 400, but force exception?
        # We need to FORCE an exception inside do_action logic.
        # Hard to inject without mocking too much.
        # But we can call the crash handler code directly to test JSON serialization.

        print("Testing serialize_state with usage of app.json.dumps...")
        try:
            # Get state
            gs = ROOMS[room_id]["state"]
            # Serialize
            serialized = RustGameStateSerializer(
                ROOMS[room_id]["state"].db.inner, ROOMS[room_id]["state"].db.inner, ROOMS[room_id]["state"].db.inner
            ).serialize_state(gs, mode="pve")  # Hacky init

            # The actual serializer is global in server.py.
            # Let's import it
            from backend.server import rust_serializer

            serialized = rust_serializer.serialize_state(gs, mode="pve")

            # Try dumping
            dump = app.json.dumps({"error": "Test Error", "trace": "Traceback...", "state": serialized})
            print(f"PASS: JSON Dump successful. Length: {len(dump)}")

        except Exception as e:
            print(f"FAIL: JSON Dump failed: {e}")
            traceback.print_exc()


if __name__ == "__main__":
    simulate_crash()
