#!/usr/bin/env python3
"""
Debug search_mcts API to see if it's working correctly.
"""

import sys
from pathlib import Path
import time

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from engine_rust import SearchHorizon, EvalMode
from tools.compare_vanilla_strategies import VanillaComparison, ComparisonConfig

config = ComparisonConfig(
    db_path='data/cards_vanilla.json',
    checkpoint_path='checkpoints/vanilla_overnight/best.pt',
    deck_source='ai/decks/muse_cup.txt',
    time_per_move=0.5,
    num_games=1,
    seed_base=14000,
    verbosity=False,
)

comp = VanillaComparison(config)
game = comp._new_game(14000)

# Skip to a decision point
step_count = 0
for _ in range(100):
    if game.is_terminal():
        print(f"Game terminal at step {step_count}")
        break
    
    phase = int(game.phase)
    step_count += 1
    
    legal_ids = [int(x) for x in game.get_legal_action_ids()]
    if not legal_ids:
        game.auto_step(comp.rust_db)
        continue
    
    print(f"Step {step_count}: Phase {phase}, Legal actions: {len(legal_ids)}")
    
    if phase == 4 and len(legal_ids) > 1:
        print(f"\n{'='*60}")
        print(f"Found Phase 4 decision point at step {step_count}")
        print(f"Phase: {phase}")
        print(f"Legal actions: {legal_ids[:10]}... ({len(legal_ids)} total)")
        print(f"{'='*60}\n")
        
        # Test search_mcts with time budget and correct enums
        print(f"Testing search_mcts with time_limit=0.5s")
        start = time.time()
        try:
            suggestions = game.search_mcts(
                0,                          # num_sims = 0 (use time only)
                0.5,                        # timeout_sec = 0.5s
                "greedy",                   # heuristic
                SearchHorizon.TurnEnd(),    # horizon (enum)
                EvalMode.Blind              # eval (enum)
            )
            elapsed = time.time() - start
            print(f"✓ search_mcts succeeded!")
            print(f"  Time taken: {elapsed:.4f}s")
            print(f"  Suggestions count: {len(suggestions) if suggestions else 0}")
            print(f"  Top 3 suggestions: {suggestions[:3] if suggestions else 'None'}")
        except Exception as e:
            elapsed = time.time() - start
            print(f"✗ search_mcts FAILED after {elapsed:.4f}s")
            print(f"  Error: {type(e).__name__}: {e}")
        
        break
    
    # Make a move
    action = legal_ids[0]
    game.step(action)

print(f"\nCompleted {step_count} steps")


