import json
import os
import engine_rust

def test_card_1419_fix():
    print("--- Testing Card 1419 Systematic Fix ---")
    
    # Load DB
    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        db_json = f.read()
    db = engine_rust.PyCardDatabase(db_json)
    
    # Initialize game
    gs = engine_rust.PyGameState(db)
    gs.debug_mode = True
    
    # Setup IDs
    card_1419_id = db.id_by_no("PL!S-bp2-006-P")
    cost_2_id = db.id_by_no("PL!-sd1-002-SD")
    cost_11_id = db.id_by_no("PL!-sd1-001-SD")
    
    print(f"Card 1419 ID: {card_1419_id}")
    print(f"Cost 2 Card ID: {cost_2_id}")
    print(f"Cost 11 Card ID: {cost_11_id}")
    
    # Setup game state
    # P0 has Card 1419 on stage (slot 0)
    # P0 has cost_2_id and cost_11_id in discard
    gs.set_stage_card(0, 0, card_1419_id)
    gs.set_discard_cards(0, [cost_2_id, cost_11_id])
    
    # Put some energy for P0
    gs.set_energy_cards(0, [0, 0, 0, 0])
    
    # Set phase to Response (to trigger ability)
    gs.phase = 10 # Phase::Response
    
    # Manually trigger ability 0 of Card 1419 (Activate)
    # PL!S-bp2-006-P Ability 0: [Activate] Play up to 2 members from discard with total cost <= 4
    try:
        gs.trigger_ability_on_card(0, card_1419_id, 0, 0)
    except Exception as e:
        print(f"Trigger failed (expected if it suspended): {e}")

    # Check for suspension
    print(f"Pending Choice Type: {gs.pending_choice_type}")
    print(f"Pending Card ID: {gs.pending_card_id}")
    
    if gs.pending_choice_type != "SELECT_DISCARD_PLAY":
        print("FAILED: Expected SELECT_DISCARD_PLAY suspension")
        return

    # Check legal actions - should only include cost_2_id
    actions = gs.get_legal_action_ids()
    print(f"Legal Actions (Card Selection): {actions}")
    
    # Choices start at 500. looked_cards[0] is cost_2, looked_cards[1] is cost_11.
    looked = gs.get_player(0).looked_cards
    print(f"Looked Cards: {looked}")
    
    # Verify that cost_11_id is NOT in looked cards
    if cost_11_id in looked:
        print("FAILED: cost_11_id should have been filtered out")
    if cost_2_id not in looked:
        print("FAILED: cost_2_id should be in looked cards")

    # Step: Select cost_2 (Action 500 if it's the only one)
    gs.step(500)
    
    print(f"After selecting card, Pending Choice Type: {gs.pending_choice_type}")
    if gs.pending_choice_type != "SELECT_STAGE":
        print("FAILED: Expected SELECT_STAGE suspension after card selection")
        return

    # Legal actions for Stage should be 600, 601, 602
    actions = gs.get_legal_action_ids()
    print(f"Legal Actions (Slot Selection): {actions}")
    if 601 not in actions:
        print("FAILED: Expected slot 601 to be legal")

    # Select slot 1
    gs.step(601)
    
    # Verify card 1419 played card to slot 1
    stage = gs.get_player(0).stage
    print(f"Stage after play: {stage}")
    if stage[1] != cost_2_id:
        print(f"FAILED: Expected card {cost_2_id} at slot 1, found {stage[1]}")

    # Since v was 2, and we played 1, it should check for next card.
    # But discard is now empty (or only has cost_11 which is filtered).
    # So it should finish.
    print(f"Final Phase: {gs.phase}")
    print(f"Pending Choice Type: {gs.pending_choice_type}")
    
    print("--- TEST PASSED ---")

if __name__ == "__main__":
    test_card_1419_fix()
