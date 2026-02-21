import os
import sys

sys.path.append(os.getcwd())
import traceback

from engine.game.game_state import initialize_game


def main():
    print("DEBUG: Initializing game...")
    game = initialize_game(deck_type="training")

    cno = "PL!N-bp4-023-N"
    cid = -1
    for k, v in game.member_db.items():
        if v.card_no == cno:
            cid = k
            break

    if cid == -1:
        print(f"DEBUG: Card {cno} not found!")
        return

    print(f"DEBUG: Found card ID {cid}")
    player = game.players[0]

    # Setup
    # card_inst = game.member_db[cid] # Don't need object
    player.hand.append(cid)
    card_idx = len(player.hand) - 1

    # Infinite energy
    player.energy_zone = [game.member_db[cid] for _ in range(10)]

    prev_deck = len(player.main_deck)
    print(f"DEBUG: Prev Deck: {prev_deck}, Hand: {len(player.hand)}")

    game.phase = 4
    game.turn_player = 0
    game.current_player = 0

    print("DEBUG: Playing member...")
    try:
        game._play_member(hand_idx=card_idx, area_idx=0)
    except Exception as e:
        print(f"DEBUG: Play failed: {e}")
        traceback.print_exc()
        return

    print(f"DEBUG: Triggered Abilities Queue: {len(game.triggered_abilities)}")

    print("DEBUG: Processing rules/triggers...")
    game._process_rule_checks()

    curr_deck = len(player.main_deck)
    print(f"DEBUG: Curr Deck: {curr_deck}, Hand: {len(player.hand)}")

    val = 1
    if curr_deck == prev_deck - val:
        print("DEBUG: SUCCESS! Deck decreased by 1")
    else:
        print(f"DEBUG: FAILURE! Deck change {prev_deck} -> {curr_deck} (Expected -{val})")


if __name__ == "__main__":
    main()
