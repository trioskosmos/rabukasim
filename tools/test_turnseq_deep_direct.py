#!/usr/bin/env python3
"""
Deep diagnostic for TurnSeq timing on Phase 4.
"""

import sys
from pathlib import Path
import time

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tools.compare_vanilla_strategies import VanillaComparison, ComparisonConfig

config = ComparisonConfig(
    db_path='data/cards_vanilla.json',
    checkpoint_path='checkpoints/vanilla_overnight/best.pt',
    deck_source='ai/decks/muse_cup.txt',
    time_per_move=1.0,
    num_games=1,
    seed_base=14000,
    verbosity=False,
)

comp = VanillaComparison(config)
game = comp._new_game(14000)

print("=" * 80)
print("TURNSEQ PHASE 4 DEEP DIAGNOSTIC")
print("=" * 80)

# Find Phase 4
found_phase4 = False
for _ in range(100):
    if game.is_terminal():
        break
    
    phase = int(game.phase)
    legal_ids = [int(x) for x in game.get_legal_action_ids()]
    
    if not legal_ids:
        game.auto_step(comp.rust_db)
        continue
    
    if phase == 4 and len(legal_ids) > 1 and not found_phase4:
        found_phase4 = True
        print(f"\nFound Phase 4! {len(legal_ids)} legal actions")
        print(f"Testing plan_full_turn_with_stats directly:")
        print()
        
        # Test multiple calls
        for attempt in range(3):
            start = time.time()
            try:
                result = game.plan_full_turn_with_stats(comp.rust_db)
                elapsed = time.time() - start
                
                if result and len(result) >= 2:
                    action_scores, action_seq = result[0], result[1]
                    heuristic_score = result[3] if len(result) > 3 else None
                    print(f"Attempt {attempt+1}:")
                    print(f"  Time: {elapsed:.4f}s")
                    print(f"  Sequence length: {len(action_seq) if action_seq else 0}")
                    print(f"  Heuristic score: {heuristic_score}")
                    print(f"  First 3 actions in seq: {action_seq[:3] if action_seq and len(action_seq) >= 3 else action_seq}")
                else:
                    print(f"Attempt {attempt+1}:")
                    print(f"  Time: {elapsed:.4f}s")
                    print(f"  Result: {result}")
            except Exception as e:
                elapsed = time.time() - start
                print(f"Attempt {attempt+1}: ERROR after {elapsed:.4f}s")
                print(f"  {type(e).__name__}: {e}")
            print()
        
        break
    
    # Make a move
    action = legal_ids[0]
    game.step(action)

if not found_phase4:
    print("Never found Phase 4 with multiple legal actions")

print("=" * 80)
