import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8000"


def test_endpoint(method, endpoint, payload=None):
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            print(f"GET {endpoint}...", end=" ")
            res = requests.get(url)
        else:
            print(f"POST {endpoint} with {payload}...", end=" ")
            res = requests.post(url, json=payload)

        print(f"Status: {res.status_code}")
        if res.status_code != 200:
            print(f"ERROR BODY: {res.text}")
            return None
        return res.json()
    except Exception as e:
        print(f"EXCEPTION: {e}")
        return None


def verify():
    print(f"--- Verifying Loveca Launcher API at {BASE_URL} ---")

    # 1. List Rooms
    test_endpoint("GET", "/api/rooms/list")

    # 2. Create Room
    # Using 'pve' mode
    room_data = test_endpoint("POST", "/api/rooms/create", {"mode": "pve"})

    if not room_data or not room_data.get("success"):
        print("FAIL: Could not create room.")
        return

    room_id = room_data["room_id"]
    print(f"SUCCESS: Created Room {room_id}")

    # 3. Join Room
    join_data = test_endpoint("POST", "/api/rooms/join", {"room_id": room_id})
    if join_data and join_data.get("success"):
        print("SUCCESS: Joined Room")
    else:
        print("FAIL: Could not join room")

    # 4. Get Decks
    decks_data = test_endpoint("GET", "/api/get_decks")
    if decks_data and decks_data.get("success"):
        decks = decks_data.get("decks", [])
        print(f"SUCCESS: Found {len(decks)} decks.")
        if len(decks) == 0:
            print("WARNING: No decks found! This explains why AI decks are missing.")
        else:
            print(f"Deck IDs: {[d.get('id') for d in decks]}")
    else:
        print("FAIL: Could not get decks")

    # 5. Check for unknown endpoints mentioned by user
    # "unknown api when trying to start a game"
    # User might be hitting /api/set_deck or similar.
    # We can't easily test set_deck without a valid session token from the join, but we can check if it 404s.
    # We need a session token.
    token = room_data.get("session")
    if token:
        # Mock set_deck call
        # header X-Room-Id, X-Session-Token
        url = f"{BASE_URL}/api/set_deck"
        headers = {"X-Room-Id": room_id, "X-Session-Token": token}
        # We need a valid deck body, but let's just see if it is 404 or 400.
        print("POST /api/set_deck (Check existence)...", end=" ")
        res = requests.post(url, headers=headers, json={})
        print(f"Status: {res.status_code}")
        if res.status_code == 404:
            print("FAIL: /api/set_deck is 404 Not Found")
        else:
            print("SUCCESS: /api/set_deck exists (got non-404)")


if __name__ == "__main__":
    verify()
