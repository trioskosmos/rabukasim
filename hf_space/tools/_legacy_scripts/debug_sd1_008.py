import os
import sys

sys.path.append(os.getcwd())
from engine.game.enums import Phase
from engine.game.game_state import GameState, initialize_game

# Ensure fresh load
GameState.member_db = {}
GameState.live_db = {}

gs = initialize_game(use_real_data=True)
p = gs.players[0]

# Find SD1-008
for cid, card in gs.member_db.items():
    if card.card_no == "PL!-sd1-008-SD":
        print(f"Found SD1-008 at ID {cid}")

        # Setup test state
        gs.current_player = 0
        p.stage[0] = cid
        p.main_deck = [cid] * 20
        p.energy_zone = [cid] * 20
        p.tapped_energy.fill(False)
        gs.phase = Phase.MAIN

        # Trace step(200)
        print("Before step(200):")
        print(f"  Phase: {gs.phase} (MAIN={Phase.MAIN})")
        print(f"  pending_choices: {len(gs.pending_choices)}")
        print("  action: 200")
        print(f"  200 <= 200 <= 202: {200 <= 200 <= 202}")

        # Call _execute_action directly to trace
        print("\nCalling _execute_action(200) directly...")
        gs._execute_action(200)

        print("After _execute_action:")
        print(f"  Deck={len(p.main_deck)}, Discard={len(p.discard)}")
        print(f"  pending_effects={len(gs.pending_effects)}")
        print(f"  pending_choices={len(gs.pending_choices)}")
        break
