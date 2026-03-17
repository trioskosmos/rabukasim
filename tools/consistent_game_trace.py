#!/usr/bin/env python3
"""
Run a proper game comparing two strategies consistently.
Examine phase transitions and cache behavior across Phase 4 → Phase 5.
"""

import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent.parent))

import logging
import time
import torch
from tools.compare_vanilla_strategies import VanillaComparison, ComparisonConfig

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def log_vram():
    """Log VRAM usage."""
    try:
        vram_used = torch.cuda.memory_allocated() / 1024 / 1024
        vram_total = torch.cuda.get_device_properties(0).total_memory / 1024 / 1024
        return f"{vram_used:.0f}/{vram_total:.0f}MB"
    except:
        return "N/A"

logger.info("="*100)
logger.info("SINGLE GAME: TurnSeq vs Random (proper strategy comparison)")
logger.info("="*100)

try:
    config = ComparisonConfig(num_games=1, time_per_move=0.3)
    comp = VanillaComparison(config)
    
    logger.info(f"Initial VRAM: {log_vram()}")
    
    game = comp._new_game(seed=5001)
    initial_deck = comp.decks[0]
    
    move_count = 0
    phase_transitions = []
    last_phase = -100
    
    # Alternating players: Player 0 uses TurnSeq, Player 1 uses Random
    player_strategies = {
        0: "turnseq",
        1: "random"
    }
    
    logger.info("\nGame state trace:")
    logger.info(f"{'Move':>4} {'Phase':>1} {'Turn':>3} {'Legal Count':>3} {'Strategy':>8} {'Action':>6} {'VRAM':>8}")
    logger.info("-" * 90)
    
    while not game.is_terminal() and move_count < 60:
        phase = int(game.phase)
        turn = int(game.turn)
        legal_ids = [int(x) for x in game.get_legal_action_ids()]
        
        if not legal_ids:
            break
        
        # Track phase transitions
        if phase != last_phase:
            phase_transitions.append((move_count, phase, turn))
            last_phase = phase
        
        move_count += 1
        
        # Simple strategy rotation: alternate turnseq and random
        strategy = "turnseq" if move_count % 2 == 1 else "random"
        
        if strategy == "turnseq":
            action = comp._choose_turnseq_action(game, legal_ids, time_limit=0.3)
        else:
            action = comp._choose_random_action(game, legal_ids)
        
        vram = log_vram()
        
        logger.info(f"{move_count:4} {phase:2} {turn:3} {len(legal_ids):3} {strategy:>8} {int(action):6} {vram:>8}")
        
        game.step(int(action))
    
    logger.info("-" * 90)
    logger.info(f"\nCompleted {move_count} moves")
    logger.info(f"Phase transitions: {phase_transitions}")
    logger.info(f"Final VRAM: {log_vram()}")
    logger.info(f"\nTurnSeq cache contents:")
    for key in sorted(comp.turnseq_plan_cache.keys()):
        val = comp.turnseq_plan_cache[key]
        if isinstance(val, list):
            logger.info(f"  {key}: {val}")
        else:
            logger.info(f"  {key}: {val}")
    
except Exception as e:
    logger.error(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

logger.info("\n" + "="*100)
