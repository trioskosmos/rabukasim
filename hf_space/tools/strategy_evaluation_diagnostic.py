#!/usr/bin/env python3
"""
Deep diagnostic of strategy evaluations and search effort.
Examine: MCTS simulations, TurnSeq sequences, Neural ensemble, fair seeding.
"""

import sys
from pathlib import Path
import time
import json

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tools.compare_vanilla_strategies import VanillaComparison, ComparisonConfig

config = ComparisonConfig(
    db_path='data/cards_vanilla.json',
    checkpoint_path='checkpoints/vanilla_overnight/best.pt',
    deck_source='ai/decks/muse_cup.txt',
    time_per_move=0.2,
    num_games=1,
    seed_base=14000,
    verbosity=False,
)

comp = VanillaComparison(config)

print("=" * 80)
print("STRATEGY EVALUATION DIAGNOSTIC")
print("=" * 80)

# Create 2 identical games to verify seeding
seed = 14000
game1 = comp._new_game(seed)
game2 = comp._new_game(seed)

print(f"\nChecking seed consistency (seed={seed}):")
print(f"  Game 1 - Phase: {game1.phase}, Turn: {game1.turn}")
print(f"  Game 2 - Phase: {game2.phase}, Turn: {game2.turn}")

# Compare initial state
legal1 = set(int(x) for x in game1.get_legal_action_ids())
legal2 = set(int(x) for x in game2.get_legal_action_ids())

if (game1.phase == game2.phase and game1.turn == game2.turn and legal1 == legal2):
    print(f"  [OK] Seeds consistent! Both have {len(legal1)} legal actions")
else:
    print(f"  [FAIL] Seeds NOT consistent - seeding issue!")

# Now trace a single game with diagnostics
print(f"\n{'=' * 80}")
print("TRACING SINGLE GAME WITH EVALUATIONS")
print(f"{'=' * 80}\n")

game = comp._new_game(seed)
selected_deck = comp.decks[0]  # Use first deck for consistency
initial_deck = selected_deck["initial_deck"]

move_count = 0
max_moves = 30

strategies = ["neural", "mcts", "turnseq", "random"]
evaluations = {s: [] for s in strategies}
search_effort = {s: [] for s in strategies}

while not game.is_terminal() and move_count < max_moves:
    phase = int(game.phase)
    turn = int(game.turn)
    legal_ids = [int(x) for x in game.get_legal_action_ids()]
    
    if not legal_ids:
        game.auto_step(comp.rust_db)
        continue
    
    if len(legal_ids) == 1:
        action = legal_ids[0]
        game.step(action)
        continue
    
    print(f"Move #{move_count + 1}: Phase {phase}, Turn {turn}, {len(legal_ids)} legal actions")
    print(f"  Legal IDs: {legal_ids[:5]}{'...' if len(legal_ids) > 5 else ''}")
    
    # Test each strategy
    for strategy in strategies:
        if strategy == "neural":
            start = time.time()
            action = comp._choose_neural_action(game, legal_ids, initial_deck, time_limit=0.2)
            elapsed = time.time() - start
            evaluations[strategy].append({"time": elapsed, "action": action})
            print(f"  [{strategy:8}] {elapsed:.4f}s → action {action}")
            
        elif strategy == "mcts":
            start = time.time()
            action = comp._choose_mcts_action(game, legal_ids, time_limit=0.2)
            elapsed = time.time() - start
            # MCTS doesn't expose simulation count, but time tells us budget usage
            evaluations[strategy].append({"time": elapsed, "action": action})
            print(f"  [{strategy:8}] {elapsed:.4f}s → action {action}")
            
        elif strategy == "turnseq":
            # Clear cache for diagnostic (multi-move caching only works in actual gameplay)
            comp.turnseq_plan_cache.clear()
            start = time.time()
            action = comp._choose_turnseq_action(game, legal_ids, time_limit=0.2)
            elapsed = time.time() - start
            evaluations[strategy].append({"time": elapsed, "action": action, "cache_size": len(comp.turnseq_plan_cache)})
            print(f"  [{strategy:8}] {elapsed:.4f}s → action {action}")
            
        elif strategy == "random":
            start = time.time()
            action = comp._choose_random_action(game, legal_ids)
            elapsed = time.time() - start
            evaluations[strategy].append({"time": elapsed, "action": action})
            print(f"  [{strategy:8}] {elapsed:.4f}s → action {action}")
    
    # Execute first strategy's action
    action = comp._choose_neural_action(game, legal_ids, initial_deck, time_limit=0.2)
    game.step(action)
    move_count += 1
    print()

print(f"\n{'=' * 80}")
print("SUMMARY STATISTICS")
print(f"{'=' * 80}\n")

import numpy as np
for strategy in strategies:
    if evaluations[strategy]:
        times = [e["time"] for e in evaluations[strategy]]
        print(f"{strategy.upper()}:")
        print(f"  Moves evaluated: {len(times)}")
        print(f"  Avg time: {np.mean(times):.4f}s")
        print(f"  Min: {np.min(times):.4f}s, Max: {np.max(times):.4f}s")
        print(f"  Total: {np.sum(times):.4f}s")
        print()

print(f"{'=' * 80}")
print("NEURAL MCTS QUESTION")
print(f"{'=' * 80}\n")

print("""
Why can't neural MCTS be time-based?

Current implementation uses: state.search_mcts_alphazero(sims, evaluator)
This API only takes simulation count, not time budget.

Available time-based APIs:
1. state.search_mcts(num_sims, timeout_sec, ...) - general MCTS [YES] Already time-based
2. state.get_mcts_suggestions(sims, timeout_sec=...) - takes timeout [YES] Already time-based
3. state.search_mcts_alphazero(sims, evaluator) - NO timeout parameter [NO]

Solutions:
A) Loop search_mcts_alphazero with time budget (call multiple times)
B) Use general search_mcts with neural heuristic evaluation
C) Use get_mcts_suggestions with timeout (already supports it)

Current MCTS uses search_mcts() → Already time-based! [YES]
Just need to verify AlphaZero variant uses same.
""")
