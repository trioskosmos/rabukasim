import concurrent.futures
import json

import engine_rust


def parse_deck(deck_file, member_db, live_db, energy_db):
    with open(deck_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    main_deck = []
    lives = []
    energy_deck = []

    db_map = {"member": member_db, "live": live_db, "energy": energy_db}

    for line in lines:
        line = line.strip()
        if not line or " x " not in line:
            continue

        parts = line.split(" x ")
        card_no = parts[0].strip()
        count = int(parts[1].strip())

        found_type = None
        found_id = None

        for db_type, db in db_map.items():
            for i, card in db.items():
                if card.get("card_no") == card_no:
                    found_id = int(i)
                    found_type = db_type
                    break
            if found_id is not None:
                break

        if found_id is not None:
            if found_type == "live":
                lives.extend([found_id] * count)
            elif found_type == "energy":
                energy_deck.extend([found_id] * count)
            else:
                main_deck.extend([found_id] * count)
        else:
            # Fallback for Energy if it's named like one or matches known patterns
            if "energy" in card_no.lower() or "sd1-036" in card_no.lower():
                default_energy_id = 20000  # Use new offset
                energy_deck.extend([default_energy_id] * count)
            else:
                print(f"Warning: Card {card_no} not found in DB")

    return main_deck, lives, energy_deck


def run_benchmark(deck_name, deck_file, db_content, sims=100):
    db_json = json.loads(db_content)
    member_db = db_json["member_db"]
    live_db = db_json["live_db"]
    energy_db = db_json.get("energy_db", {})

    main_deck, lives, energy_deck = parse_deck(deck_file, member_db, live_db, energy_db)

    # Padding/Trimming to standard sizes if needed
    test_lives = lives[:12]
    test_deck = main_deck[:48]  # Rule 6.1.1.1
    test_energy = energy_deck[:12]  # Rule 6.1.1.3

    db = engine_rust.PyCardDatabase(db_content)
    game = engine_rust.PyGameState(db)

    game.initialize_game(test_deck, test_deck, test_energy, test_energy, test_lives, test_lives)

    turn_limit = 10
    step = 0
    while not game.is_terminal() and game.turn <= turn_limit and step < 1000:
        cp = game.current_player
        phase = game.phase
        is_interactive = phase in [-1, 0, 4, 5]

        if is_interactive:
            # Use TurnEnd horizon specifically for this bench
            suggestions = game.get_mcts_suggestions(sims, engine_rust.SearchHorizon.TurnEnd)
            best_action = suggestions[0][0]
            game.step(best_action)
        else:
            game.step(0)
        step += 1

    p0 = game.get_player(0)
    return {
        "deck": deck_name,
        "score": p0.score,
        "lives_cleared": len(p0.success_lives),
        "turns": game.turn,
        "steps": step,
    }


def main():
    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        db_content = f.read()

    deck_files = {
        "Aqours": "ai/decks/aqours_cup.txt",
        "Hasunosora": "ai/decks/hasunosora_cup.txt",
        "Liella": "ai/decks/liella_cup.txt",
        "Muse": "ai/decks/muse_cup.txt",
        "Nijigasaki": "ai/decks/nijigaku_cup.txt",
    }

    print(f"{'Deck':<12} | {'Score':<5} | {'Lives':<5} | {'Turns':<5}")
    print("-" * 40)

    # Run in parallel to save time
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = {
            executor.submit(run_benchmark, name, path, db_content, 50): name for name, path in deck_files.items()
        }
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            print(f"{res['deck']:<12} | {res['score']:<5} | {res['lives_cleared']:<5} | {res['turns']:<5}")


if __name__ == "__main__":
    main()
