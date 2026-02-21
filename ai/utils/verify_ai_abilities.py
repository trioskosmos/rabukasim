import json
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import engine_rust

from ai.utils.benchmark_decks import parse_deck
from engine.game.data_loader import CardDataLoader  # Only for descriptions
from engine.game.desc_utils import get_action_desc
from engine.game.game_state import GameState  # Only for descriptions


def verify_abilities():
    print("--- AI Ability Visibility Verification (Rust Engine) ---")

    # 1. Load DB
    db_path = "engine/data/cards_compiled.json"
    with open(db_path, "r", encoding="utf-8") as f:
        db_content = f.read()
    db_json = json.loads(db_content)

    # Initialize Python GameState for descriptions
    loader = CardDataLoader(db_path)
    members, lives, energy = loader.load()
    GameState.initialize_class_db(members, lives)
    py_gs = GameState()

    # 2. Setup Rust Engine State
    db = engine_rust.PyCardDatabase(db_content)
    gs = engine_rust.PyGameState(db)

    # Load a benchmark deck to get valid IDs
    deck_file = "ai/decks/liella_cup.txt"
    main_deck, lives_deck, energy_deck = parse_deck(
        deck_file, db_json["member_db"], db_json["live_db"], db_json.get("energy_db", {})
    )

    # Standard sizes
    test_lives = (lives_deck * 10)[:12]
    test_deck = (main_deck * 10)[:48]
    test_energy = (energy_deck * 10)[:12]

    gs.initialize_game(test_deck, test_deck, test_energy, test_energy, test_lives, test_lives)

    # Fast-forward to Main Phase
    # Phase Flow: MULLIGAN_P1 -> MULLIGAN_P2 -> LIVE_SET -> MAIN
    print(f"Skipping Mulligan P1 (Current: {gs.phase})...")
    gs.step(0)  # Confirm Mulligan P1
    print(f"Skipping Mulligan P2 (Current: {gs.phase})...")
    gs.step(0)  # Confirm Mulligan P2

    # In Live Set, we need to set a card.
    # Actions 400-459 are Live Set.
    # Player 1 (index 0) sets a card.
    print(f"Setting Live Card (Current: {gs.phase})...")
    gs.step(400)  # Set first card in hand as live
    # Player 2 (index 1) sets a card.
    gs.step(400)

    # Sync Python GS for descriptions
    hand = list(gs.get_player(0).hand)
    py_gs.players[0].hand = hand
    py_gs.current_player = gs.current_player
    py_gs.phase = gs.phase

    # 3. Find or Inject Ability Card
    ability_card_id = -1
    hand_idx = -1
    for i, cid in enumerate(hand):
        if cid in members:
            card = members[cid]
            # Check for ACTIVATED trigger
            if any(ab.trigger.name == "ACTIVATED" for ab in card.abilities):
                ability_card_id = cid
                hand_idx = i
                break

    # Sync Python GS for descriptions
    hand = list(gs.get_player(0).hand)
    py_gs.players[0].hand = hand
    py_gs.current_player = gs.current_player
    py_gs.phase = gs.phase

    # 3. Inject and Play Ability Card (Keke ID 247)
    target_cid = 247
    print(f"Injecting Card ID {target_cid} into hand...")
    # Update Rust State
    gs.get_player(0).hand = [target_cid] + list(gs.get_player(0).hand)
    # Update Python Stage for get_action_desc
    py_gs.players[0].hand = [target_cid] + list(py_gs.players[0].hand)

    # Check if card has an activated ability in py_gs
    card = members[target_cid]
    abs = [ab for ab in card.abilities if ab.trigger.name == "ACTIVATED"]
    print(f"Card {card.name} has {len(abs)} activated abilities.")
    for ab in abs:
        print(f" - Ability: {ab.raw_text}")

    print(f"Playing {get_action_desc(500, py_gs)} to Center...")
    # Action ID 2 (Hand 0 to Center)
    gs.step(2)

    # Update Python Stage
    py_gs.players[0].stage[1] = target_cid
    py_gs.players[0].hand = list(gs.get_player(0).hand)

    # Check legality
    def check_legal(gs, py_gs):
        legal_actions = list(gs.get_legal_action_ids())
        print(f"Phase: {gs.phase} | Legal IDs: {len(legal_actions)}")
        if 201 in legal_actions:
            print("SUCCESS: Action 201 (Center Ability) is legal.")
            return True
        print("Action 201 is NOT legal.")
        if len(legal_actions) < 20:  # Show only if list is small
            for a in legal_actions:
                print(f"  - Action {a}: {get_action_desc(a, py_gs)}")
        return False

    if not check_legal(gs, py_gs):
        print("Skipping to next turn's Main Phase...")
        # Finish Turn 1
        gs.step(0)  # End Main
        gs.step(0)  # End Live Start
        gs.step(0)  # End Live Set
        gs.step(0)  # End Performance
        gs.step(0)  # End Turn

        # Turn 2
        gs.step(0)  # End Active/Standby
        gs.step(0)  # End Draw

        # Now we should be in Turn 2 Main Phase
        # Re-sync Python GS
        py_gs.phase = gs.phase
        py_gs.current_player = gs.current_player

        check_legal(gs, py_gs)

    # 4. Run MCTS
    model_path = "ai/models/alphanet_best.onnx"
    mcts = engine_rust.PyHybridMCTS(model_path, 0.0)

    print("\nRunning MCTS (1600 sims)...")
    suggestions = mcts.get_suggestions(gs, 1600)

    print("\nTop MCTS Suggestions:")
    for action_id, score, visits in sorted(suggestions, key=lambda x: x[2], reverse=True)[:10]:
        desc = get_action_desc(int(action_id), py_gs)
        print(f"  Action {action_id:4}: {visits:5} visits | {score:.4f} score | {desc}")

    # 5. Final confirmation
    ability_actions = [a for (a, s, v) in suggestions if 200 <= a <= 202]
    if ability_actions:
        print(f"\nCONFIRMED: MCTS explored ability actions: {[int(a) for a in ability_actions]}")
        for a in ability_actions:
            print(f" - {get_action_desc(int(a), py_gs)}")
    else:
        print("\nISSUE: MCTS did NOT explore ability actions.")


if __name__ == "__main__":
    verify_abilities()
