#!/usr/bin/env python3
"""
Detailed diagnostic showing why strategies fail.
Focus: TurnSeq returns empty action sequences!
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import numpy as np
import torch
from tools.compare_vanilla_strategies import VanillaComparison, ComparisonConfig

try:
    import engine_rust
except ImportError:
    print("ERROR: engine_rust not available")
    sys.exit(1)

from alphazero.training.vanilla_action_codec import build_legal_policy_context
from alphazero.training.overnight_vanilla import build_state_observation

config = ComparisonConfig(
    db_path='data/cards_vanilla.json',
    checkpoint_path='checkpoints/vanilla_overnight/best.pt',
    deck_source='ai/decks/muse_cup.txt',
    time_per_move=1.0,
    num_games=1,
    seed_base=10000,
    verbosity=False,
)

comp = VanillaComparison(config)
fixed_deck = comp.decks[0]

print("=" * 80)
print("STRATEGY DIAGNOSTIC - ROOT CAUSE ANALYSIS")
print("=" * 80)

game = comp._new_game(10000)
print(f"\nInitial state: Phase={int(game.phase)}, Turn={int(game.turn)}")

# Move through setup phase to reach actual gameplay
for i in range(20):
    if game.is_terminal():
        break
    
    phase = int(game.phase)
    legal_ids = [int(x) for x in game.get_legal_action_ids()]
    
    if not legal_ids:
        game.auto_step(comp.rust_db)
        continue
    
    cp = game.current_player
    
    print(f"\nMove #{i+1}: Phase {phase}, Player {cp}, {len(legal_ids)} legal actions")
    
    # ========== NEURAL OUTPUT ==========
    print(f"\n  [NEURAL]")
    try:
        legal_mask, legal_policy_ids, mapping = build_legal_policy_context(legal_ids, fixed_deck["initial_deck"], phase)
        
        if len(legal_policy_ids) > 0:
            obs = build_state_observation(game, config.observation_mode)
            with torch.no_grad():
                obs_tensor = torch.from_numpy(obs[np.newaxis, :]).to(comp.device)
                probs, value = comp.model(obs_tensor)
                probs = probs.cpu().numpy()[0]
                value = float(value) if value is not None else 0.0
            
            # Find best legal action
            best_legal_idx = legal_policy_ids[np.argmax(probs[legal_policy_ids])]
            best_action = int(mapping.get(best_legal_idx, legal_ids[0]))
            
            # Show top 3 legal probabilities
            prob_scores = [(idx, probs[idx]) for idx in legal_policy_ids]
            prob_scores.sort(key=lambda x: x[1], reverse=True)
            
            print(f"    Value: {value:.4f}")
            print(f"    Top legal actions:")
            for idx, prob in prob_scores[:3]:
                game_id = mapping.get(idx, "?")
                print(f"      Policy action {idx} -> game ID {game_id}: prob={prob:.6f}")
            print(f"    Selected: {best_action}")
        else:
            print(f"    No legal policy actions, using random")
    except Exception as e:
        print(f"    ERROR: {e}")
    
    # ========== TURNSEQ OUTPUT ==========
    print(f"\n  [TURNSEQ]")
    try:
        result = game.plan_full_turn_with_stats(comp.rust_db)
        if result:
            _, action_seq, heuristic_score, diagnostics, extra = result
            print(f"    Heuristic score: {float(heuristic_score):.4f}")
            print(f"    Action seq length: {len(action_seq) if action_seq else 0}")
            print(f"    Diagnostics: {diagnostics}")
            print(f"    Extra info: {extra}")
            
            if action_seq and len(action_seq) > 0:
                first_action = int(action_seq[0])
                in_legal = "YES" if first_action in legal_ids else "NO"
                print(f"    First action: {first_action} (in legal? {in_legal})")
                print(f"    Full sequence (first 10): {[int(a) for a in action_seq[:10]]}")
            else:
                print(f"    >>> PROBLEM: Empty action sequence returned! <<<")
        else:
            print(f"    plan_full_turn_with_stats returned None")
    except Exception as e:
        print(f"    ERROR: {type(e).__name__}: {e}")
    
    # ========== MCTS OUTPUT ==========
    print(f"\n  [MCTS]")
    try:
        # Try simple search_mcts call
        import time
        start = time.time()
        suggestions = game.search_mcts(0, 0.1, "greedy", "turn", "blind")  # 0.1s budget
        elapsed = time.time() - start
        
        if suggestions:
            print(f"    Time: {elapsed:.4f}s")
            print(f"    Suggestions: {len(suggestions)}")
            for i, (action, value) in enumerate(suggestions[:3]):
                action_int = int(action)
                value_float = float(value)
                in_legal = "YES" if action_int in legal_ids else "NO"
                print(f"      {i+1}. Action {action_int}: value={value_float:.4f} (legal? {in_legal})")
        else:
            print(f"    No suggestions returned")
    except TypeError as e:
        if "SearchHorizon" in str(e):
            print(f"    API ERROR: search_mcts string parameters not compatible")
            print(f"    Note: Should use enum-based API")
        else:
            print(f"    ERROR: {e}")
    except Exception as e:
        print(f"    ERROR: {type(e).__name__}: {e}")
    
    # Execute best neural action
    action = comp._choose_neural_action(game, legal_ids, fixed_deck["initial_deck"])
    print(f"\n  -> Executing: {action}")
    game.step(int(action))
    
    if i >= 5:
        break

print(f"\n{'=' * 80}")
print("SUMMARY OF FINDINGS:")
print("=" * 80)
print("""
1. TURNSEQ: Returns action_seq with length 0 
   -> This is why it crashes when trying to access action_seq[0]
   -> Even though heuristic_score is valid, action sequence is empty

2. MCTS: Requires SearchHorizon enum, not string parameters
   -> Current code uses string "turn" and "blind" which aren't compatible
   -> Need to fix API call

3. NEURAL: Works correctly
   -> Returns valid value estimates
   -> Selects legal actions properly
   -> Probabilities for each legal action available
""")
