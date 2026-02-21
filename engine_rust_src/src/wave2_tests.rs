use crate::test_helpers::{create_test_db, create_test_state};
use crate::core::logic::*;
use crate::core::logic::card_db::LOGIC_ID_MASK;
use crate::core::hearts::HeartBoard;
// use std::collections::HashMap;

fn add_test_member(db: &mut CardDatabase, mut member: MemberCard) {
    member.hearts_board = HeartBoard::from_array(&member.hearts);
    member.blade_hearts_board = HeartBoard::from_array(&member.blade_hearts);
    let id = member.card_id;
    println!("DEBUG: Adding Member ID {} to database.", id);
    db.members.insert(id, member.clone());
    let logic_id = (id as usize) & LOGIC_ID_MASK as usize;
    if logic_id < db.members_vec.len() {
        db.members_vec[logic_id] = Some(member);
        println!("DEBUG: Member ID {} added to members_vec at index {}.", id, logic_id);
    } else {
        println!("DEBUG: Member ID {} OUT OF RANGE for members_vec (len: {}).", id, db.members_vec.len());
    }
}

fn add_test_live(db: &mut CardDatabase, live: LiveCard) {
    let id = live.card_id;
    db.lives.insert(id, live.clone());
    if (id as usize) < db.lives_vec.len() {
        db.lives_vec[(id as usize) & LOGIC_ID_MASK as usize] = Some(live);
    }
}

#[test]
fn test_opcode_reduce_yell_count() {
    let db = create_test_db();
    let mut state = create_test_state();
    
    // O_REDUCE_YELL_COUNT 1
    let ctx = AbilityContext { player_id: 0, ..Default::default() };
    let bc = vec![O_REDUCE_YELL_COUNT, 1, 0, 0, O_RETURN, 0, 0, 0];
    state.resolve_bytecode(&db, &bc, &ctx);
    
    assert_eq!(state.core.players[0].yell_count_reduction, 1);
    
    // Test do_yell reduction
    // Setup deck
    state.core.players[0].deck = vec![3010, 3002, 3003, 3004, 3005].into();
    
    // Try to yell 3 cards. Should yell 3 - 1 = 2.
    let revealed = state.do_yell(&db, 3);
    assert_eq!(revealed.len(), 2);
    // Revealed cards should be 3005 and 3004 (pop order)
    assert_eq!(revealed[0], 3005);
    assert_eq!(revealed[1], 3004);
    
    // Try to yell 1 card. Should yell 1 - 1 = 0.
    let revealed_zero = state.do_yell(&db, 1);
    assert_eq!(revealed_zero.len(), 0);
}

#[test]
fn test_opcode_swap_area() {
    let db = create_test_db();
    let mut state = create_test_state();
    
    // Setup Stage: [19, 20, 30]
    state.core.players[0].stage = [10, 20, 30];
    // Setup Tapped: [false, true, false]
    state.core.players[0].set_tapped(0, false);
    state.core.players[0].set_tapped(1, true);
    state.core.players[0].set_tapped(2, false);
    
    let ctx = AbilityContext { player_id: 0, ..Default::default() };
    // O_SWAP_AREA (Rotate Right: 0->1, 1->2, 2->0)
    // 10->Pos1, 20->Pos2, 30->Pos0
    // Result: [30, 10, 20]
    let bc = vec![O_SWAP_AREA, 0, 0, 0, O_RETURN, 0, 0, 0];
    state.resolve_bytecode(&db, &bc, &ctx);
    
    assert_eq!(state.core.players[0].stage, [30, 10, 20]);
    // Tapped follows: 30(false)->Pos0, 10(false)->Pos1, 20(true)->Pos2
    assert_eq!(state.core.players[0].is_tapped(0), false);
    assert_eq!(state.core.players[0].is_tapped(1), false);
    assert_eq!(state.core.players[0].is_tapped(2), true);
}

#[test]
fn test_opcode_negate() {
    let mut db = create_test_db();
    let mut state = create_test_state();
    
    // Setup negated triggers
    let target_cid = 99999;
    let ctx = AbilityContext { player_id: 0, target_slot: 0, source_card_id: target_cid, ..Default::default() }; 
    state.core.players[0].stage[0] = target_cid; // Target member
    
    // O_NEGATE_EFFECT (27), val=2 (OnLiveStart)
    let bc = vec![O_NEGATE_EFFECT, 2, 0, 0, O_RETURN, 0, 0, 0];
    state.resolve_bytecode(&db, &bc, &ctx);
    
    // Check negated_triggers
    assert_eq!(state.core.players[0].negated_triggers.len(), 1);
    assert_eq!(state.core.players[0].negated_triggers[0], (target_cid, TriggerType::OnLiveStart, 1));
    
    // Now verify trigger logic SKIPS this card for OnLiveStart
    add_test_member(&mut db, MemberCard {
         card_id: target_cid,
         abilities: vec![
             Ability { 
                 trigger: TriggerType::OnLiveStart, 
                 bytecode: vec![O_DRAW, 1, 0, 0], // Draw 1
                 ..Default::default() 
             }
         ],
         ..Default::default()
    });
    
    // Ensure deck has cards
    state.core.players[0].deck = vec![3010].into();
    state.core.players[0].hand = vec![].into();
    
    // Trigger OnLiveStart
    let trigger_ctx = AbilityContext { player_id: 0, source_card_id: target_cid, ..Default::default() };
    println!("DEBUG: Triggering OnLiveStart. Negated: {:?}", state.core.players[0].negated_triggers);
    state.trigger_abilities(&db, TriggerType::OnLiveStart, &trigger_ctx);
    
    // Should NOT have drawn card (hand size 0)
    assert_eq!(state.core.players[0].hand.len(), 0);
    
    // Clear negation manually to verify it DOES work without negation
    state.core.players[0].negated_triggers.clear();
    state.trigger_abilities(&db, TriggerType::OnLiveStart, &trigger_ctx);
    
    // Should HAVE drawn card (hand size 1)
    assert_eq!(state.core.players[0].hand.len(), 1);
}

