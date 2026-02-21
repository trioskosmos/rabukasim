import os
import sys

sys.path.append(os.getcwd())

from engine.game.data_loader import CardDataLoader
from engine.game.enums import Phase
from engine.game.game_state import GameState


def reproduce_loop():
    print("Initializing GameState...")

    # Load data
    json_path = os.path.join(os.getcwd(), "data", "cards.json")
    loader = CardDataLoader(json_path)
    # Assuming loader defaults work, or we point to data/cards_compiled.json
    # We might need to handle paths if CWD is wrong, but we set CWD in run_command.
    members, lives, energy = loader.load()
    GameState.initialize_class_db(members, lives)

    gs = GameState()
    # gs.reset_game() # Does not exist

    p0 = gs.players[0]

    # Setup state matching the report
    # Player 0 Stage: Miyashita Ai (Nijigasaki)
    # ID: 3146176
    # Note: Using compiled IDs requires checking logic consistency
    # Assuming standard loading handles IDs correctly

    # Clear decks/hands for clarity
    p0.hand = []
    p0.stage = [-1] * 3
    p0.stage_energy = [[], [], []]
    p0.live_zone = []

    # Add Miyashita Ai to Stage 0
    p0.stage[0] = 3146176  # PL!N-sd1-017-SD (Nijigasaki)
    p0.tapped_members[0] = False

    # Add Love wing bell to Live Zone
    # ID: 1049587
    p0.live_zone.append(1049587)

    # Set Phase to PERFORMANCE_P1
    gs.phase = Phase.PERFORMANCE_P1
    gs.current_player = 0
    gs.first_player = 0

    # Ensure performance_abilities_processed is False
    p0.performance_abilities_processed = False

    print(f"Initial Phase: {gs.phase}")
    print(f"P0 Stage: {p0.stage}")
    print(f"P0 Live Zone: {p0.live_zone}")

    # Step 1: Should trigger ability and queue it
    print("\n--- Executing Step(0) #1 ---")
    gs = gs.step(0)
    print(f"Phase after #1: {gs.phase}")

    # Check if ability triggered
    # (can't check internal triggered_abilities easily from outside without inspection, but phase shouldn't change yet if it returned early)

    if gs.phase == Phase.PERFORMANCE_P1:
        print("Phase stayed P1 (Expected: Ability Triggered)")
    else:
        print(f"Phase changed unexpectedly! {gs.phase}")

    # Step 2: Should process ability and advance
    print("\n--- Executing Step(0) #2 ---")
    gs = gs.step(0)
    print(f"Phase after #2: {gs.phase}")

    if gs.phase != Phase.PERFORMANCE_P1:
        print("SUCCESS: Phase advanced!")
    else:
        print("FAILURE: Phase stuck in PERFORMANCE_P1 (Infinite Loop detected)")

        # Inspection
        print(f"Pending Choices: {gs.pending_choices}")
        print(f"Triggered Abilities: {gs.triggered_abilities}")
        print(f"Pending Effects: {gs.pending_effects}")
        print(f"Processed Flag: {getattr(p0, 'performance_abilities_processed', 'Missing')}")


if __name__ == "__main__":
    reproduce_loop()
