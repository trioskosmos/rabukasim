#!/usr/bin/env python3
"""
Examine what values each strategy gives to legal moves.
Trace through a single game showing move evaluation from all strategies.
"""

import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent.parent))

from pathlib import Path
import logging
import time
import torch
from tools.compare_vanilla_strategies import VanillaComparison, ComparisonConfig

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def log_memory():
    """Log current memory usage."""
    try:
        vram_used = torch.cuda.memory_allocated() / 1024 / 1024
        vram_total = torch.cuda.get_device_properties(0).total_memory / 1024 / 1024
        return f"VRAM: {vram_used:.0f}/{vram_total:.0f}MB"
    except:
        return f"VRAM: unavailable"

logger.info("=" * 100)
logger.info("STRATEGY VALUE EXAMINATION - Single Game Trace")
logger.info("=" * 100)

try:
    config = ComparisonConfig(num_games=1, time_per_move=0.3)
    comp = VanillaComparison(config)
    
    logger.info(f"Initial: {log_memory()}")
    
    game = comp._new_game(5000)
    initial_deck = comp.decks[0]
    
    move_count = 0
    phase4_moves = 0
    
    while not game.is_terminal() and move_count < 30:
        phase = int(game.phase)
        turn = int(game.turn)
        legal_ids = [int(x) for x in game.get_legal_action_ids()]
        
        if not legal_ids:
            break
        
        move_count += 1
        
        # Only trace detailed moves for Phase 4 (where planning happens)
        if phase == 4:
            phase4_moves += 1
            logger.info(f"\n--- Move #{move_count} (Phase {phase}, Turn {turn}) ---")
            logger.info(f"    Legal IDs: {legal_ids}")
            logger.info(f"    Memory: {log_memory()}")
            
            # Try neural (single pass to save memory)
            try:
                # REMOVED: torch.cuda.empty_cache() - too slow, let garbage collector handle it
                start = time.time()
                action_neural = comp._choose_neural_action(game, legal_ids, initial_deck, time_limit=0.05)
                time_neural = time.time() - start
                logger.info(f"    [neural  ] {time_neural:.4f}s → {action_neural}")
            except RuntimeError as e:
                if "out of memory" in str(e).lower() or "cuda" in str(e).lower():
                    logger.error(f"    [neural  ] ❌ CUDA/MEMORY: {str(e)[:80]}")
                else:
                    logger.error(f"    [neural  ] ERROR: {type(e).__name__}: {str(e)[:60]}")
                action_neural = legal_ids[0]
            except Exception as e:
                logger.error(f"    [neural  ] ERROR: {type(e).__name__}: {str(e)[:60]}")
                action_neural = legal_ids[0]
            
            # Try TurnSeq
            try:
                start = time.time()
                action_turnseq = comp._choose_turnseq_action(game, legal_ids, time_limit=0.1)
                time_turnseq = time.time() - start
                logger.info(f"    [turnseq ] {time_turnseq:.4f}s → {action_turnseq}")
            except Exception as e:
                logger.error(f"    [turnseq ] ERROR: {type(e).__name__}")
                action_turnseq = legal_ids[0]
            
            # Try MCTS
            try:
                start = time.time()
                action_mcts = comp._choose_mcts_action(game, legal_ids, time_limit=0.1)
                time_mcts = time.time() - start
                logger.info(f"    [mcts    ] {time_mcts:.4f}s → {action_mcts}")
            except Exception as e:
                logger.error(f"    [mcts    ] ERROR: {type(e).__name__}")
                action_mcts = legal_ids[0]
            
            # Random
            action_random = comp._choose_random_action(game, legal_ids)
            logger.info(f"    [random  ] 0.0000s → {action_random}")
            
            logger.info(f"    Cache keys: {list(comp.turnseq_plan_cache.keys())}")
            logger.info(f"    Memory after: {log_memory()}")
            
            # Use neural's choice if available, otherwise random
            action = action_neural if action_neural is not None else action_random
        else:
            # Quick action for other phases
            legal_ids_int = [int(x) for x in legal_ids]
            action = comp._choose_random_action(game, legal_ids_int)
        
        game.step(int(action))
    
    logger.info(f"\n{'=' * 100}")
    logger.info(f"Completed {move_count} moves ({phase4_moves} Phase 4)")
    logger.info(f"Final: {log_memory()}")
    logger.info(f"TurnSeq cache size: {len(comp.turnseq_plan_cache)}")
    logger.info(f"TurnSeq cache keys: {list(comp.turnseq_plan_cache.keys())}")
    
    # Show cache contents
    for key in sorted(comp.turnseq_plan_cache.keys()):
        val = comp.turnseq_plan_cache[key]
        if isinstance(val, list):
            logger.info(f"  {key}: {val}")
        else:
            logger.info(f"  {key}: {val}")
    
except Exception as e:
    logger.error(f"FATAL: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
finally:
    logger.info(f"Cleanup: {log_memory()}")
