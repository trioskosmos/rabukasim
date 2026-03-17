#!/usr/bin/env python3
"""
Debug TurnSeq caching to understand why Phase 5 actions aren't being used.
Traces exactly what's cached and when it's used.
"""

import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent.parent))

from pathlib import Path
import logging
from tools.compare_vanilla_strategies import VanillaComparison, ComparisonConfig

logging.basicConfig(level=logging.DEBUG, format='%(message)s')
logger = logging.getLogger(__name__)

# Create a minimal game
config = ComparisonConfig(num_games=1, time_per_move=0.2)
comp = VanillaComparison(config)

# Load a game
db = comp.rust_db
decks = comp.decks
initial_deck = decks[0]

# Create game with fixed seed
game = comp._new_game(5000)

# Trace through moves
logger.info("=" * 80)
logger.info("TRACING TURNSEQ CACHING BEHAVIOR")
logger.info("=" * 80)

move_count = 0
while not game.is_terminal():
    phase = int(game.phase)
    turn = int(game.turn)
    legal_ids = [int(x) for x in game.get_legal_action_ids()]
    
    if len(legal_ids) == 0:
        break
    
    move_count += 1
    
    # Only trace Phase 4 and Phase 5 moves
    if phase in (4, 5):
        logger.info(f"\n--- Move #{move_count}: Phase {phase}, Turn {turn} ---")
        logger.info(f"    Legal IDs: {legal_ids[:5]}{'...' if len(legal_ids) > 5 else ''}")
        
        # BEFORE calling strategy
        cache_keys_before = list(comp.turnseq_plan_cache.keys())
        logger.info(f"    Cache before: {cache_keys_before}")
        
        # Call TurnSeq
        action = comp._choose_turnseq_action(game, legal_ids, time_limit=0.2)
        logger.info(f"    TurnSeq chose: {action}")
        
        # AFTER calling strategy
        cache_keys_after = list(comp.turnseq_plan_cache.keys())
        logger.info(f"    Cache after:  {cache_keys_after}")
        
        # Show cache contents
        for key in cache_keys_after:
            val = comp.turnseq_plan_cache[key]
            if isinstance(val, list):
                logger.info(f"      {key}: {val[:3] if len(val) > 3 else val}")
            else:
                logger.info(f"      {key}: {val}")
    else:
        # Just get a quick action
        legal_ids_int = [int(x) for x in legal_ids]
        action = comp._choose_random_action(game, legal_ids_int)
    
    # Advance game
    game.step(int(action))
    
    # Stop after decent number of moves
    if move_count > 40:
        break

logger.info("\n" + "=" * 80)
logger.info(f"Stopped at move {move_count}")
logger.info("=" * 80)
