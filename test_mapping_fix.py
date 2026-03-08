#!/usr/bin/env python3
"""Quick test script to verify the mapping fix for RPS and Turn Choice actions."""

import sys
import json
from pathlib import Path

# Add project root to path
root_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(root_dir))

# Test the mapping function directly
LOGIC_ID_MASK = 0x0FFF

def map_engine_to_vanilla(p_data, engine_id, initial_deck):
    """Maps engine action ID to vanilla 128-dim action space."""
    if engine_id == 0: return 0  # Pass
    if 300 <= engine_id < 306: return 1 + (engine_id - 300) # Mulligan
    if engine_id == 11000: return 7  # Confirm
    
    # Play Member (Hand)
    if 1000 <= engine_id < 1600:
        hand_idx = (engine_id - 1000) // 10
        if hand_idx < len(p_data.get('hand', [])):
            cid = p_data['hand'][hand_idx]
            try:
                # Use LOGIC_ID_MASK for robust matching
                target_cid = cid & LOGIC_ID_MASK
                deck_logic_ids = [c & LOGIC_ID_MASK for c in initial_deck]
                deck_idx = deck_logic_ids.index(target_cid)
                return 8 + (deck_idx % 60)
            except ValueError:
                return -1
                
    # Set Live (Selection/Slot)
    if 400 <= engine_id < 500:
        hand_idx = engine_id - 400
        if hand_idx < len(p_data.get('hand', [])):
            cid = p_data['hand'][hand_idx]
            try:
                target_cid = cid & LOGIC_ID_MASK
                deck_logic_ids = [c & LOGIC_ID_MASK for c in initial_deck]
                deck_idx = deck_logic_ids.index(target_cid)
                # Ensure it fits in 68-127 range (60 slots)
                return 68 + (deck_idx % 60)
            except ValueError:
                return -1
        return 68 

    # Select Success Live (Minimal Index 0)
    if 600 <= engine_id < 603:
        return 0

    # Turn Choice (Go First / Second)
    if engine_id in [5000, 5001]:
        return 0 # Map to Pass/Done for vanilla 128 space
    
    # RPS (Rock-Paper-Scissors) - Phase -3
    # P1: 20000 (Rock), 20001 (Paper), 20002 (Scissors)
    # P2: 21000 (Rock), 21001 (Paper), 21002 (Scissors)
    if 20000 <= engine_id <= 20002 or 21000 <= engine_id <= 21002:
        return 0 # Map to Pass - RPS outcome doesn't affect vanilla training

    return -1


def test_mapping():
    """Test the mapping function with RPS and Turn Choice IDs."""
    print("Testing mapping fix...")
    print("=" * 60)
    
    # Test data
    p_data = {'hand': [376, 258, 370, 28921, 370, 245]}
    initial_deck = []
    
    # Test RPS IDs
    print("\n--- RPS Phase IDs (Phase -3) ---")
    rps_ids = [
        (20000, "P1 Rock"),
        (20001, "P1 Paper"),
        (20002, "P1 Scissors"),
        (21000, "P2 Rock"),
        (21001, "P2 Paper"),
        (21002, "P2 Scissors"),
    ]
    
    all_passed = True
    for engine_id, desc in rps_ids:
        vid = map_engine_to_vanilla(p_data, engine_id, initial_deck)
        status = "✓ PASS" if vid == 0 else "✗ FAIL"
        print(f"  {desc:12s}: Engine ID {engine_id} -> VID {vid} {status}")
        if vid != 0:
            all_passed = False
    
    # Test Turn Choice IDs
    print("\n--- Turn Choice IDs ---")
    turn_choice_ids = [
        (5000, "Go First"),
        (5001, "Go Second"),
    ]
    
    for engine_id, desc in turn_choice_ids:
        vid = map_engine_to_vanilla(p_data, engine_id, initial_deck)
        status = "✓ PASS" if vid == 0 else "✗ FAIL"
        print(f"  {desc:12s}: Engine ID {engine_id} -> VID {vid} {status}")
        if vid != 0:
            all_passed = False
    
    # Test Normal IDs that should still work
    print("\n--- Normal Action IDs (should still work) ---")
    normal_ids = [
        (0, "Pass", 0),
        (300, "Mulligan 0", 1),
        (305, "Mulligan 5", 6),
        (11000, "Confirm", 7),
    ]
    
    for engine_id, desc, expected_vid in normal_ids:
        vid = map_engine_to_vanilla(p_data, engine_id, initial_deck)
        status = "✓ PASS" if vid == expected_vid else "✗ FAIL"
        print(f"  {desc:12s}: Engine ID {engine_id} -> VID {vid} (expected {expected_vid}) {status}")
        if vid != expected_vid:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("All tests PASSED! ✓")
    else:
        print("Some tests FAILED! ✗")
    
    return all_passed


if __name__ == "__main__":
    success = test_mapping()
    sys.exit(0 if success else 1)
