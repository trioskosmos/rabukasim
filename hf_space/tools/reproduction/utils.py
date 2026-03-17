import os

import engine_rust


def debug_print(msg):
    print(f"[DEBUG] {msg}")


def create_test_card_database():
    """
    Creates a minimal card database for testing.
    Since we can't easily modify the compiled json in memory without parsing it,
    we usually load the real one.
    However, for simple tests, we might want to patch it.
    For reproduction, we mainly rely on the real `cards_compiled.json`.
    """
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    json_path = os.path.join(project_root, "data", "cards_compiled.json")

    with open(json_path, "r", encoding="utf-8") as f:
        json_content = f.read()

    db = engine_rust.PyCardDatabase(json_content)
    return db


def create_game_state(db):
    """
    Creates a game state with standard initialization.
    """
    gs = engine_rust.PyGameState(db)

    # Initialize with dummy decks
    p0_deck = [1] * 60  # Dummy ID
    p1_deck = [1] * 60
    p0_energy = [1] * 10
    p1_energy = [1] * 10
    p0_lives = [1, 2, 3]  # Dummy life IDs
    p1_lives = [1, 2, 3]

    gs.initialize_game(p0_deck, p1_deck, p0_energy, p1_energy, p0_lives, p1_lives)

    # Fast forward to Main Phase
    gs.phase = 4

    return gs


def process_action(gs, arg1, arg2=None, arg3=None):
    """
    Helper to emulate the old process_action behavior by calculating action IDs.
    Args:
        gs: PyGameState
        arg1: hand_idx (for Play) or choice_idx (for Select) or slot_idx (for Activate)
        arg2: slot_idx (for Play) or ab_idx (for Activate) or action_id (legacy)
        arg3: slot_idx (legacy)
    """
    # Legacy format: process_action(player_idx, action_type, target) -> We don't use this anymore here.
    # We assume usage like:
    # Play: process_action(gs, hand_idx, slot_idx)
    # Select: process_action(gs, choice_idx)

    action_id = 0

    # Heuristic detection of intent
    if arg2 is not None:
        # Play Member: hand_idx, slot_idx
        hand_idx = arg1
        slot_idx = arg2
        # Formula: 1 + hand_idx * 3 + slot_idx
        action_id = 1 + hand_idx * 3 + slot_idx
    else:
        # Select Choice: choice_idx
        # Check if pending choice exists
        if gs.pending_choice_type:
            # If it's SELECT_HAND_DISCARD, args are choice indices, which map to 600+
            choice_idx = arg1
            action_id = 600 + choice_idx
        else:
            # Unknown single arg?
            pass

    debug_print(f"Executing Action ID: {action_id} (args: {arg1}, {arg2})")
    gs.step(action_id)
