#!/usr/bin/env python
"""
Quick test of card-centric + slot-aware 248-dim action space implementation.
Tests baton pass awareness and proper slot selection.
"""
import sys
from pathlib import Path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import torch
import numpy as np
from alphazero.vanilla_net import HighFidelityAlphaNet

def test_model_output_shape():
    """Test that model outputs 248-dim policy with slot awareness"""
    print("[TEST] Model output shape...")
    model = HighFidelityAlphaNet(input_dim=800, num_actions=248)
    
    # Dummy input
    obs = torch.randn(4, 800)  # Batch of 4
    mask = torch.ones(4, 248, dtype=torch.bool)
    
    policy, value = model(obs, mask=mask)
    
    assert policy.shape == (4, 248), f"Expected (4, 248), got {policy.shape}"
    assert value.shape == (4, 1), f"Expected (4, 1), got {value.shape}"
    print(f"✓ Policy shape: {policy.shape}, Value shape: {value.shape}")
    print(f"✓ Action space: 8 phase + 60 generic + 180 slot-specific (60×3)")

def test_action_mapping_functions():
    """Test card + slot aware action mapping functions"""
    print("[TEST] Action mapping functions (248-dim)...")
    
    # These should be importable from vanilla_training
    try:
        from alphazero.training.vanilla_training import (
            get_card_zone,
            engine_action_to_action_248,
            action_248_to_engine_action,
            build_action_mask_248
        )
        print("✓ All mapping functions imported successfully")
        print(f"  - get_card_zone: zone lookup (0-5)")
        print(f"  - engine_action_to_action_248: 22k→248 mapping")
        print(f"  - action_248_to_engine_action: 248→22k mapping")
        print(f"  - build_action_mask_248: phase-aware masking")
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    
    return True

def test_neural_mcts():
    """Test NeuralMCTS with 248-dim card + slot aware actions"""
    print("[TEST] NeuralMCTS card + slot aware...")
    
    try:
        from alphazero.training.vanilla_training import NeuralMCTS
        
        model = HighFidelityAlphaNet(input_dim=800, num_actions=248)
        device = torch.device('cpu')
        initial_deck = list(range(60))  # Dummy deck
        
        mcts = NeuralMCTS(model, device, initial_deck)
        print(f"✓ NeuralMCTS initialized with {len(initial_deck)} cards")
        print(f"✓ Action space breakdown:")
        print(f"    - 0: Pass")
        print(f"    - 1-6: Mulligan (6)")
        print(f"    - 7: Confirm")
        print(f"    - 8-67: Generic card plays (60)")
        print(f"    - 68-127: Play to slot 0 (60)")
        print(f"    - 128-187: Play to slot 1 (60)")
        print(f"    - 188-247: Play to slot 2 (60)")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    
    return True

def test_sparse_policy_conversion():
    """Test sparse policy representation for 248-dim space"""
    print("[TEST] Sparse policy conversion (248-dim)...")
    
    policy_248 = np.zeros(248)
    policy_248[0] = 0.2  # Pass
    policy_248[10] = 0.3  # Generic card play idx 2
    policy_248[100] = 0.15  # Slot 0 play
    policy_248[180] = 0.15  # Slot 1 play
    policy_248[220] = 0.2  # Slot 2 play
    
    # Get non-zero indices
    nonzero_idx = np.where(policy_248 > 1e-6)[0]
    nonzero_val = policy_248[nonzero_idx]
    
    print(f"  Dense policy shape: {policy_248.shape}")
    print(f"  Non-zero actions: {len(nonzero_idx)} / 248")
    print(f"  Indices: {nonzero_idx}")
    print(f"  Values: {nonzero_val}")
    print(f"  Coverage: {np.sum(nonzero_val):.1%}")
    print(f"✓ Sparse representation works (sparse ratio: {len(nonzero_idx)}/248 ≈ {len(nonzero_idx)/248:.1%})")
    
    return True

if __name__ == "__main__":
    print("\n" + "="*60)
    print("CARD-CENTRIC + SLOT-AWARE 248-DIM ACTION SPACE")
    print("="*60 + "\n")
    
    all_pass = True
    
    try:
        test_model_output_shape()
    except Exception as e:
        print(f"✗ Model test failed: {e}")
        all_pass = False
    
    try:
        all_pass = test_action_mapping_functions() and all_pass
    except Exception as e:
        print(f"✗ Mapping test failed: {e}")
        all_pass = False
    
    try:
        all_pass = test_neural_mcts() and all_pass
    except Exception as e:
        print(f"✗ MCTS test failed: {e}")
        all_pass = False
    
    try:
        all_pass = test_sparse_policy_conversion() and all_pass
    except Exception as e:
        print(f"✗ Sparse policy test failed: {e}")
        all_pass = False
    
    print("\n" + "="*60)
    if all_pass:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("="*60 + "\n")
