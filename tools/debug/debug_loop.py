import engine_rust

# Load DB
with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
    db_content = f.read()
db = engine_rust.PyCardDatabase(db_content)

# Fixed Starter Decks (SD1)
p0_deck = [124, 127, 130, 132] * 5
p1_deck = [124, 127, 130, 132] * 5
# Lives (SD1)
p_lives = [1024, 1025, 1027]
p_energy = [0] * 10

game = engine_rust.PyGameState(db)
game.initialize_game(p0_deck, p1_deck, p_energy, p_energy, p_lives, p_lives)

print(f"Initial Phase: {game.phase}")

last_p = -1
last_cp = -1
last_turn = -1

step = 0
while not game.is_terminal() and step < 1500:
    cp = game.current_player
    phase = game.phase
    turn = game.turn
    is_interactive = phase in [-1, 0, 4, 5]

    if phase != last_p or cp != last_cp or turn != last_turn:
        print(f"Step {step}: Turn {turn}, Player {cp}, Phase {phase}, Interactive={is_interactive}")
        last_p = phase
        last_cp = cp
        last_turn = turn

    if is_interactive:
        suggestions = game.get_mcts_suggestions(50, engine_rust.SearchHorizon.TurnEnd)  # 50 sims
        best_action = suggestions[0][0]
        # print(f"  Action: {best_action}")
        game.step(best_action)
    else:
        game.step(0)

    step += 1

print(f"Final Step {step}: Phase {game.phase}, Terminal={game.is_terminal()}")
if game.is_terminal():
    print(f"Winner: {game.get_winner()}")
