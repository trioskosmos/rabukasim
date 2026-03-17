"""
Deep Performance Investigation - Phase 2
Investigates WHICH game states cause slowdowns
"""

import time
import sys
from pathlib import Path
from collections import defaultdict
import numpy as np

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from engine_rust.engine_rust import PyCardDatabase, PyGameState
from alphazero.training.overnight_vanilla import load_vanilla_database_json, load_tournament_decks
import random

def analyze_operation_variance():
    """Profile operations and track which game states cause slowdowns"""
    print("\n" + "="*80)
    print("DEEP PROFILE V2 - OPERATION VARIANCE ANALYSIS")
    print("="*80 + "\n")
    
    # Initialize - load database
    ROOT_DIR = Path(__file__).resolve().parent.parent
    db_path = str(ROOT_DIR / "data/cards_compiled.json")
    full_db, db_json = load_vanilla_database_json(db_path)
    db = PyCardDatabase(db_json)
    db.is_vanilla = False
    
    # Load decks  
    decks = load_tournament_decks(full_db, str(ROOT_DIR / 'ai/decks/muse_cup.txt'))
    deck = decks[0]
    
    print("[PHASE 1] SAMPLING OPERATION COSTS BY GAME PHASE")
    print("-" * 80)
    
    # Track operations by phase
    phase_stats = defaultdict(lambda: {"times": [], "count": 0})
    operation_counts = defaultdict(int)
    
    # Run multiple games, tracking every operation
    num_games = 50
    total_moves = 0
    
    for game_idx in range(num_games):
        game = PyGameState(db)
        game.initialize_game_with_seed(
            deck['initial_deck'], 
            deck['initial_deck'], 
            deck['energy'], 
            deck['energy'], 
            [], [], 42 + game_idx
        )
        moves = 0
        
        while not game.is_terminal() and moves < 1000:
            # Track which move we're on (early, mid, late game)
            if moves < 10:
                phase = "early_game"
            elif moves < 50:
                phase = "mid_game"
            else:
                phase = "late_game"
            
            # Profile get_legal_action_ids
            t0 = time.perf_counter_ns()
            legal_ids = game.get_legal_action_ids()
            t1 = time.perf_counter_ns()
            get_ids_us = (t1 - t0) / 1000
            
            # Profile step (with chosen action)
            action = random.choice(legal_ids)
            t2 = time.perf_counter_ns()
            game.step(action)
            t3 = time.perf_counter_ns()
            step_us = (t3 - t2) / 1000
            
            # Track stats
            phase_stats[phase]["times"].append({
                "get_ids": get_ids_us,
                "step": step_us,
                "total": get_ids_us + step_us,
                "legal_count": len(legal_ids)
            })
            phase_stats[phase]["count"] += 1
            operation_counts["get_ids_expensive" if get_ids_us > 50 else "get_ids_normal"] += 1
            operation_counts["step_expensive" if step_us > 100 else "step_normal"] += 1
            
            moves += 1
            total_moves += 1
    
    # Analyze results
    print(f"\nAnalyzed {num_games} games, {total_moves} moves\n")
    
    print("Operation classification:")
    for op, count in sorted(operation_counts.items()):
        pct = 100 * count / total_moves
        print(f"  {op:30s}: {count:6d} ({pct:5.1f}%)")
    
    # Find worst phases
    print("\n[PHASE 2] EXPENSIVE PHASE IDENTIFICATION")
    print("-" * 80)
    
    phase_summary = []
    for phase, stats in phase_stats.items():
        times = stats["times"]
        if not times:
            continue
        
        get_ids = [t["get_ids"] for t in times]
        step_times = [t["step"] for t in times]
        
        avg_get = np.mean(get_ids)
        max_get = np.max(get_ids)
        avg_step = np.mean(step_times)
        max_step = np.max(step_times)
        
        phase_summary.append({
            "phase": phase,
            "count": len(times),
            "avg_get": avg_get,
            "max_get": max_get,
            "avg_step": avg_step,
            "max_step": max_step,
        })
    
    # Sort by average cost and show
    phase_summary.sort(key=lambda x: x["avg_step"] + x["avg_get"], reverse=True)
    
    print("\nTop 10 most expensive phases:")
    print(f"{'Phase':<15} {'Count':>6} {'Avg Get':>10} {'Max Get':>10} {'Avg Step':>10} {'Max Step':>10}")
    print("-" * 70)
    for p in phase_summary[:10]:
        print(f"{p['phase']:<15} {p['count']:>6} {p['avg_get']:>9.1f}µs {p['max_get']:>9.1f}µs {p['avg_step']:>9.1f}µs {p['max_step']:>9.1f}µs")
    
    # Analyze expensive ops
    print("\n[PHASE 3] ANALYZING EXPENSIVE OPERATIONS")
    print("-" * 80)
    
    expensive_get = []
    expensive_step = []
    
    for phase, stats in phase_stats.items():
        for timing in stats["times"]:
            if timing["get_ids"] > 50:
                expensive_get.append({"phase": phase, **timing})
            if timing["step"] > 100:
                expensive_step.append({"phase": phase, **timing})
    
    print(f"\nOperations > 50µs:")
    print(f"  get_legal_action_ids: {len(expensive_get)} occurrences (avg {np.mean([e['get_ids'] for e in expensive_get]):.1f}µs if any)")
    print(f"  game.step():          {len(expensive_step)} occurrences (avg {np.mean([e['step'] for e in expensive_step]):.1f}µs if any)")
    
    if expensive_get:
        print("\n  Expensive get_legal_action_ids - mostly in phases:")
        exp_phases = defaultdict(int)
        for e in expensive_get:
            exp_phases[e["phase"]] += 1
        for phase, count in sorted(exp_phases.items(), key=lambda x: -x[1])[:5]:
            print(f"    {phase}: {count} times")
    
    if expensive_step:
        print("\n  Expensive step() - mostly in phases:")
        exp_phases = defaultdict(int)
        for e in expensive_step:
            exp_phases[e["phase"]] += 1
        for phase, count in sorted(exp_phases.items(), key=lambda x: -x[1])[:5]:
            print(f"    {phase}: {count} times")
    
    # Profile pure Rust in detail
    print("\n[PHASE 4] RUST vs PYTHON COMPARISON")
    print("-" * 80)
    
    print("\nPython loop simulation (10 games):")
    t0 = time.perf_counter()
    python_moves = 0
    for _ in range(10):
        game = PyGameState(db)
        game.initialize_game_with_seed(
            deck['initial_deck'], 
            deck['initial_deck'], 
            deck['energy'], 
            deck['energy'], 
            [], [], 42 + python_moves
        )
        while not game.is_terminal():
            legal = game.get_legal_action_ids()
            game.step(random.choice(legal))
            python_moves += 1
    t1 = time.perf_counter()
    python_time = t1 - t0
    python_mps = python_moves / python_time
    print(f"  {python_moves} moves in {python_time:.3f}s = {python_mps:,.0f} MPS")
    
    print("\nRust batch simulation (10 games):")
    t0 = time.perf_counter()
    db.sim_random_games(10)
    t1 = time.perf_counter()
    rust_time = t1 - t0
    rust_mps = (10 * 173) / rust_time  # Rough ~173 avg moves per game
    print(f"  ~1730 moves in {rust_time:.3f}s = {rust_mps:,.0f} MPS (estimated)")
    
    speedup = rust_mps / python_mps if python_mps > 0 else 0
    print(f"\n  Rust is {speedup:.1f}x faster than Python loop")
    
    # Recommendations
    print("\n" + "="*80)
    print("OPTIMIZATION RECOMMENDATIONS")
    print("="*80)
    print("""
1. PROFILING INSIGHTS:
   - get_legal_action_ids variance suggests complex phase transitions
   - step() variance indicates expensive ability/effect computations
   - Early turns (turn_1, turn_2) likely more expensive than late turns
   
2. IMMEDIATE OPTIMIZATIONS:
   - Cache legal_ids types (list vs numpy detection)
   - Profile which turns are slow
   - Stream operation micro-timing to identify patterns
   
3. LONG-TERM:
   - Consider C++ wrapper for hot loop
   - Batch operations to reduce PyO3 crossings
   - Profile Rust side for memory allocation patterns
   
4. VERIFICATION NEEDED:
   - Why is get_legal_action_ids varying so much?
   - Is it phase-dependent (early vs late game)?
   - Are certain card effects causing slowdown?
""")

if __name__ == "__main__":
    analyze_operation_variance()
