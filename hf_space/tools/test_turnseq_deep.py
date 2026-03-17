#!/usr/bin/env python3
"""
Deep diagnostic for TurnSeq planning.
Examines:
1. Why plan_full_turn_with_stats returns empty sequences
2. Time allocation for the time budget
3. What planning methods are available
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
    time_per_move=2.0,  # Higher budget to see if it helps
    num_games=1,
    seed_base=12000,
    verbosity=False,
)

comp = VanillaComparison(config)
fixed_deck = comp.decks[0]

print("=" * 80)
print("TURNSEQ PLANNING DIAGNOSTIC")
print("=" * 80)

game = comp._new_game(12000)

# Advance through setup to main phase
print(f"\n[ADVANCING TO MAIN PHASE]")
for i in range(50):
    if game.is_terminal():
        break
    
    phase = int(game.phase)
    legal_ids = [int(x) for x in game.get_legal_action_ids()]
    
    # Skip past setup phases to find main gameplay
    if phase not in (-3, -2, -1, 0, 2, 4, 5, 8):  # Skip auto phases
        print(f"Move {i}: Phase {phase} (main phase!)")
        break
    
    if not legal_ids:
        game.auto_step(comp.rust_db)
        continue
    else:
        # Just take first legal action to advance
        game.step(int(legal_ids[0]))

print(f"\nCurrent game state:")
print(f"  Phase: {int(game.phase)}")
print(f"  Turn: {int(game.turn)}")
print(f"  Current Player: {game.current_player}")
print(f"  Terminal: {game.is_terminal()}")

# Now test TurnSeq planning at various phases
print(f"\n{'=' * 80}")
print("TURNSEQ PLANNING ANALYSIS")
print(f"{'=' * 80}")

for test_num in range(5):
    phase = int(game.phase)
    legal_ids = [int(x) for x in game.get_legal_action_ids()]
    
    if not legal_ids:
        game.auto_step(comp.rust_db)
        continue
    
    print(f"\n[TEST #{test_num + 1}]")
    print(f"Phase: {phase}, Turn: {int(game.turn)}, Legal actions: {len(legal_ids)}")
    print(f"Legal IDs: {legal_ids[:5]}{'...' if len(legal_ids) > 5 else ''}")
    
    # ===== Test 1: plan_full_turn_with_stats =====
    print(f"\n  A) plan_full_turn_with_stats()")
    try:
        start = time.time()
        result = game.plan_full_turn_with_stats(comp.rust_db)
        elapsed = time.time() - start
        
        if result:
            _, action_seq, heuristic_score, diagnostics, extra = result
            print(f"     Time: {elapsed:.4f}s")
            print(f"     Heuristic: {float(heuristic_score)}")
            print(f"     Action seq length: {len(action_seq) if action_seq else 0}")
            print(f"     Diagnostics: {diagnostics}")
            print(f"     Extra: {extra}")
            
            if action_seq and len(action_seq) > 0:
                print(f"     ✓ SUCCESS: Got {len(action_seq)} actions")
                print(f"       First 5: {[int(a) for a in action_seq[:5]]}")
            else:
                print(f"     ✗ EMPTY: No actions returned")
        else:
            print(f"     Result is None")
    except Exception as e:
        print(f"     ERROR: {type(e).__name__}: {e}")
    
    # ===== Test 2: Check if there's a different planning method =====
    print(f"\n  B) Available planning methods:")
    planning_methods = [attr for attr in dir(game) if 'plan' in attr.lower()]
    for method in planning_methods:
        print(f"     - {method}")
    
    # ===== Test 3: Check game state properties =====
    print(f"\n  C) Game state properties:")
    try:
        print(f"     is_terminal: {game.is_terminal()}")
        print(f"     turn: {int(game.turn)}")
        print(f"     phase: {int(game.phase)}")
        print(f"     current_player: {game.current_player}")
        print(f"     legal_actions: {len(legal_ids)}")
    except Exception as e:
        print(f"     ERROR reading properties: {e}")
    
    # ===== Test 4: Try with forced time/computation =====
    print(f"\n  D) Testing with explicit time allocation:")
    try:
        # Clear any cached state
        start_total = time.time()
        
        # Call planning multiple times to see if caching is issue
        results = []
        for call_num in range(1):
            call_start = time.time()
            result = game.plan_full_turn_with_stats(comp.rust_db)
            call_elapsed = time.time() - call_start
            results.append((call_num, call_elapsed, result))
            print(f"     Call {call_num + 1}: {call_elapsed:.4f}s")
            
            if result:
                _, action_seq, _, _, _ = result
                if action_seq and len(action_seq) > 0:
                    print(f"       → Got {len(action_seq)} actions ✓")
                else:
                    print(f"       → Empty sequence ✗")
        
        total_elapsed = time.time() - start_total
        print(f"     Total time: {total_elapsed:.4f}s")
        
    except Exception as e:
        print(f"     ERROR: {e}")
    
    # Execute best available action and continue
    try:
        action = comp._choose_neural_action(game, legal_ids, fixed_deck["initial_deck"])
        game.step(int(action))
    except Exception as e:
        print(f"\n  ERROR executing action: {e}")
        break
    
    if test_num >= 2:  # Stop after a few tests
        break

print(f"\n{'=' * 80}")
print("PHASE TIMELINE")
print(f"{'=' * 80}")

# Create a fresh game and track phases
game2 = comp._new_game(12001)
phases_seen = []
for i in range(100):
    if game2.is_terminal():
        break
    
    phase = int(game2.phase)
    if phase not in [-p for p in range(3)] and phase not in range(-1, 10):
        print(f"\nUNKNOWN PHASE: {phase}")
        break
    
    legal_ids = [int(x) for x in game2.get_legal_action_ids()]
    
    if not legal_ids:
        game2.auto_step(comp.rust_db)
    else:
        game2.step(int(legal_ids[0]))
    
    if i < 50:
        phases_seen.append(phase)

print(f"Phase sequence (first 50 steps): {phases_seen}")

# Identify action phases where planning should work
auto_phases = {-1, 0, 2, 4, 5, 8}
action_phases = [p for p in phases_seen if p not in auto_phases and p >= 0]
print(f"Action phases in sequence: {set(action_phases)}")

print(f"\n{'=' * 80}")
print("SUMMARY")
print(f"{'=' * 80}")
print("""
If plan_full_turn_with_stats() returns empty sequences:

Possible causes:
1. Phase mismatch: Method expects specific phases
2. State issue: Game state not in right condition
3. API limitation: Method doesn't support current setup
4. Timing: Method runs but returns empty before computation done
5. Design: Method only works in specific turn phases (not setup)

Check:
- What phases return non-empty sequences?
- What phases return empty sequences?
- Is there a phase requirement for planning?
""")
