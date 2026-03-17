#!/usr/bin/env python3
"""
Trace through complete game to find:
1. When does plan_full_turn_with_stats() return non-empty sequences?
2. What phases allow actual planning?
3. Time allocation during moves
"""

import sys
from pathlib import Path
import time

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import numpy as np
from tools.compare_vanilla_strategies import VanillaComparison, ComparisonConfig

try:
    import engine_rust
except ImportError:
    print("ERROR: engine_rust not available")
    sys.exit(1)

config = ComparisonConfig(
    db_path='data/cards_vanilla.json',
    checkpoint_path='checkpoints/vanilla_overnight/best.pt',
    deck_source='ai/decks/muse_cup.txt',
    time_per_move=2.0,
    num_games=1,
    seed_base=13000,
    verbosity=False,
)

comp = VanillaComparison(config)
fixed_deck = comp.decks[0]

print("=" * 80)
print("FULL GAME TRACE: FINDING WHEN TURNSEQ WORKS")
print("=" * 80)

game = comp._new_game(13000)

planning_results = []
step_count = 0

while not game.is_terminal() and step_count < 200:
    phase = int(game.phase)
    turn = int(game.turn)
    cp = game.current_player
    legal_ids = [int(x) for x in game.get_legal_action_ids()]
    
    if not legal_ids:
        game.auto_step(comp.rust_db)
        step_count += 1
        continue
    
    # Try planning at this phase
    try:
        start = time.time()
        result = game.plan_full_turn_with_stats(comp.rust_db)
        elapsed = time.time() - start
        
        if result:
            _, action_seq, heuristic_score, diagnostics, extra = result
            seq_len = len(action_seq) if action_seq else 0
            planning_results.append({
                'step': step_count,
                'phase': phase,
                'turn': turn,
                'cp': cp,
                'seq_len': seq_len,
                'time': elapsed,
                'score': float(heuristic_score),
                'success': seq_len > 0,
            })
            
            if seq_len == 0 and step_count < 100:
                print(f"Step {step_count:3d}: Phase {phase:2d}, Turn {turn:2d}, P{cp} → [EMPTY] ({elapsed:.4f}s)")
        else:
            planning_results.append({
                'step': step_count,
                'phase': phase,
                'turn': turn,
                'cp': cp,
                'seq_len': 0,
                'time': 0,
                'score': 0,
                'success': False,
            })
            if step_count < 100:
                print(f"Step {step_count:3d}: Phase {phase:2d}, Turn {turn:2d}, P{cp} → [None]")
    
    except Exception as e:
        if step_count < 100:
            print(f"Step {step_count:3d}: Phase {phase:2d}, Turn {turn:2d}, P{cp} → [ERROR: {type(e).__name__}]")
    
    # Always take first legal action to advance
    try:
        game.step(int(legal_ids[0]))
    except Exception as e:
        print(f"Step error: {e}")
        break
    
    step_count += 1

print(f"\n{'=' * 80}")
print("ANALYSIS: WHEN DID PLANNING RETURN SUCCESS?")
print(f"{'=' * 80}")

successes = [r for r in planning_results if r['success']]
print(f"\nTotal planning attempts: {len(planning_results)}")
print(f"Successful (non-empty): {len(successes)}")

if successes:
    print(f"\nSuccessful planning calls:")
    for r in successes[:10]:
        print(f"  Step {r['step']:3d}: Phase {r['phase']:2d}, Turn {r['turn']:2d}, "
              f"Seq len: {r['seq_len']}, Time: {r['time']:.4f}s")
else:
    print(f"\n⚠️  NO SUCCESSFUL PLANNING CALLS!")
    print(f"All {len(planning_results)} attempts returned empty sequences")

# Group by phase
print(f"\n{'=' * 80}")
print("RESULTS BY PHASE")
print(f"{'=' * 80}")

phases_stats = {}
for r in planning_results:
    phase = r['phase']
    if phase not in phases_stats:
        phases_stats[phase] = {'total': 0, 'success': 0, 'times': []}
    phases_stats[phase]['total'] += 1
    phases_stats[phase]['success'] += 1 if r['success'] else 0
    phases_stats[phase]['times'].append(r['time'])

for phase in sorted(phases_stats.keys()):
    stats = phases_stats[phase]
    avg_time = np.mean(stats['times']) if stats['times'] else 0
    print(f"Phase {phase:3d}: {stats['total']:3d} attempts, "
          f"{stats['success']:3d} success, "
          f"avg time: {avg_time:.4f}s")

print(f"\n{'=' * 80}")
print("CONCLUSION")
print(f"{'=' * 80}")

if not successes:
    print("""
plan_full_turn_with_stats() appears to NEVER return action sequences,
even after many attempts across different phases.

This suggests:
1. The method might have a different API contract than expected
2. It might require specific preconditions (e.g., full turn context)
3. It might be deprecated/broken
4. The action sequence might always be empty for Turn-based planning

RECOMMENDATION: Try plan_full_turn() without stats instead,
or use different planning method.
""")
else:
    print(f"""
plan_full_turn_with_stats() SUCCESS FOUND!
- Phases that work: {sorted([r['phase'] for r in successes if r['phase']])}
- Most common: Phase {max(set([r['phase'] for r in successes]), key=[r['phase'] for r in successes].count)}
- Average time: {np.mean([r['time'] for r in successes]):.4f}s
""")