#[test]
fn test_granted_ability_propagation_cost() {
    let mut db = create_test_db();
    let mut state = create_test_state();
    
    // 1. Create source card with grantable ability
    let source_id = 1900;
    add_test_member(&mut db, MemberCard {
        card_id: source_id,
        abilities: vec![
            Ability {
                trigger: TriggerType::Constant,
                bytecode: vec![O_REDUCE_COST, 1, 0, 0, O_RETURN, 0, 0, 0],
                ..Default::default()
            }
        ],
        ..Default::default()
    });
    
    // 2. Create target card
    add_test_member(&mut db, MemberCard {
        card_id: 110, 
        cost: 5, 
        ..Default::default()
    });
    
    // 3. Grant Ability to Card 110
    state.core.players[0].stage[0] = -1; // Slot must be empty to check "play cost" without baton touch
    state.core.players[0].granted_abilities.push((110, source_id, 0)); 
    
    // 4. Check Cost
    let cost = state.get_member_cost(0, 110, 0, -1, &db, 0);
    assert_eq!(cost, 4); // 5 - 1 = 4
}

#[test]
fn test_granted_ability_propagation_hearts() {
    let mut db = create_test_db();
    let mut state = create_test_state();
    
    // Card 3003: 1 Green Heart
    add_test_member(&mut db, MemberCard {
        card_id: 3003, 
        hearts: [0, 0, 0, 1, 0, 0, 0], // Green (idx 3) = 1
        ..Default::default()
    });
    
    // Source Card 3900: Grant "Constant: Add 1 Pink Heart (idx 0)"
    let source_id = 3900;
    add_test_member(&mut db, MemberCard {
        card_id: source_id,
        abilities: vec![
            Ability {
                trigger: TriggerType::Constant,
                bytecode: vec![O_ADD_HEARTS, 1, 0, 0, O_RETURN, 0, 0, 0], // O_ADD_HEARTS [count, color, 0]
                ..Default::default()
            }
        ],
        ..Default::default()
    });
    
    state.core.players[0].stage[0] = 3003;
    state.core.players[0].granted_abilities.push((3003, source_id, 0));
    
    // Check Total Hearts
    let hearts = state.get_effective_hearts(0, 0, &db, 0); // Check slot 0
    let arr = hearts.to_array();
    assert_eq!(arr[3], 1); // Original Green
    assert_eq!(arr[0], 1); // Granted Pink
}

#[test]
fn test_granted_ability_propagation_score() {
    let mut db = create_test_db();
    let mut state = create_test_state();
    
    // Source Card 900: Grant "Constant: Boost Score +500"
    let source_id = 900;
    add_test_member(&mut db, MemberCard {
        card_id: source_id,
        abilities: vec![
            Ability {
                trigger: TriggerType::Constant,
                bytecode: vec![O_BOOST_SCORE, 500, 0, 0, O_RETURN, 0, 0, 0], 
                ..Default::default()
            }
        ],
        ..Default::default()
    });
    
    // Target Card 110 on stage
    state.core.players[0].stage[0] = 110;
    add_test_member(&mut db, MemberCard { card_id: 110, ..Default::default() });
    
    state.core.players[0].granted_abilities.push((110, source_id, 0));
    
    // Performance results
    state.ui.performance_results.insert(0, serde_json::json!({
        "success": true,
        "lives": [
            {"slot_idx": 0, "passed": true, "score": 1000},
            {"slot_idx": 1, "passed": false, "score": 0},
            {"slot_idx": 2, "passed": false, "score": 0}
        ],
        "yell_score_bonus": 0,
        "volume_icons": 0
    }));
    state.core.players[0].live_zone[0] = 10050; // Mock live card id 
    state.core.players[0].live_zone[1] = -1;
    state.core.players[0].live_zone[2] = -1;

    // Register 10050 in DB so do_live_result doesn't skip it
    add_test_live(&mut db, LiveCard {
        card_id: 10050,
        score: 1000,
        ..Default::default()
    });
    
    // The logic in do_live_result:
    // 1. Sum scores from performance_results (1000)
    // 2. Add live_score_bonus (9 initially)
    // 3. Iterate granted_abilities and add to live_score_bonus
    // 4. Update scores[p]
    
    state.do_live_result(&db);
    
    // Check final score in state via performance_results["total_score"] or similar?
    // do_live_result updates performance_results and then clears them in finalize_live_result
    // BUT it should save them to last_performance_results first.
    let res = state.ui.last_performance_results.get(&0u8).expect("Last performance results for P0 missing!");
    println!("DEBUG: test_score: res JSON: {:?}", res);
    let total = res.get("total_score").expect("total_score missing from res object").as_u64().expect("total_score is not u64");
    
    // Expected: 1000 (base) + 500 (bonus) = 1500
    assert_eq!(total, 1500);
}

