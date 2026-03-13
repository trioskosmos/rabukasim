#!/usr/bin/env python3
"""
Test to verify rule log messages are being generated correctly.
"""

import sys
sys.path.insert(0, '.')

import json
from engine_rust import PyGameState, PyCardDatabase

def test_phase_transitions():
    """Test that phase transitions are logged"""
    print("="*60)
    print("Testing Phase Transition Logging")
    print("="*60)
    
    # Load card database from JSON
    with open('data/cards_compiled.json', 'r', encoding='utf-8') as f:
        cards_json = json.load(f)
    
    db = PyCardDatabase(json.dumps(cards_json))
    gs = PyGameState(db)
    
    # Use same deck as stress_test.py to match working configuration
    p0_deck = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] * 3  # 30 main cards
    p1_deck = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] * 3  # 30 main cards
    p0_lives = [1001, 1002, 1003]  # 3 live cards
    p1_lives = [1001, 1002, 1003]  # 3 live cards
    
    print("Initializing game...")
    gs.initialize_game(p0_deck, p1_deck, [], [], p0_lives, p1_lives)
    
    # Use play_mirror_match to generate a complete game with logs
    print("Running mirror match to generate logs...")
    result = gs.play_mirror_match(100, 100, 0, 0)  # mcts_p0, mcts_p1, heur_p0, heur_p1
    winner, turns = result
    
    # Now check the logs
    print(f"Game completed. Winner: {winner}, Turns: {turns}")
    print(f"Final Phase: {gs.phase_name} (ID: {gs.phase})")
    if winner == -1:
        print("  WARNING: Game did not reach Terminal phase (possible early exit)")
    
    # Get the rule logs
    final_logs = gs.rule_log if gs.rule_log else []
    print(f"\n--- Final Log Summary ---")
    print(f"Total entries: {len(final_logs)}")
    
    # Show ALL logs first
    print(f"\n--- All Logs (First 20) ---")
    for i, log in enumerate(final_logs[:20]):
        print(f"  [{i}] {log}")
    
    # Count phase-related logs
    phase_logs = [log for log in final_logs if "Entering" in log or "Phase" in log]
    draw_logs = [log for log in final_logs if "DRAW" in log or "draws" in log]
    rule_logs = [log for log in final_logs if "[Rule" in log]
    
    print(f"Phase transition logs: {len(phase_logs)}")
    print(f"Draw event logs: {len(draw_logs)}")
    print(f"Rule-based logs: {len(rule_logs)}")
    
    # Show some examples
    print(f"\n--- Sample Phase Transition Logs ---")
    for log in phase_logs[:10]:
        print(f"  {log}")
    print(f"\n--- Sample Draw Logs ---")
    for log in draw_logs[:5]:
        print(f"  {log}")
    
    print(f"\n--- Sample Rule Logs ---")
    for log in rule_logs[:5]:
        print(f"  {log}")
    
    # Verify expected logs exist
    print("\n--- Verification ---")
    has_energy_phase = any("Entering Energy Phase" in log for log in final_logs)
    has_draw_phase = any("Entering Draw Phase" in log for log in final_logs)
    has_main_phase = any("Entering Main Phase" in log for log in final_logs)
    has_draw_event = any("DRAW" in log for log in final_logs)
    
    print(f"[OK] Energy Phase log found: {has_energy_phase}")
    print(f"[OK] Draw Phase log found: {has_draw_phase}")
    print(f"[OK] Main Phase log found: {has_main_phase}")
    print(f"[OK] Draw event logged: {has_draw_event}")
    
    all_passed = has_energy_phase and has_draw_phase and has_main_phase and has_draw_event
    result_text = "*** ALL TESTS PASSED ***" if all_passed else "*** SOME TESTS FAILED ***"
    print(f"\nResult: {result_text}")
    
    return all_passed

if __name__ == "__main__":
    try:
        success = test_phase_transitions()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(2)
