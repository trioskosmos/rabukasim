import torch
import numpy as np
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir))

from alphazero.alphanet import AlphaNet, ACTION_TYPE_TABLE, ACTION_SUB_TABLE

def verify_lut_consistency():
    print("Verifying LUT Parity between Global Tables and Model Buffers...")
    model = AlphaNet()
    
    # Check a few critical IDs
    test_ids = [
        0,      # Pass
        300,    # Mulligan
        1000,   # PlayMember
        2200,   # PlayMemberChoice
        5000,   # TurnChoice (Critically sensitive)
        8300,   # ActivateMember (Critically sensitive - Slot 0, AB 0)
        8400,   # ActivateMember (Slot 1, AB 0)
        20000,  # RPS
    ]
    
    m_types = model.action_type_lut.cpu().numpy()
    m_subs = model.action_sub_lut.cpu().numpy()
    
    all_pass = True
    for aid in test_ids:
        expected_t = ACTION_TYPE_TABLE[aid]
        expected_s = ACTION_SUB_TABLE[aid]
        
        actual_t = m_types[aid]
        actual_s = m_subs[aid]
        
        status = "PASS" if (expected_t == actual_t and expected_s == actual_s) else "FAIL"
        if status == "FAIL": all_pass = False
        
        print(f"ID {aid:5d}: Expected({expected_t}, {expected_s}) | Actual({actual_t}, {actual_s}) -> {status}")

    if all_pass:
        print("\n✅ GLOBAL PARITY VERIFIED. Model LUTs match Engine Decomposition.")
    else:
        print("\n❌ PARITY ERROR DETECTED.")
        sys.exit(1)

if __name__ == "__main__":
    verify_lut_consistency()
