import json
import os
import time

import engine_rust


def load_deck(deck_path: str, card_map: dict[str, int]) -> list[int]:
    deck_ids = []
    with open(deck_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("x")
            if len(parts) >= 1:
                card_no = parts[0].strip()
                count = 1
                if len(parts) > 1:
                    try:
                        count = int(parts[1].strip())
                    except ValueError:
                        pass

                if card_no in card_map:
                    cid = card_map[card_no]
                    deck_ids.extend([cid] * count)
                else:
                    print(f"Warning: Card {card_no} not found in database")
    return deck_ids


def run_deathmatch(num_games=20, sims=1000):
    print(f"Starting Deathmatch: Zero-Rollout vs Standard ({num_games} games, {sims} sims)")

    # Path handling
    cards_path = "data/cards_compiled.json"
    if not os.path.exists(cards_path):
        print(f"Error: {cards_path} not found.")
        return

    with open(cards_path, "r", encoding="utf-8") as f:
        db_content = f.read()
        db_json = json.loads(db_content)

    # Build Card Map
    card_map = {}

    def process_db(db_section):
        for cid, data in db_section.items():
            c_no = data.get("card_no")
            c_id = data.get("card_id")
            if c_no and c_id is not None:
                card_map[c_no] = c_id

    process_db(db_json.get("member_db", {}))
    process_db(db_json.get("live_db", {}))
    process_db(db_json.get("energy_db", {}))

    db = engine_rust.PyCardDatabase(db_content)

    # Load Deck
    deck_path = "ai/decks/muse_cup.txt"
    if not os.path.exists(deck_path):
        print(f"Error: {deck_path} not found.")
        return

    full_deck = load_deck(deck_path, card_map)

    # Split
    p_deck = []
    p_energy = []
    p_lives = []

    for cid in full_deck:
        if cid >= 40000:
            p_energy.append(cid)
        elif cid >= 30000:
            p_lives.append(cid)
        else:
            p_deck.append(cid)

    # Stats
    # P0 = Zero Rollout
    # P1 = Standard
    wins = {0: 0, 1: 0, 2: 0}
    total_time = 0

    for i in range(num_games):
        g = engine_rust.PyGameState(db)
        seed = 2000 + i
        swap = i % 2 == 1

        # Initialize
        deck_u16 = [int(x) for x in p_deck]
        energy_u16 = [int(x) for x in p_energy]
        live_u16 = [int(x) for x in p_lives]

        # Ensure we have enough cards? The deck files usually have 40+10+5
        # If not, fill with 0? No, rely on valid deck.

        g.initialize_game_with_seed(deck_u16, deck_u16, energy_u16, energy_u16, live_u16, live_u16, seed)

        start_game = time.time()

        # P0=Zero(NoRollout), P1=Standard(Rollout)
        if not swap:
            # P0 is Player 0, P1 is Player 1
            winner, turns = g.play_asymmetric_match(
                db,
                sims,
                sims,
                0,
                0,
                engine_rust.SearchHorizon.TurnEnd,
                False,
                True,  # P0=False(Zero), P1=True(Standard)
            )
            actual_winner = winner
        else:
            # P0 is Player 1, P1 is Player 0
            # We want P0 to be ZeroRollout. But here we swap SEATS.
            # So Seat 0 gets Standard (Rollout=True), Seat 1 gets Zero (Rollout=False)
            winner, turns = g.play_asymmetric_match(
                db,
                sims,
                sims,
                0,
                0,
                engine_rust.SearchHorizon.TurnEnd,
                True,
                False,  # P0(Seat0)=True(Standard), P1(Seat1)=False(Zero)
            )
            # Map back to our logical P0/P1
            if winner == 0:
                actual_winner = 1  # Standard won
            elif winner == 1:
                actual_winner = 0  # Zero won
            else:
                actual_winner = 2

        if actual_winner == -1:
            actual_winner = 2

        wins[actual_winner] += 1
        duration = time.time() - start_game
        total_time += duration

        w_str = "Zero-Rollout" if actual_winner == 0 else "Standard" if actual_winner == 1 else "Draw"
        print(f"Game {i + 1}/{num_games}: Winner={w_str}, Turns={turns}, Time={duration:.2f}s")

    print(f"\nResults over {num_games} games:")
    print(f"Zero-Rollout Wins: {wins[0]}")
    print(f"Standard Wins:     {wins[1]}")
    print(f"Draws:             {wins[2]}")
    print(f"Avg Time:          {total_time / num_games:.2f}s")


if __name__ == "__main__":
    run_deathmatch(20, 1000)
