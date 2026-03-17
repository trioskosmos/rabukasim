"""Debug what plan_full_turn_with_stats() actually returns."""
import sys
import json
import random
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from engine_rust.engine_rust import PyCardDatabase, PyGameState
import logging

logging.basicConfig(level=logging.DEBUG, format='%(name)s: %(message)s')
logger = logging.getLogger('DEBUG')

# Load database and start game
with open(ROOT_DIR / "data" / "cards_vanilla.json", "r", encoding="utf-8") as f:
    db_json = f.read()
db = PyCardDatabase(db_json)
db.is_vanilla = True

# Create a game
game = PyGameState(db)

# Load a simple deck
with open(ROOT_DIR / "data" / "cards_vanilla.json", "r", encoding="utf-8") as f:
    card_data = json.load(f)
simple_deck = [card_data["cards"][0]["id"]] * 50

game.initialize_game_with_seed(
    simple_deck,
    simple_deck,
    0.0,
    0.0,
    [],
    [],
    5000,
)
game.silent = True
game.debug_mode = False

# Play through to Phase 4, Turn 0
for _ in range(4):
    game.make_decision(20000, db)  # RPS decisions
game.make_decision(20000, db)  # Turn order

# Skip to Phase 4 Turn 0
while game.phase != 4 or game.turn != 0:
    legal = list(game.get_legal_actions())
    if legal:
        game.make_decision(legal[0], db)
    else:
        break

logger.info(f"At Phase {game.phase}, Turn {game.turn}")
logger.info(f"Legal actions: {list(game.get_legal_actions())}")

# Now try planning
logger.info("Calling plan_full_turn_with_stats()...")
result = game.plan_full_turn_with_stats(db)
if result:
    _, action_seq, heuristic_score, diagnostics, extra = result
    logger.info(f"Plan returned {len(action_seq)} actions: {list(action_seq)}")
    logger.info(f"Heuristic score: {heuristic_score}")
    logger.info(f"Diagnostics: {diagnostics}")
    logger.info(f"Extra: {extra}")
else:
    logger.info("Plan returned None")

# Try calling it again
logger.info("\nCalling plan_full_turn_with_stats() again from same position...")
result2 = game.plan_full_turn_with_stats(db)
if result2:
    _, action_seq2, heuristic_score2, diagnostics2, extra2 = result2
    logger.info(f"Plan 2 returned {len(action_seq2)} actions: {list(action_seq2)}")
    logger.info(f"Heuristic score 2: {heuristic_score2}")
else:
    logger.info("Plan 2 returned None")

# Try planning at different phase
logger.info(f"\n=== Making a Phase 4 decision to move forward ===")
if action_seq and len(action_seq) > 0:
    first_action = int(action_seq[0])
    logger.info(f"Making move {first_action}")
    game.make_decision(first_action, db)
    logger.info(f"Now at Phase {game.phase}, Turn {game.turn}")
    logger.info(f"Legal actions: {list(game.get_legal_actions())}")
    
    # Try planning again now
    result3 = game.plan_full_turn_with_stats(db)
    if result3:
        _, action_seq3, heuristic_score3, diagnostics3, extra3 = result3
        logger.info(f"Plan 3 returned {len(action_seq3)} actions: {list(action_seq3)}")
    else:
        logger.info("Plan 3 returned None")
