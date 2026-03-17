#!/usr/bin/env python3
"""Understand what plan_full_turn_with_stats returns."""

import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent.parent))

from tools.compare_vanilla_strategies import VanillaComparison, ComparisonConfig
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config = ComparisonConfig(num_games=1, time_per_move=0.2)
comp = VanillaComparison(config)

game = comp._new_game(5000)
move_count = 0

# Advance to a Phase 4/5 transition
while move_count < 30:
    phase = int(game.phase)
    turn = int(game.turn)
    legal_ids = [int(x) for x in game.get_legal_action_ids()]
    
    if phase == 4 and move_count % 5 == 0:  # Sample a few Phase 4 states
        logger.info(f"\n--- At Phase {phase}, Turn {turn} ---")
        logger.info(f"Legal IDs: {legal_ids}")
        
        try:
            _, action_seq, score, diag, extra = game.plan_full_turn_with_stats(comp.rust_db)
            logger.info(f"Plan returned {len(action_seq)} actions:")
            logger.info(f"  Sequence: {action_seq}")
            
            # Analyze the sequence
            phase4_ids = {x for x in action_seq if 1000 <= x < 2000}
            phase5_ids = {x for x in action_seq if 400 <= x < 500}
            passes = [x for x in action_seq if x == 0]
            
            logger.info(f"  Phase 4 action IDs (1000-1999): {phase4_ids or 'none'}")
            logger.info(f"  Phase 5 action IDs (400-499): {phase5_ids or 'none'}")
            logger.info(f"  Passes (0): {len(passes)}")
            
        except Exception as e:
            logger.error(f"Error: {e}")
    
    if len(legal_ids) > 0:
        action = legal_ids[0]
        game.step(action)
        move_count += 1
    else:
        break

logger.info("\nDone!")
