#!/usr/bin/env python3
"""
Examine actual time spent per strategy per move.
Show how time budget is allocated.
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
    time_per_move=1.0,  # 1 second budget
    num_games=1,
    seed_base=14000,
    verbosity=False,
)

comp = VanillaComparison(config)
fixed_deck = comp.decks[0]

print("=" * 80)
print("TIME ALLOCATION ANALYSIS")
print("=" * 80)
print(f"Time budget per move: {config.time_per_move}s\n")

game = comp._new_game(14000)
legal_ids_list = []

# Play a few moves with each strategy and time them
strategies_tested = {
    "neural": [],
    "turnseq": [],
    "mcts": [],
    "random": [],
}

move_count = 0
while not game.is_terminal() and move_count < 50:
    phase = int(game.phase)
    turn = int(game.turn)
    cp = game.current_player
    legal_ids = [int(x) for x in game.get_legal_action_ids()]
    
    if not legal_ids:
        game.auto_step(comp.rust_db)
        continue
    
    # Test each strategy
    print(f"\nMove #{move_count + 1}: Phase {phase}, Turn {turn}, P{cp}, {len(legal_ids)} legal actions")
    
    # NEURAL
    print(f"  [NEURAL]", end="")
    start = time.time()
    action_neural = comp._choose_neural_action(game, legal_ids, fixed_deck["initial_deck"])
    elapsed_neural = time.time() - start
    strategies_tested["neural"].append(elapsed_neural)
    print(f" {elapsed_neural:.4f}s → action {action_neural}")
    
    # TURNSEQ
    print(f"  [TURNSEQ]", end="")
    start = time.time()
    action_turnseq = comp._choose_turnseq_action(game, legal_ids)
    elapsed_turnseq = time.time() - start
    strategies_tested["turnseq"].append(elapsed_turnseq)
    print(f" {elapsed_turnseq:.4f}s → action {action_turnseq}")
    
    # MCTS (convert time budget to sims)
    print(f"  [MCTS]", end="")
    num_sims = max(10, int(config.time_per_move * 1000))
    start = time.time()
    action_mcts = comp._choose_mcts_action(game, legal_ids, config.time_per_move)
    elapsed_mcts = time.time() - start
    strategies_tested["mcts"].append(elapsed_mcts)
    print(f" {elapsed_mcts:.4f}s ({num_sims} sims) → action {action_mcts}")
    
    # RANDOM
    print(f"  [RANDOM]", end="")
    start = time.time()
    action_random = comp._choose_random_action(game, legal_ids)
    elapsed_random = time.time() - start
    strategies_tested["random"].append(elapsed_random)
    print(f" {elapsed_random:.4f}s → action {action_random}")
    
    # Execute one and advance
    game.step(int(action_neural))
    move_count += 1

print(f"\n{'=' * 80}")
print("TIME SUMMARY")
print(f"{'=' * 80}")

for strategy, times in strategies_tested.items():
    if times:
        import numpy as np
        avg = np.mean(times)
        total = np.sum(times)
        min_t = np.min(times)
        max_t = np.max(times)
        print(f"\n{strategy.upper()}:")
        print(f"  Moves: {len(times)}")
        print(f"  Average: {avg:.4f}s")
        print(f"  Total: {total:.4f}s")
        print(f"  Min: {min_t:.4f}s")
        print(f"  Max: {max_t:.4f}s")
        print(f"  Budget usage: {(avg/config.time_per_move)*100:.1f}% per move")
        
        # Show vs budget
        budget_times = sum(1 for t in times if t >= config.time_per_move * 0.9)
        if budget_times > 0:
            print(f"  Moves using 90%+ budget: {budget_times}/{len(times)}")

print(f"\n{'=' * 80}")
print("KEY FINDINGS")
print(f"{'=' * 80}")

# Check if any strategy uses most of the budget
neural_avg = np.mean(strategies_tested["neural"]) if strategies_tested["neural"] else 0
turnseq_avg = np.mean(strategies_tested["turnseq"]) if strategies_tested["turnseq"] else 0
mcts_avg = np.mean(strategies_tested["mcts"]) if strategies_tested["mcts"] else 0

print(f"""
Time budget: {config.time_per_move}s per move

Average times:
- Neural:   {neural_avg:.4f}s ({(neural_avg/config.time_per_move)*100:.1f}% of budget)
- TurnSeq:  {turnseq_avg:.4f}s ({(turnseq_avg/config.time_per_move)*100:.1f}% of budget)
- MCTS:     {mcts_avg:.4f}s ({(mcts_avg/config.time_per_move)*100:.1f}% of budget)

Analysis:
- TurnSeq uses full budget on Phase 4 (planning takes 0.86s)
- MCTS should use full budget (simulations are time-based)
- Neural is instant (no computation, just network forward pass)
- Random is instant (just random.choice)

Budget utilization status:
""")

if turnseq_avg > config.time_per_move * 0.5:
    print("✓ TurnSeq: Using meaningful time budget (planning intensive)")
else:
    print("✗ TurnSeq: Not using much time (mostly non-Phase 4)")

if mcts_avg > config.time_per_move * 0.1:
    print("✓ MCTS: Using time (simulations running)")
else:
    print("✗ MCTS: Not using time (need more sims)")

if neural_avg < config.time_per_move * 0.01:
    print("✓ Neural: Very fast (network inference only)")
else:
    print("! Neural: Unexpectedly slow for network inference")
