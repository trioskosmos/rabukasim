import requests

BASE_URL = "http://127.0.0.1:8000"


def log(msg):
    print(f"[SIM] {msg}")


def run_simulation():
    session = requests.Session()

    # 1. Fetch Decks
    log("Fetching decks...")
    try:
        res = session.get(f"{BASE_URL}/api/get_decks")
        if res.status_code != 200:
            log(f"FAIL: Fetch decks returned {res.status_code}")
            return
        data = res.json()
        if not data.get("success"):
            log("FAIL: Fetch decks success=false")
            return

        decks = data.get("decks", [])
        if not decks:
            log("FAIL: No decks found")
            return

        # Use the first available deck
        # The frontend uses Modals.resolveDeck logic, but for simulation we just need valid IDs/names if the backend accepts raw names or IDs
        # api/rooms/create expects "p0_deck": [card_ids...] or similar?
        # Let's check api.rs for what CreateRoomReq expects.
        # Assuming it expects deck content (list of card IDs).
        # We'll use a known starter deck if we can't parse the response easily, or just try to use what we got.

        # Actually, let's just use the 'Starter' deck if present, or the first one.
        # Ideally we resolve it like the frontend does.
        # For now, let's try to get a random deck to be safe.

    except Exception as e:
        log(f"FAIL: Exception fetching decks: {e}")
        return

    # 1b. Get Random Deck (easier for valid IDs)
    log("Fetching random valid deck...")
    deck_content = []
    energy_content = []
    try:
        res = session.get(f"{BASE_URL}/api/get_random_deck")
        data = res.json()
        if not data.get("success"):
            log("FAIL: Random deck failed")
            return
        deck_content = data.get("content", [])
        energy_content = ["30005"] * 10  # Strings! 30005 is a valid energy ID as string
    except Exception as e:
        log(f"FAIL: Exception fetching random deck: {e}")
        return

    # 2. Create Room
    log("Creating room...")
    room_id = ""
    token = ""
    payload = {
        "mode": "pve",
        "p0_deck": deck_content,
        "p1_deck": deck_content,
        "p0_energy": energy_content,
        "p1_energy": energy_content,
        "public": True,
    }

    try:
        res = session.post(f"{BASE_URL}/api/rooms/create", json=payload)
        if res.status_code != 200:
            log(f"FAIL: Create room returned {res.status_code} - {res.text}")
            return

        data = res.json()
        if not data.get("success"):
            log(f"FAIL: Create room success=false - {data.get('error')}")
            return

        room_id = data.get("room_id")
        token = data.get("session")
        player_idx = data.get("player_idx")

        log(f"Room Created! ID: {room_id}, Session: {token}, PID: {player_idx}")

    except Exception as e:
        log(f"FAIL: Exception creating room: {e}")
        return

    # 3. Fetch State (Simulate Network.js)
    log("Fetching State...")
    headers = {"X-Room-Id": room_id, "X-Session-Token": token}

    try:
        res = session.get(f"{BASE_URL}/api/state?viewer=0", headers=headers)
        if res.status_code != 200:
            log(f"FAIL: Fetch state returned {res.status_code} - {res.text}")
            return

        data = res.json()

        if not data.get("success"):
            log("FAIL: State success=false")
            return

        state = data.get("state")
        if not state:
            log("FAIL: 'state' object missing in response")
            return

        log("State fetched successfully. Validating structure for ui_rendering.js...")

        # Validate critical fields for ui_rendering.js
        # ui_rendering.js:257: Cannot read properties of undefined (reading '0')
        # Likely state.players[p_idx].live_zone[0] or similar

        players = state.get("players", [])
        if len(players) < 2:
            log("FAIL: state.players length < 2")

        p0 = players[0]
        live_zone = p0.get("live_zone")

        if live_zone is None:
            log("FAIL: p0.live_zone is None")
        elif not isinstance(live_zone, list):
            log("FAIL: p0.live_zone is not a list")
        else:
            log(f"p0.live_zone length: {len(live_zone)}")
            # Check if accessing index 0 works (even if None)
            try:
                item = live_zone[0]
                log(f"p0.live_zone[0]: {item}")
            except IndexError:
                log("FAIL: p0.live_zone is empty")

        log("Simulation Complete.")

    except Exception as e:
        log(f"FAIL: Exception fetching state: {e}")


if __name__ == "__main__":
    run_simulation()
