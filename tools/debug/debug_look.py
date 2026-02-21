import os
import sys

import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from game.game_state import GameState, MemberCard


def test():
    game = GameState(verbose=True)
    p0 = game.players[0]

    # Setup Deck
    print("Setting up deck...")
    p0.main_deck = list(range(1, 11))
    for i in range(1, 11):
        game.member_db[i] = MemberCard(
            card_id=i,
            card_no=f"M{i}",
            name=f"Member {i}",
            cost=1,
            hearts=np.zeros(6),
            blade_hearts=np.zeros(6),
            blades=1,
            group="Group",
            unit="",
            img_path="",
        )

    print(f"Deck: {p0.main_deck}")

    # 1. Look Deck
    game.looked_cards = []
    for _ in range(5):
        if p0.main_deck:
            game.looked_cards.append(p0.main_deck.pop(0))
    print(f"Looked Cards: {game.looked_cards}")

    # 2. Setup Choice
    # Manual setup mimicking _resolve_pending_effect
    candidates = game.looked_cards.copy()
    game.pending_choices.append(("SELECT_FROM_LIST", {"cards": candidates, "reason": "look_and_choose"}))
    print("Choice setup complete.")

    # 3. Execute
    action_id = 602  # Index 2 -> Card 3
    print(f"Executing action {action_id}...")
    game = game.step(action_id)
    p0 = game.players[0]

    print(f"Hand: {p0.hand}")
    print(f"Discard: {p0.discard}")
    print(f"Looked (Game): {game.looked_cards}")

    if 3 in p0.hand:
        print("PASS: Card 3 in hand")
    else:
        print("FAIL: Card 3 not in hand")

    if set(p0.discard) == {1, 2, 4, 5}:
        print("PASS: Discard correct")
    else:
        print("FAIL: Discard incorrect")


if __name__ == "__main__":
    test()
