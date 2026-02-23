import sys
import os

# Add the project root to sys.path to import engine_rust
sys.path.append(os.getcwd())

import engine_rust
from engine_rust import PyGameState, PyCardDatabase

import io

def verify_logging():
    output = io.StringIO()
    def log_print(msg):
        print(msg)
        output.write(str(msg) + "\n")

    log_print("Testing Enriched Ability Logging...")
    
    # Load compiled cards
    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        cards_json = f.read()
    
    db = PyCardDatabase(cards_json)
    state = PyGameState(db)
    
    log_print(f"DEBUG: state methods/attributes: {dir(state)}")
    
    # Initialize game
    # Hazuki Ren (ID 4596)
    state.initialize_game_with_seed(
        [4596, 4596], [4596, 4596],
        [], [],
        [], [],
        123
    )
    
    # Skip to Main Phase (Phase 4)
    state.phase = 4
    state.current_player = 0
    
    # Give energy
    state.set_energy_cards(0, [152, 152, 152, 152, 152]) # Give plenty of energy
    
    # Setup hand: [Hazuki Ren, Some other card]
    state.set_hand_cards(0, [4596, 152]) # 4596 is Hazuki Ren
    
    # Debug info
    log_print(f"Current Player: {state.current_player}")
    log_print(f"Current Phase: {state.phase}")
    log_print(f"Legal Actions: {state.get_legal_action_ids()}")
    
    # Try to see if rule_log exists under another name if not directly
    has_rule_log = hasattr(state, "rule_log")
    log_print(f"DEBUG: state has rule_log: {has_rule_log}")
    
    # Scenario 1: Play Hazuki Ren (Trigger OnPlay)
    log_print("\n--- Phase: Play Card (Expected: TRIGGER + Pseudocode) ---")
    try:
        # ACTION_BASE_HAND (1000) + 0 (hand_idx)
        state.step(1000) 
    except Exception as e:
        log_print(f"FAILED to play card: {e}")
        # If it failed, check why
        if not has_rule_log:
             log_print("Cannot check rule_log because it is missing.")
        
    logs = getattr(state, "rule_log", [])
    found_trigger = False
    found_exec_start = False
    for log in logs:
        log_print(f"Log: {log}")
        if "[OnPlay]" in log and "Triggered for 葉月 恋" in log:
            found_trigger = True
        if "Bytecode execution started." in log:
            found_exec_start = True
            
    if found_trigger and found_exec_start:
         log_print("SUCCESS: Trigger and Execution Start logs found.")
    else:
         log_print(f"FAIL: trigger={found_trigger}, exec_start={found_exec_start}")

    # Scenario 2: Condition Failure
    log_print("\n--- Scenario 2: Condition Failure ---")
    state2 = PyGameState(db)
    state2.initialize_game_with_seed([4596], [4596], [], [], [], [], 456)
    state2.phase = 4
    state2.current_player = 0
    state2.set_energy_cards(0, [152, 152, 152, 152, 152])
    
    # Hand has only Hazuki Ren.
    state2.set_hand_cards(0, [4596])
    
    log_print("\n--- Phase: Play Card with Failed Condition (Expected: Failure Detail) ---")
    try:
        state2.step(1000)
    except Exception as e:
        log_print(f"Card play failed: {e}")
    
    logs2 = getattr(state2, "rule_log", [])
    found_failure = False
    for log in logs2:
        log_print(f"Log: {log}")
        if "ability did not activate because target condition was not met: Need 1 card in Hand" in log:
            found_failure = True
            
    if found_failure:
        log_print("SUCCESS: Detailed condition failure log found.")
    else:
         log_print("FAIL: Detailed condition failure log NOT found.")

    # Scenario 3: Activated Ability (Shibuya Kanon 4587)
    log_print("\n--- Scenario 3: Activated Ability ---")
    state3 = PyGameState(db)
    state3.initialize_game_with_seed([4587], [4587], [], [], [], [], 789)
    state3.phase = 4
    state3.current_player = 0
    state3.set_energy_cards(0, [152, 152, 152, 152, 152])
    
    # Put Shibuya Kanon on Stage
    state3.set_stage_card(0, 0, 4587)
    
    # Debug Shibuya Kanon state
    log_print(f"Scenario 3 Legal Actions: {state3.get_legal_action_ids()}")
    
    # Shibuya Kanon ability 0: Activated, Cost 0, Choice 1: Draw 1 card? 
    # Let's try picking an action from the list that looks like an ability.
    # Usually ACTION_BASE_MEMBER=2000. 
    # If 2000 is in the list, use it.
    
    log_print("\n--- Phase: Activate Ability (Expected: ACTIVATE + Pseudocode) ---")
    action_to_try = 2000
    if 2000 not in state3.get_legal_action_ids():
         # Fallback to whatever is available above 2000
         abilities = [a for a in state3.get_legal_action_ids() if a >= 2000]
         if abilities:
             action_to_try = abilities[0]
             log_print(f"Using alternate action ID: {action_to_try}")

    try:
        state3.step(action_to_try)
    except Exception as e:
        log_print(f"Activation failed: {e}")
        
    logs3 = getattr(state3, "rule_log", [])
    found_activate = False
    for log in logs3:
        log_print(f"Log: {log}")
        if "activates ability of 澁谷 かのん" in log:
            found_activate = True
            
    if found_activate:
        log_print("SUCCESS: Activated ability log found.")
    else:
        log_print("FAIL: Activated ability log NOT found.")

    with open("verification_log.txt", "w", encoding="utf-8") as f:
        f.write(output.getvalue())

if __name__ == "__main__":
    verify_logging()
