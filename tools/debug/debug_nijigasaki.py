import json

import engine_rust


def debug_nijigasaki():
    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        db_content = f.read()
    db_json = json.loads(db_content)

    # Load Nijigasaki deck
    from ai.benchmark_decks import parse_deck

    main_deck, lives = parse_deck("ai/decks/nijigaku_cup.txt", db_json["member_db"], db_json["live_db"])

    test_lives = lives[:3]
    test_deck = (main_deck * 2)[:30]

    db = engine_rust.PyCardDatabase(db_content)
    game = engine_rust.PyGameState(db)

    p_energy = [0] * 10
    game.initialize_game(test_deck, test_deck, p_energy, p_energy, test_lives, test_lives)

    print(f"Initial Phase: {game.phase}, Turn: {game.turn}")

    step = 0
    while not game.is_terminal() and step < 200:
        cp = game.current_player
        phase = game.phase
        turn = game.turn
        is_interactive = phase in [-1, 0, 4, 5]

        if is_interactive:
            suggestions = game.get_mcts_suggestions(50, engine_rust.SearchHorizon.TurnEnd)
            best_action = suggestions[0][0]
            print(f"Step {step}: Turn {turn}, Player {cp}, Phase {phase}, Action {best_action}")
            game.step(best_action)
        else:
            game.step(0)

        step += 1

        if game.is_terminal():
            print(f"Reached Terminal at Step {step}, Turn {game.turn}")
            break

    p0 = game.get_player(0)
    print(f"Result: Score {p0.score}, Lives {len(p0.success_lives)}")
    for i, cid in enumerate(p0.success_lives):
        print(f"  Live Success {i}: ID {cid}")


if __name__ == "__main__":
    debug_nijigasaki()
