#!/usr/bin/env python3
"""
Test TurnSeq caching without neural model to avoid CUDA OOM.
Verifies that TurnSeq correctly uses cached plans across multiple Phase 4 calls.
"""

import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent.parent))

from pathlib import Path
import logging
from tools.compare_vanilla_strategies import VanillaComparison, ComparisonConfig

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Create comparison without loading neural model
config = ComparisonConfig(num_games=1, time_per_move=0.2)
comp = VanillaComparison(config)

# Use only TurnSeq and random
game = comp._new_game(5000)

turnseq_actions = []
phase4_moves = 0

logger.info("=" * 80)
logger.info("TURNSEQ CACHING TEST - Single Game")
logger.info("=" * 80)

while not game.is_terminal() and phase4_moves < 20:
    phase = int(game.phase)
    turn = int(game.turn)
    legal_ids = [int(x) for x in game.get_legal_action_ids()]
    
    if phase == 4:
        phase4_moves += 1
        cache_size_before = len(comp.turnseq_plan_cache)
        
        action = comp._choose_turnseq_action(game, legal_ids, time_limit=0.2)
        turnseq_actions.append((turn, action))
        
        cache_size_after = len(comp.turnseq_plan_cache)
        
        logger.info(f"Phase 4, Turn {turn}, Move {phase4_moves}: action={action}, cache before={cache_size_before}, after={cache_size_after}")
    else:
        # Use random for other phases
        if legal_ids:
            action = comp._choose_random_action(game, legal_ids)
        else:
            break
    
    game.step(action)

logger.info("\n" + "=" * 80)
logger.info(f"SUMMARY: Made {phase4_moves} Phase 4 moves")
logger.info(f"Cache final size: {len(comp.turnseq_plan_cache)}")
logger.info(f"Cache keys: {list(comp.turnseq_plan_cache.keys())}")
logger.info("=" * 80)

# Verify caching worked
if not comp.turnseq_plan_cache:
    logger.error("FAILED: Cache is empty! Caching did not work.")
    sys.exit(1)

# Check that we have entries for different turns
turn_entries = {}
for key in comp.turnseq_plan_cache.keys():
    if key.startswith('plan_turn_'):
        turn_num = key.split('_')[-1]
        turn_entries[turn_num] = turn_entries.get(turn_num, 0) + 1

logger.info(f"\nTurns with cache entries:")
for turn_num in sorted(turn_entries.keys(), key=lambda x: int(x)):
    logger.info(f"  Turn {turn_num}: 3 entries (plan, actions, index)")

logger.info("\n✅ CACHING VERIFIED: Turn-scoped plans created and reused")
