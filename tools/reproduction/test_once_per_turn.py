import os
import sys
import json
import traceback

# --- PATH SETUP ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if os.path.join(PROJECT_ROOT, "engine") not in sys.path:
    sys.path.insert(0, os.path.join(PROJECT_ROOT, "engine"))

import engine_rust
from backend.rust_serializer import RustGameStateSerializer
from game.data_loader import CardDataLoader


def run_test():
    log_file = os.path.join(PROJECT_ROOT, "test_output.log")
    with open(log_file, "w", encoding="utf-8") as out:

        def log(msg):
            print(msg)
            out.write(msg + "\n")
            out.flush()  # Ensure output is written immediately

        log("=" * 60)
        log("TEST: ON_REVEAL Once Per Turn Enforcement")
        log("=" * 60)

        try:
            # 1. Load Data
            # We load the master card data to fetch specific members and live cards.
            # We also read 'cards_compiled.json' which contains the actual engine bytecode.
            log("Checkpoint: Loading Data...")
            loader = CardDataLoader("data/cards.json")
            m_db, l_db, e_db = loader.load()
            log(f"Checkpoint: Data Loaded. Members: {len(m_db)}")

            with open(os.path.join(PROJECT_ROOT, "data/cards_compiled.json"), "r", encoding="utf-8") as f:
                compiled_json_str = f.read()
            log("Checkpoint: Compiled Data Read.")

            # 2. Initialize Game Engine
            # We initialize the Rust-backed PyGameState with the compiled card database.
            rust_db = engine_rust.PyCardDatabase(compiled_json_str)
            gs = engine_rust.PyGameState(rust_db)
            log("Checkpoint: Engine Initialized.")

            # 3. Setup Minimal Game State
            # Decks, Energy, and Lives are required for the engine to initialize properly.
            plinth_cid = 1368
            energy_cid = 40000
            p0_deck = [plinth_cid] * 60
            p1_deck = [plinth_cid] * 60
            p0_energy = [energy_cid] * 60
            p1_energy = [energy_cid] * 60
            p0_lives = [l for l in l_db.keys()][:3]
            p1_lives = [l for l in l_db.keys()][:3]
            gs.initialize_game(p0_deck, p1_deck, p0_energy, p1_energy, p0_lives, p1_lives)

            # 4. Prepare conditions for ON_REVEAL ability (Card 977)
            # Conditions for 977 (Rin): Live in revealed zone & Hand <= 7.
            cid = 977

            # Meet Condition A: Set a live card in the revealed cards zone.
            live_cid = list(l_db.keys())[0]
            gs.set_revealed_cards(0, [live_cid])

            # Meet Condition B: Empty the hand.
            gs.set_hand_cards(0, [])

            # Setup Trigger Location: Place the card in the discard pile.
            # This allows trigger_ability_on_card(..., slot_idx=100) to find it.
            gs.set_discard_cards(0, [cid])

            log(f"Initial hand size: {len(gs.get_player(0).hand)}")
            log(f"Discard pile: {gs.get_player(0).discard}")
            log(f"Revealed cards: {gs.get_player(0).revealed_cards}")

            # 4.5 Attempt 0: Failed Condition (Should NOT consume Once Per Turn)
            # We temporarily remove the revealed live card to make the condition fail.
            log("\n--- Triggering ON_REVEAL (Attempt 0, Condition Fails) ---")
            gs.set_revealed_cards(0, [])  # Clear revealed zone
            try:
                gs.trigger_ability_on_card(0, cid, 100, 0)
                log("FAILURE: Ability should have failed due to conditions.")
            except ValueError as e:
                log(f"SUCCESS: Caught expected condition error: {e}")

            # Restore the condition
            gs.set_revealed_cards(0, [live_cid])
            log("Restored revealed card condition.")

            # 5. First Activation (Valid)
            # This should still work because the failed attempt 0 should not have consumed the flag.
            log("\n--- Triggering ON_REVEAL (Attempt 1, After failed condition) ---")
            gs.trigger_ability_on_card(0, cid, 100, 0)

            log(f"Hand size after Attempt 1: {len(gs.get_player(0).hand)}")
            if len(gs.get_player(0).hand) == 1:
                log("SUCCESS: Card drawn. (OPT was NOT consumed by the failed condition check)")
            else:
                log("FAILURE: Card not drawn. (Did the failed condition consume the flag?)")

            # 6. Second Activation (Same Turn - SHOULD FAIL)
            # The engine's OPT enforcement logic should throw an error here.
            log("\n--- Triggering ON_REVEAL (Attempt 2, Same Turn) ---")
            try:
                gs.trigger_ability_on_card(0, cid, 100, 0)
                log("FAILURE: Second activation should have failed.")
            except Exception as e:
                # Success here means the engine caught the double-trigger!
                log(f"SUCCESS: Caught expected error: {e}")

            log(f"Hand size after Attempt 2: {len(gs.get_player(0).hand)}")
            if len(gs.get_player(0).hand) == 1:
                log("SUCCESS: Once Per Turn enforced (no second draw).")
            else:
                log("FAILURE: Card drawn again or logic failed.")

            # 7. Verification of Flag Reset
            # Clearing OPT flags manually simulates a new turn.
            log("\n--- Clearing Once Per Turn Flags and Triggering Again ---")
            gs.clear_once_per_turn_flags(0)

            log("\n--- Triggering ON_REVEAL (Attempt 3, Reset flags) ---")
            gs.trigger_ability_on_card(0, cid, 100, 0)

            log(f"Hand size after Attempt 3: {len(gs.get_player(0).hand)}")
            if len(gs.get_player(0).hand) == 2:
                log("SUCCESS: Ability works again after flag reset.")
            else:
                log(f"FAILURE: Ability blocked after flag reset. Hand size: {len(gs.get_player(0).hand)}")

        except Exception:
            log(traceback.format_exc())


if __name__ == "__main__":
    run_test()
