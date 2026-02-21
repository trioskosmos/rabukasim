import os
import sys

# Add workspace to path
sys.path.append(os.getcwd())

from compiler.parser_v2 import parse_ability_text
from engine.game.game_state import GameState


def test_kasumi_ability():
    # 1. Setup Game State
    gs = GameState(verbose=True)
    gs.players[0].main_deck = [101]  # Active deck top
    gs.players[1].main_deck = [201]  # Opponent deck top

    text = "自分か相手を選ぶ。自分は、そのプレイヤーのデッキの一番上のカードを見る。自分はそのカードを控え室に置いてもよい。"
    abilities = parse_ability_text(text)
    kasumi_ability = abilities[0]

    print(f"Parsed Ability Text: {kasumi_ability.raw_text}")
    print(f"Bytecode: {kasumi_ability.compile()}")

    # 2. Simulate "Choose Opponent" (Option 2 of SELECT_MODE)
    # The parser transforms this into SELECT_MODE with 2 options
    gs.current_player = 0
    gs.pending_effects.append(kasumi_ability.compile())

    # Trigger resolution
    gs.take_action(0)  # Resolve Ability block -> SELECT_MODE choice pushed

    print(f"\nPending choices: {[c[0] for c in gs.pending_choices]}")

    # Choose Option 2 (Opponent)
    # Action 571 = Choice index 1
    gs._handle_choice(571)

    # Resolve Option 2 Effects
    print(f"Pending effects count: {len(gs.pending_effects)}")
    gs.take_action(0)  # Resolve Option 2

    print(f"Looked cards: {gs.looked_cards} (Should be [201])")
    assert gs.looked_cards == [201]
    assert len(gs.players[1].main_deck) == 0  # Popped from deck

    print(f"Pending choices: {[c[0] for c in gs.pending_choices]} (Should be [SELECT_FROM_LIST])")

    # Simulate Discard (Action 600 = Card at index 0)
    gs._handle_choice(600)
    print(f"Opponent discard: {gs.players[1].discard} (Should be [201])")
    assert 201 in gs.players[1].discard

    # 3. Simulate "Choose Yourself" and "Decline Discard"
    gs.players[0].main_deck = [102]
    gs.players[0].discard = []
    gs.pending_effects.append(kasumi_ability.compile())

    gs.take_action(0)  # SELECT_MODE
    gs._handle_choice(570)  # Choice Yourself

    gs.take_action(0)  # Resolve Option 1

    print(f"\nLooked cards: {gs.looked_cards} (Should be [102])")
    assert gs.looked_cards == [102]

    gs._handle_choice(0)  # Decline (Action 0)
    print(f"Active deck: {gs.players[0].main_deck} (Should be [102] put back)")
    assert gs.players[0].main_deck == [102]
    assert len(gs.players[0].discard) == 0

    print("\nTEST PASSED successfully!")


if __name__ == "__main__":
    test_kasumi_ability()
