#!/usr/bin/env python3
"""
Detailed diagnostic test examining strategy outputs and deck ordering.
Shows probabilities/values each strategy assigns to moves.
"""

import sys
from pathlib import Path
import json

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import numpy as np
import torch
from tools.compare_vanilla_strategies import VanillaComparison, ComparisonConfig

# Import required modules
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
    time_per_move=1.0,  # Increased for better search depth
    num_games=1,
    seed_base=10000,
    verbosity=False,
)

comp = VanillaComparison(config)

# Use consistent deck across all strategy comparisons
fixed_deck = comp.decks[0]
print(f"Using fixed deck: {fixed_deck['name']} (from {fixed_deck.get('source', 'unknown')})")
print(f"Initial deck size: {len(fixed_deck['initial_deck'])}")
print(f"Energy list size: {len(fixed_deck['energy'])}")
print(f"Members: {len(fixed_deck['members'])}, Lives: {len(fixed_deck['lives'])}")
print("=" * 80)

# Create a diagnostic game and examine strategy outputs
game = comp._new_game(10000)
print(f"\nInitial game state:")
print(f"  Phase: {int(game.phase)}")
print(f"  Turn: {int(game.turn)}")
print(f"  Terminal: {game.is_terminal()}")

# Simulate a few moves and examine what each strategy outputs
move_count = 0
max_moves = 50
strategies_to_test = [("neural", comp._choose_neural_action), 
                       ("turnseq", comp._choose_turnseq_action),
                       ("mcts", comp._choose_mcts_action)]

print(f"\n{'=' * 80}")
print("STRATEGY OUTPUT ANALYSIS")
print('=' * 80)

while not game.is_terminal() and move_count < max_moves:
    phase = int(game.phase)
    turn = int(game.turn)
    cp = game.current_player
    legal_ids = [int(x) for x in game.get_legal_action_ids()]
    
    if not legal_ids:
        game.auto_step(comp.rust_db)
        move_count += 1
        continue
    
    print(f"\n--- Move #{move_count + 1} ---")
    print(f"Phase: {phase}, Turn: {turn}, CurrentPlayer: {cp}")
    print(f"Legal actions: {legal_ids}")
    
    # Test Neural strategy
    print(f"\n{' NEURAL OUTPUT ':^60}")
    try:
        legal_mask, legal_policy_ids, mapping = build_legal_policy_context(
            legal_ids, fixed_deck["initial_deck"], phase
        )
        print(f"  Policy action IDs (from deck): {legal_policy_ids}")
        print(f"  Mapping to game IDs: {mapping}")
        
        if len(legal_policy_ids) > 0:
            obs = build_state_observation(game, config.observation_mode)
            with torch.no_grad():
                obs_tensor = torch.from_numpy(obs[np.newaxis, :]).to(comp.device)
                probs, value = comp.model(obs_tensor)
                probs = probs.cpu().numpy()[0]
                value = value.cpu().item() if value is not None else "N/A"
            
            # Show top probabilities for legal moves
            print(f"  Value estimate: {value}")
            print(f"  Top 5 policy probabilities (all actions):")
            top_indices = np.argsort(probs)[-5:][::-1]
            for idx in top_indices:
                prob = probs[idx]
                in_legal = "✓" if idx in legal_policy_ids else "✗"
                print(f"    Action {idx}: {prob:.6f} {in_legal}")
            
            # Show selected action
            choice = int(legal_policy_ids[np.argmax(probs[legal_policy_ids])])
            selected_action = int(mapping.get(choice, legal_ids[0]))
            print(f"  Selected by neural: {selected_action}")
        else:
            print(f"  No legal policy actions! Falling back to random legal action")
    
    except Exception as e:
        print(f"  Error: {type(e).__name__}: {e}")
    
    # Test TurnSeq strategy
    print(f"\n{' TURNSEQ OUTPUT ':^60}")
    try:
        # Clone state to test without affecting actual game
        print(f"  Calling plan_full_turn_with_stats()...")
        result = game.plan_full_turn_with_stats(comp.rust_db)
        if result:
            _, action_seq, heuristic_score, diagnostics, extra = result
            print(f"  Heuristic score: {float(heuristic_score)}")
            print(f"  Action sequence length: {len(action_seq) if action_seq else 0}")
            print(f"  Extra info: {extra}")
            
            if action_seq and len(action_seq) > 0:
                print(f"  First 5 actions: {[int(a) for a in action_seq[:5]]}")
                first_action = int(action_seq[0])
                print(f"  First action {first_action} in legal_ids {legal_ids}? {first_action in legal_ids}")
                print(f"  Selected by turnseq: {first_action}")
            else:
                print(f"  ⚠️  WARNING: Action sequence is empty! This is why turnseq fails!")
                print(f"  Diagnostics data: {diagnostics}")
        else:
            print(f"  plan_full_turn_with_stats returned None")
    except KeyboardInterrupt:
        print(f"  INTERRUPTED (KeyboardInterrupt)")
        raise
    except Exception as e:
        print(f"  Error: {type(e).__name__}: {e}")
    
    # Test MCTS strategy
    print(f"\n{' MCTS OUTPUT ':^60}")
    try:
        print(f"  Calling search_mcts with time_limit={config.time_per_move}s...")
        suggestions = game.search_mcts(0, config.time_per_move, "greedy", "turn", "blind")
        if suggestions:
            print(f"  Top 5 suggestions (action, value):")
            for i, (action, value) in enumerate(suggestions[:5]):
                in_legal = "✓" if action in legal_ids else "✗"
                print(f"    {i+1}. Action {int(action)}: value={float(value):.4f} {in_legal}")
            print(f"  Selected by mcts: {int(suggestions[0][0])}")
        else:
            print(f"  No suggestions returned")
    except Exception as e:
        print(f"  Error: {type(e).__name__}: {e}")
    
    # Execute the neural action to advance
    try:
        neural_action = comp._choose_neural_action(game, legal_ids, fixed_deck["initial_deck"])
        print(f"\n→ Executing neural action: {neural_action}")
        game.step(int(neural_action))
        move_count += 1
    except Exception as e:
        print(f"Error executing move: {e}")
        break
    
    # Stop after a few moves for inspection
    if move_count >= 5:
        print(f"\n{'=' * 80}")
        print("Stopping after 5 moves for inspection")
        break

print(f"\n{'=' * 80}")
print(f"Total moves executed: {move_count}")
print(f"Final phase: {int(game.phase)}, turn: {int(game.turn)}, terminal: {game.is_terminal()}")
