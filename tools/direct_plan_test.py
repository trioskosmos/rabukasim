#!/usr/bin/env python3
"""Test plan_full_turn_with_stats directly to see if it works."""

import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent.parent))

from tools.compare_vanilla_strategies import VanillaComparison, ComparisonConfig
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config = ComparisonConfig(num_games=1, time_per_move=0.2)
comp = VanillaComparison(config)

# Create a game
game = comp._new_game(5000)

# Advance to Phase 4
while int(game.phase) != 4 and not game.is_terminal():
    legal_ids = [int(x) for x in game.get_legal_action_ids()]
    if legal_ids:
        action = int(legal_ids[0])
        game.step(action)

logger.info(f"Reached Phase {game.phase}, Turn {game.turn}")

# Try to plan
try:
    logger.info("Calling plan_full_turn_with_stats...")
    result = game.plan_full_turn_with_stats(comp.rust_db)
    logger.info(f"Result type: {type(result)}")
    logger.info(f"Result length: {len(result) if isinstance(result, tuple) else 'N/A'}")
    
    if isinstance(result, tuple) and len(result) >= 2:
        _, action_seq = result[0], result[1]
        logger.info(f"Action sequence: {action_seq}")
        logger.info(f"Action sequence type: {type(action_seq)}")
        logger.info(f"Action sequence length: {len(action_seq) if hasattr(action_seq, '__len__') else 'N/A'}")
    else:
        logger.info(f"Full result: {result}")
        
except Exception as e:
    logger.error(f"Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
