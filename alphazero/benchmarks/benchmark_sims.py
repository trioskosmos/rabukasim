import json
import random
import sys
import time
from pathlib import Path

# Add root for engine
sys.path.insert(0, str(Path(__file__).parent.parent))

import engine_rust

from engine.game.deck_utils import UnifiedDeckParser, load_deck_from_file


def load_decks(full_db):
    decks_dir = Path(__file__).parent.parent / "ai" / "decks"
    parser = UnifiedDeckParser(full_db)
    loaded_decks = []

    for deck_file in decks_dir.glob("*.txt"):
        main, energy, counts, errs = load_deck_from_file(str(deck_file), full_db)
        if not main:
            continue

        m, l, e = [], [], []
        for code in main:
            cdata = parser.resolve_card(code)
            if not cdata:
                continue
            if cdata.get("type") == "Member":
                m.append(cdata["card_id"])
            elif cdata.get("type") == "Live":
                l.append(cdata["card_id"])

        for code in energy:
            cdata = parser.resolve_card(code)
            if cdata:
                e.append(cdata["card_id"])

        if len(m) >= 30:
            loaded_decks.append({"members": m, "lives": l, "energy": e})
    return loaded_decks


def play_match(sims_p0, sims_p1, decks, db_engine):
    d0 = random.choice(decks)
    d1 = random.choice(decks)
    state = engine_rust.PyGameState(db_engine)
    state.initialize_game(d0["members"] + d0["lives"], d1["members"] + d1["lives"], d0["energy"], d1["energy"], [], [])
    state.silent = True

    start_time = time.time()
    while not state.is_terminal() and state.turn < 100:
        sims = sims_p0 if state.current_player == 0 else sims_p1
        legal_ids = state.get_legal_action_ids()
        if not legal_ids:
            break

        res = state.get_mcts_suggestions(
            sims, 1.41, engine_rust.SearchHorizon.GameEnd(), engine_rust.EvalMode.TerminalOnly
        )

        acts = [s[0] for s in res]
        vts = [s[2] for s in res]

        try:
            if not acts or sum(vts) == 0:
                action = random.choice(legal_ids)
            else:
                action = random.choices(acts, weights=vts, k=1)[0]
        except Exception:
            action = random.choice(legal_ids)

        state.step(action)
        state.auto_step(db_engine)

    return state.get_winner(), time.time() - start_time, state.turn


def analyze_sims():
    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        full_db = json.load(f)
    db_engine = engine_rust.PyCardDatabase(json.dumps(full_db))
    decks = load_decks(full_db)

    matchups = [(512, 128), (512, 256), (256, 128)]
    games_per_matchup = 10  # 10 games each for a quick statistical check

    print("--- MCTS SIMULATIONS: DEEP DIVE ANALYSIS ---")
    print("Evaluating how much 'intellectual depth' we actually lose by reducing sims.")

    for s0, s1 in matchups:
        print(f"\n--- MATCHUP: {s0} Sims (P0) vs {s1} Sims (P1) ---")
        wins_s0 = 0
        wins_s1 = 0
        draws = 0
        total_time = 0
        total_turns = 0

        for i in range(games_per_matchup):
            # Alternate who goes first to prevent First-Player Advantage bias
            p0, p1 = (s0, s1) if i % 2 == 0 else (s1, s0)

            winner, dt, turns = play_match(p0, p1, decks, db_engine)

            if winner == 0:
                if p0 == s0:
                    wins_s0 += 1
                else:
                    wins_s1 += 1
            elif winner == 1:
                if p1 == s0:
                    wins_s0 += 1
                else:
                    wins_s1 += 1
            else:
                draws += 1

            total_time += dt
            total_turns += turns
            print(f"Game {i + 1} done. ({dt:.1f}s)")

        print(f"Results: {s0} Sims won {wins_s0} | {s1} Sims won {wins_s1} | Draws: {draws}")
        print(
            f"Avg Time/Game: {total_time / games_per_matchup:.1f}s | Avg Turns/Game: {total_turns / games_per_matchup:.1f}"
        )


if __name__ == "__main__":
    analyze_sims()
