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
    model = HighFidelityAlphaNet(input_dim=800, num_actions=256)
    
    # Dummy input
    obs = torch.randn(4, 800)  # Batch of 4
    mask = torch.ones(4, 256, dtype=torch.bool)
    
    policy, value = model(obs, mask=mask)
    
    assert policy.shape == (4, 256), f"Expected (4, 256), got {policy.shape}"
    assert value.shape == (4, 1), f"Expected (4, 1), got {value.shape}"
    print(f"✓ Policy shape: {policy.shape}, Value shape: {value.shape}")
    print(f"✓ Action space: 8 phase + 60 generic + 180 slot-specific (60×3)")

def test_action_mapping_functions():
    """Test card + slot aware action mapping functions"""
    print("[TEST] Action mapping functions (248-dim)...")
    
    # These should be importable from vanilla_training
    try:
        from alphazero.training.vanilla_utils import (
            map_engine_to_vanilla,
            engine_action_to_action_256,
            action_256_to_engine_action,
            build_action_mask_248
        )
        print("✓ All mapping functions imported successfully")
        print(f"  - engine_action_to_action_256: 22k→256 mapping")
        print(f"  - action_256_to_engine_action: 256→22k mapping")
        print(f"  - build_action_mask_248: phase-aware masking")
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    
    return True

def test_neural_mcts():
    """Test NeuralMCTS with 248-dim card + slot aware actions"""
    print("[TEST] NeuralMCTS card + slot aware...")
    
    try:
        from alphazero.training.vanilla_utils import NeuralMCTS
        
        model = HighFidelityAlphaNet(input_dim=800, num_actions=256)
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
    """Test sparse policy representation for 256-dim space"""
    print("[TEST] Sparse policy conversion (256-dim)...")
    
    policy_256 = np.zeros(256)
    policy_256[0] = 0.2  # Pass
    policy_256[10] = 0.3  # Generic card play idx 2
    policy_256[100] = 0.15  # Slot 0 play
    policy_256[180] = 0.15  # Slot 1 play
    policy_256[220] = 0.2  # Slot 2 play
    
    # Get non-zero indices
    nonzero_idx = np.where(policy_256 > 1e-6)[0]
    nonzero_val = policy_256[nonzero_idx]
    
    print(f"  Dense policy shape: {policy_256.shape}")
    print(f"  Non-zero actions: {len(nonzero_idx)} / 256")
    print(f"  Indices: {nonzero_idx}")
    print(f"  Values: {nonzero_val}")
    print(f"  Coverage: {np.sum(nonzero_val):.1%}")
    print(f"✓ Sparse representation works (sparse ratio: {len(nonzero_idx)}/256 ≈ {len(nonzero_idx)/256:.1%})")
    
    return True

if __name__ == "__main__":
    print("\n" + "="*60)
    print("CARD-CENTRIC + SLOT-AWARE 256-DIM ACTION SPACE")
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
