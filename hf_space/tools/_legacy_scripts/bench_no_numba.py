import random
import time

import numpy as np

# Force Numba to be unavailable
import engine.game.numba_utils

engine.game.numba_utils.JIT_AVAILABLE = False

from engine.game.enums import Phase
from engine.game.game_state import GameState


def init_state(gs, members, lives):
    p0_deck = list(members.keys())[:40]
    p1_deck = list(members.keys())[40:80]
    p0_lives = list(lives.keys())[:20]
    p1_lives = list(lives.keys())[20:40]

    for i, p in enumerate(gs.players):
        deck = p0_deck if i == 0 else p1_deck
        lives_data = p0_lives if i == 0 else p1_lives

        p.main_deck = list(deck)
        random.shuffle(p.main_deck)

        # Draw 6
        p.hand = [p.main_deck.pop() for _ in range(6)]

        # Energy 3
        p.energy_deck = list(deck)
        random.shuffle(p.energy_deck)
        for _ in range(3):
            p.energy_zone.append(p.energy_deck.pop())

        # Lives
        p.live_zone = list(lives_data)[:3]
        p.live_zone_revealed = [False] * 3

    gs.phase = Phase.MAIN


def main():
    json_path = "data/cards_compiled.json"
    print(f"Loading cards from {json_path}...")

    from engine.game.data_loader import CardDataLoader

    loader = CardDataLoader(json_path)
    members, lives, energy = loader.load()

    GameState.member_db = members
    GameState.live_db = lives

    print(f"Database loaded. Members: {len(members)}")

    iterations = 1000
    print(f"Starting benchmark (NO NUMBA) for {iterations} steps...")

    gs = GameState(verbose=False, suppress_logs=True)
    init_state(gs, members, lives)

    start = time.perf_counter()

    steps = 0
    while steps < iterations:
        mask = gs.get_legal_actions()
        legal_indices = np.where(mask == 1)[0]

        if len(legal_indices) == 0:
            init_state(gs, members, lives)
            continue

        action_idx = legal_indices[steps % len(legal_indices)]
        gs.step(action_idx)

        steps += 1
        if gs.is_terminal:
            init_state(gs, members, lives)

    duration = time.perf_counter() - start
    print(f"Completed {steps} steps in {duration:.4f}s")
    print(f"Average time per step: {duration * 1000 / steps:.4f} ms")
    print(f"Steps per second: {steps / duration:.2f}")


if __name__ == "__main__":
    main()
