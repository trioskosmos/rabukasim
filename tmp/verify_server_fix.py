import os
import sys

# Add the project root to sys.path
sys.path.append(os.getcwd())

from backend.server import create_room_internal, load_game_data


def test_deck_partitioning():
    print("Testing deck partitioning and limits...")

    # Load real data
    load_game_data()

    # Mock some card data
    deck_content = [
        "PL!-sd1-001-SD",  # Member
        "PL!-sd1-002-SD",  # Member
        "LL-E-001-SD",  # Energy
    ] * 100  # Large list to trigger limits

    custom_decks = {"0": {"main": deck_content, "energy": ["LL-E-001-SD"] * 20}}

    room = create_room_internal("TEST", mode="pve", custom_decks=custom_decks)
    gs = room["state"]

    # Check player 0 deck in Rust engine state
    # p0_deck should be members + lives = 60
    # In my mock deck_content, I have 2 members and 0 lives (LL-E is energy and will be filtered out of main)
    # Wait, LL-E-001-SD is type 'エネルギー' (Energy).
    # In server.py partitioning:
    # if base_id in member_db: members.append(uid)
    # elif base_id in live_db: lives.append(uid)

    # So members will have 200 cards (but LL-E is not a member).
    # Wait, LL-E-001-SD is NOT in member_db.

    # Let's count what ended up in gs
    # gs.initialize_game(p0_m, p1_m, p0_e, p1_e, p0_l, p1_l)

    p0 = gs.get_player(0)
    print(f"Player 0 Main Deck Size: {len(p0.deck)}")
    print(f"Player 0 Energy Zone (initial): {len(p0.energy_zone)}")

    # In Rust engine, initial_deck is what we passed
    # and deck is shuffled version.

    # Let's verify the counts we passed to initialize_game in create_room_internal
    # (I'd need to mock or trace, but let's just check the result)

    # If I gave 200 IDs, and only 2 types were members:
    # each type appeared 100 times.
    # Truncated members: 48.
    # Truncated lives: 0.
    # Total main: 48 (because 48 members + 0 lives).

    print(f"Deck count: {len(p0.deck)}")
    # Note: engine draws 6 cards to hand, so deck size will be 48 - 6 = 42
    print(f"Hand count: {len(p0.hand)}")

    if len(p0.deck) + len(p0.hand) <= 60:
        print("Success: Deck size is within limits.")
    else:
        print(f"Failure: Deck size too large: {len(p0.deck) + len(p0.hand)}")


if __name__ == "__main__":
    test_deck_partitioning()
