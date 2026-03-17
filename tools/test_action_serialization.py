#!/usr/bin/env python3
"""
Test action button serialization for all action types.
Validates that:
1. All action types are present in legal_actions
2. All action types have correct metadata
3. Card targets (source_card_id) are present for all applicable action types
4. Action descriptions are complete and non-empty
"""

import json
import sys
import os

# --- PATH SETUP ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import engine_rust
from engine.game.state_utils import get_base_id
from backend.rust_serializer import RustGameStateSerializer, SERIALIZER_STRINGS
from engine.game.data_loader import CardDataLoader

def create_test_game():
    """Create a simple test game state."""
    # Load card databases
    DATA_DIR = os.path.join(PROJECT_ROOT, "data")
    cards_path = os.path.join(DATA_DIR, "cards.json")
    loader = CardDataLoader(cards_path)
    member_db, live_db, energy_db = loader.load()
    
    engine = engine_rust.GameEngine(member_db, live_db, energy_db, None)
    
    # Create initial game with fixed decks
    p0_deck = [1001] * 20 + [2001] * 10  # Mixed member cards
    p1_deck = [1002] * 20 + [2002] * 10
    p0_energy = [3001] * 7
    p1_energy = [3002] * 7
    p0_lives = [1, 1, 1, 1, 1, 1, 1]
    p1_lives = [1, 1, 1, 1, 1, 1, 1]
    
    engine.init_game(
        p0_deck=list(p0_deck),
        p1_deck=list(p1_deck),
        p0_energy=list(p0_energy),
        p1_energy=list(p1_energy),
        p0_lives=list(p0_lives),
        p1_lives=list(p1_lives),
        seed=12345
    )
    return engine, member_db, live_db, energy_db

def test_action_serialization():
    """Test that all action types serialize correctly with card targeting."""
    print("=" * 80)
    print("ACTION SERIALIZATION TEST")
    print("=" * 80)
    
    try:
        engine, member_db, live_db, energy_db = create_test_game()
        serializer = RustGameStateSerializer(member_db, live_db, energy_db)
        
        # Get game state
        gs = engine.get_state_object(member_db, live_db, energy_db)
        serialized = serializer.serialize_state(gs, viewer_idx=0, lang="jp")
        
        legal_actions = serialized.get("legal_actions", [])
        print(f"\nTotal legal actions: {len(legal_actions)}")
        
        # Group actions by type
        action_types = {}
        source_card_ids = {}
        descriptions = {}
        
        for action in legal_actions:
            action_id = action.get("id")
            action_type = action.get("type", "UNKNOWN")
            source_card_id = action.get("source_card_id")
            desc = action.get("desc", action.get("name", ""))
            
            if action_type not in action_types:
                action_types[action_type] = []
            action_types[action_type].append(action_id)
            
            if source_card_id is not None:
                if action_type not in source_card_ids:
                    source_card_ids[action_type] = 0
                source_card_ids[action_type] += 1
            
            if not desc or desc.startswith("Action"):
                if action_type not in descriptions:
                    descriptions[action_type] = []
                descriptions[action_type].append(f"ID:{action_id}")
        
        print("\n" + "=" * 80)
        print("ACTION TYPES PRESENT:")
        print("=" * 80)
        for action_type in sorted(action_types.keys()):
            count = len(action_types[action_type])
            source_count = source_card_ids.get(action_type, 0)
            pct = (source_count / count * 100) if count > 0 else 0
            print(f"  {action_type:20s}: {count:3d} actions, {source_count:3d} with source_card_id ({pct:5.1f}%)")
            if action_type in descriptions and descriptions[action_type]:
                print(f"    ⚠️  {len(descriptions[action_type])} actions with poor descriptions: {descriptions[action_type][:3]}")
        
        # Expected action types with card targets
        expected_with_targets = {
            "PLAY": "hand cards being played",
            "ABILITY": "stage member abilities",
            "HAND_ABILITY": "hand member abilities",
            "DISCARD_ABILITY": "discard member abilities",
            "SELECT_HAND": "hand card selection",
            "SELECT_STAGE": "stage slot selection",
            "SELECT_LIVE": "live zone selection",
            "MULLIGAN": "mulligan card selection",
            "LIVESET": "live set card selection",
            "ENERGY": "energy card selection",
            "CHOICE": "ability modal choices",
        }
        
        print("\n" + "=" * 80)
        print("VALIDATION RESULTS:")
        print("=" * 80)
        
        issues = []
        
        # Check for expected action types
        for action_type in expected_with_targets.keys():
            if action_type not in action_types:
                issues.append(f"❌ Missing action type: {action_type}")
            elif source_card_ids.get(action_type, 0) == 0:
                issues.append(f"❌ {action_type}: NO SOURCE_CARD_ID (expected for {expected_with_targets[action_type]})")
        
        # Validate specific action types
        if "HAND_ABILITY" in action_types and len(action_types["HAND_ABILITY"]) > 0:
            print("✅ HAND_ABILITY actions are being serialized")
        else:
            issues.append("❌ HAND_ABILITY actions NOT found (critical gap)")
        
        if "DISCARD_ABILITY" in action_types and len(action_types["DISCARD_ABILITY"]) > 0:
            print("✅ DISCARD_ABILITY actions are being serialized")
        else:
            issues.append("❌ DISCARD_ABILITY actions NOT found (critical gap)")
        
        # Check PLAY action metadata
        if "PLAY" in action_types:
            play_action = next((a for a in legal_actions if a.get("type") == "PLAY"), None)
            if play_action and play_action.get("source_card_id"):
                print("✅ PLAY actions have source_card_id (hand index)")
            else:
                issues.append("❌ PLAY actions missing source_card_id")
        
        # Check descriptions
        empty_descs = 0
        for action in legal_actions:
            desc = action.get("desc", "")
            if not desc or desc == "Action " + str(action.get("id")):
                empty_descs += 1
        
        if empty_descs > len(legal_actions) * 0.1:
            issues.append(f"⚠️  {empty_descs} actions ({empty_descs/len(legal_actions)*100:.1f}%) have generic descriptions")
        else:
            print(f"✅ Action descriptions: {empty_descs}/{len(legal_actions)} generic (acceptable threshold)")
        
        print("\n" + "=" * 80)
        if issues:
            print("ISSUES FOUND:")
            for issue in issues:
                print(f"  {issue}")
            return False
        else:
            print("✅ ALL TESTS PASSED")
            return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_action_serialization()
    sys.exit(0 if success else 1)
