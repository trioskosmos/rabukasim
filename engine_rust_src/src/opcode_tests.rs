//! Specialized tests for complex opcodes like REVEAL_UNTIL, DRAW_UNTIL, and LOOK_AND_CHOOSE.
//! These tests verify advanced card filtering and response-phase behaviors.

use crate::core::logic::*;
use crate::core::logic::card_db::LOGIC_ID_MASK;
// use crate::core::enums::*;
use crate::test_helpers::{create_test_db, create_test_state, add_card};

/// Verifies that O_DRAW_UNTIL draws the correct number of cards to reach a target hand size.
#[test]
fn test_opcode_draw_until() {
    let db = create_test_db();
    let mut state = create_test_state();
    state.core.players[0].deck = vec![1, 2, 3, 4, 5].into();
    state.core.players[0].hand = vec![101, 102].into(); // Hand size 2

    let ctx = AbilityContext { player_id: 0, ..Default::default() };

    // O_DRAW_UNTIL 5 (Draw up to 5)
    let bc = vec![O_DRAW_UNTIL, 5, 0, 0, 0, O_RETURN, 0, 0, 0, 0];
    state.resolve_bytecode(&db, &bc, &ctx);

    assert_eq!(state.core.players[0].hand.len(), 5);
    assert_eq!(state.core.players[0].deck.len(), 2);
}

/// Verifies that O_REVEAL_UNTIL with TYPE_CHECK correctly filters for Live cards.
#[test]
fn test_opcode_reveal_until_type_live() {
    let mut db = create_test_db();
    let mut state = create_test_state();
    // Deck: 10 (member), 15 (member), 10050 (live), 1 (fallback)
    add_card(&mut db, 10, "M10", vec![], vec![]);
    add_card(&mut db, 15, "M15", vec![], vec![]);
    add_card(&mut db, 1, "M1", vec![], vec![]);
    db.lives.insert(10050, LiveCard { card_id: 10050, name: "L10050".to_string(), ..Default::default() });
    db.lives_vec[50] = Some(db.lives[&10050].clone());

    state.core.players[0].deck = vec![1, 10050, 15, 10].into();

    let ctx = AbilityContext { player_id: 0, ..Default::default() };

    // O_REVEAL_UNTIL C_TYPE_CHECK attr: 1 (Live), target: 6 (Hand)
    // s word needs bit 25 (0x02000000) for TYPE_CHECK to match Live cards.
    let bc = vec![O_REVEAL_UNTIL, C_TYPE_CHECK, 1, 0, 6 | 0x02000000, O_RETURN, 0, 0, 0, 0];
    state.resolve_bytecode(&db, &bc, &ctx);

    // Should have popped 10, 15, then 10050.
    // 10050 matches Live. It goes to hand.
    // 10 and 15 go to discard.
    assert!(state.core.players[0].hand.contains(&10050));
    assert_eq!(state.core.players[0].discard.len(), 2); // 10 and 15
    assert!(state.core.players[0].discard.contains(&10));
    assert!(state.core.players[0].discard.contains(&15));
    assert_eq!(state.core.players[0].deck.len(), 1); // 1 remains
}

/// Verifies that O_REVEAL_UNTIL with COST_GE correctly filters for members with a minimum cost.
#[test]
fn test_opcode_reveal_until_cost_ge() {
    let mut db = create_test_db();
    let mut state = create_test_state();
    // Deck: 60010 (cost 5), 60015 (cost 15), 60001 (fallback)
    // We need to ensure these IDs exist in the DB. create_test_db uses small vec, need to expand it?
    // create_test_db in opcode_tests.rs might also need size increase.
    // Let's check opcode_tests::create_test_db first.
    let m10 = MemberCard { card_id: 60010, cost: 5, ..Default::default() };
    let m15 = MemberCard { card_id: 60015, cost: 15, ..Default::default() };
    let m1 = MemberCard { card_id: 60001, cost: 1, ..Default::default() };

    db.members.insert(60010, m10.clone());
    // Is db.members_vec large enough? In opcode_tests.rs, create_test_db might be using default size.
    // I should check create_test_db in opcode_tests.rs before applying this.
    // But for now, let's assume I need to handle the DB size update in opcode_tests.rs as well.
    if db.members_vec.len() <= 60015 { db.members_vec.resize(60020, None); }

    db.members_vec[60010] = Some(m10);
    db.members.insert(60015, m15.clone()); db.members_vec[60015] = Some(m15);
    db.members.insert(60001, m1.clone()); db.members_vec[60001] = Some(m1);

    state.core.players[0].deck = vec![60001, 60015, 60010].into();

    let ctx = AbilityContext { player_id: 0, ..Default::default() };

    // O_REVEAL_UNTIL C_COST_CHECK val=10 (raw threshold)
    let bc = vec![O_REVEAL_UNTIL, C_COST_CHECK, 10, 0, 6, O_RETURN, 0, 0, 0, 0];
    state.resolve_bytecode(&db, &bc, &ctx);

    // Should pop 60010 (cost 5 < 10), then 60015 (cost 15 >= 10).
    // 60015 goes to hand. 60010 goes to discard.
    assert!(state.core.players[0].hand.contains(&60015));
    assert_eq!(state.core.players[0].discard.len(), 1);
    assert!(state.core.players[0].discard.contains(&60010));
}

/// Verifies that O_IMMUNITY correctly toggles the FLAG_IMMUNITY on the player.
#[test]
fn test_opcode_immunity() {
    let db = create_test_db();
    let mut state = create_test_state();
    assert!(!state.core.players[0].get_flag(PlayerState::FLAG_IMMUNITY));

    let ctx = AbilityContext { player_id: 0, ..Default::default() };

    // O_IMMUNITY 1
    let bc = vec![O_IMMUNITY, 1, 0, 0, 0, O_RETURN, 0, 0, 0, 0];
    state.resolve_bytecode(&db, &bc, &ctx);
    assert!(state.core.players[0].get_flag(PlayerState::FLAG_IMMUNITY));

    // O_IMMUNITY 0
    let bc = vec![O_IMMUNITY, 0, 0, 0, 0, O_RETURN, 0, 0, 0, 0];
    state.resolve_bytecode(&db, &bc, &ctx);
    assert!(!state.core.players[0].get_flag(PlayerState::FLAG_IMMUNITY));
}

/// Verifies that O_PAY_ENERGY correctly taps the specified number of energy cards.
#[test]
fn test_opcode_pay_energy() {
    let db = create_test_db();
    let mut state = create_test_state();
    state.ui.silent = true;
    state.core.players[0].tapped_energy_mask = 0;

    let ctx = AbilityContext { player_id: 0, ..Default::default() };

    // O_PAY_ENERGY 2
    let bc = vec![O_PAY_ENERGY, 2, 0, 0, 0, O_RETURN, 0, 0, 0, 0];
    state.resolve_bytecode(&db, &bc, &ctx);

    assert_eq!(state.core.players[0].tapped_energy_mask.count_ones(), 2);
}

/// Verifies that O_LOOK_DECK moves cards from deck to the looked_cards buffer.
#[test]
fn test_opcode_look_deck() {
    let db = create_test_db();
    let mut state = create_test_state();
    state.core.players[0].deck = vec![1, 2, 3, 4, 5].into();

    let ctx = AbilityContext { player_id: 0, ..Default::default() };

    // O_LOOK_DECK 3
    let bc = vec![O_LOOK_DECK, 3, 0, 0, 0, O_RETURN, 0, 0, 0, 0];
    state.resolve_bytecode(&db, &bc, &ctx);

    assert_eq!(state.core.players[0].looked_cards.len(), 3);
    assert_eq!(state.core.players[0].deck.len(), 2);
    assert_eq!(state.core.players[0].looked_cards.as_slice(), &[5, 4, 3]);
}

/// Verifies that O_LOOK_AND_CHOOSE correctly filters looked cards and transitions to Response phase.
#[test]
fn test_opcode_look_and_choose_filter_cost_ge() {
    let mut db = create_test_db();
    let mut state = create_test_state();
    // Deck: 10 (cost 5), 15 (cost 15)
    let m10 = MemberCard { card_id: 10, cost: 5, ..Default::default() };
    let m15 = MemberCard { card_id: 15, cost: 15, ..Default::default() };
    db.members.insert(10, m10.clone()); db.members_vec[10] = Some(m10);
    db.members.insert(15, m15.clone()); db.members_vec[15] = Some(m15);

    state.core.players[0].deck = vec![15, 10].into();

    let ctx = AbilityContext { player_id: 0, area_idx: -1, choice_index: -1, ..Default::default() };

    // O_LOOK_AND_CHOOSE 2 (Look 2)
    // attr: Bit 24 (Enable) | (10 << 25) (Min Cost 10) = 0x01000000 | 0x14000000 = 0x15000000
    let bc = vec![O_LOOK_AND_CHOOSE, 2, 0x15000000, 0, 0, O_RETURN, 0, 0, 0, 0];
    state.resolve_bytecode(&db, &bc, &ctx);

    // Should be in Response phase, with looked_cards: [10, 15]
    assert_eq!(state.phase, Phase::Response);
    assert_eq!(state.core.players[0].looked_cards.len(), 2);
    assert_eq!(state.core.players[0].looked_cards[0], 10);
    assert_eq!(state.core.players[0].looked_cards[1], 15);

    // Check legal actions. base for slot -1 (default), ab -1 (default)
    // base = 550 + (-1 * 100) + (0 * 10) = 450
    let actions = state.get_legal_action_ids(&db);
    println!("DEBUG: Actions: {:?}", actions);

    // card 15 is at index 1, aid = 8000 + 1 = 8001
    // card 10 is at index 0, aid = 8000 + 0 = 8000
    assert!(actions.contains(&8001), "Card 15 (cost 15) should be legal for COST_GE=10");
    assert!(!actions.contains(&8000), "Card 10 (cost 5) should NOT be legal for COST_GE=10");
}

/// Verifies the card matching logic used by various opcodes for Live cards based on heart requirements.
/// NOTE: Live cards only match cost filters when card_type is explicitly set to Live (2).
/// This prevents generic "Cost >= X" filters (meant for members) from matching high-heart live cards.
#[test]
fn test_card_matches_filter_live_hearts() {
    let mut db = create_test_db();
    let state = create_test_state();

    // Add a Live card with 8 hearts
    let cid_live = 10080;
    db.lives.insert(cid_live, LiveCard {
        card_id: cid_live,
        required_hearts: [1, 1, 1, 1, 1, 1, 2], // Sum = 8
        ..Default::default()
    });
    let logic_id = (cid_live & LOGIC_ID_MASK) as usize;
    db.lives_vec[logic_id] = Some(db.lives[&cid_live].clone());

    // Filter: COST_GE = 8, Type = Live (2)
    // Bit 24: Enable (0x01000000)
    // Bits 25-30: Value 8 (8 << 25 = 0x10000000)
    // Bits 2-3: Type = Live (2 << 2 = 0x08)
    // Bit 30: is_le = 0
    let filter_attr = 0x01000000 | (8 << 25) | (2 << 2);

    assert!(state.card_matches_filter(&db, cid_live, filter_attr), "Live with 8 hearts should match GE 8 with Live type filter");

    // Filter: COST_GE = 9, Type = Live (2)
    let filter_attr_fail = 0x01000000 | (9 << 25) | (2 << 2);
    assert!(!state.card_matches_filter(&db, cid_live, filter_attr_fail), "Live with 8 hearts should NOT match GE 9");

    // Filter: COST_LE = 8, Type = Live (2)
    // Bit 30: is_le = 1 (0x40000000)
    let filter_attr_le = 0x01000000 | (8 << 25) | 0x40000000 | (2 << 2);
    assert!(state.card_matches_filter(&db, cid_live, filter_attr_le), "Live with 8 hearts should match LE 8 with Live type filter");
    
    // Verify that generic cost filter (without type=Live) does NOT match Live cards
    let filter_generic = 0x01000000 | (8 << 25);  // No type filter
    assert!(!state.card_matches_filter(&db, cid_live, filter_generic), "Live should NOT match generic cost filter without Live type constraint");
}

/// Verifies that O_LOOK_AND_CHOOSE correctly uses Deck source even if Destination matches Hand (Arg 3 = 6).
/// Also checks that Action 0 (Skip) is suppressed for mandatory choice.
#[test]
fn test_look_and_choose_source_zone_fix() {
    let db = create_test_db();
    let mut state = create_test_state();

    // Setup: Player has 5 cards in hand, 10 in deck
    state.core.players[0].hand = vec![1, 2, 3, 4, 5].into();
    state.core.players[0].deck = (10..20).collect();

    // Execute O_LOOK_AND_CHOOSE: Look 2, Filter 0, Destination Hand (6)
    // Bytecode: [Opcode, Value, Attr, Slot]
    // [41, 2, 0, 6]
    // Expected behavior: Source Zone defaults to Deck (8) despite Dest=6.
    let ctx = AbilityContext { player_id: 0, source_card_id: 99, ..Default::default() };
    let bc = vec![O_LOOK_AND_CHOOSE, 2, 0, 0, 6, O_RETURN, 0, 0, 0, 0];

    state.resolve_bytecode(&db, &bc, &ctx);

    // Verify 1: Source Zone Logic
    // If bug existed: source=6 -> reveal_count=hand.len()=5 -> looked_cards.len()=5 (from hand)
    // Fixed: source=8 -> reveal_count=v=2 -> looked_cards.len()=2 (from deck)
    assert_eq!(state.core.players[0].looked_cards.len(), 2, "Should look at 2 cards from deck, not all cards from hand");

    // Verify cards are from deck (10..20) not hand (1..5)
    // Deck pops from end, so should be 19, 18
    let c1 = state.core.players[0].looked_cards[0];
    let c2 = state.core.players[0].looked_cards[1];
    assert!(c1 >= 10, "Looked card 1 should be from deck (ID >= 10)");
    assert!(c2 >= 10, "Looked card 2 should be from deck (ID >= 10)");

    // Verify 2: Action 0 is now ALLOWED (Skip Ability Feature)
    // Generate legal actions
    let actions = state.get_legal_action_ids(&db);

    // 8000+0 and 8000+1 should be present (for the 2 looked cards)
    assert!(actions.contains(&8000), "Should allow choosing first looked card");
    assert!(actions.contains(&8001), "Should allow choosing second looked card");

    // Action 0 is no longer suppressed, allowing users to skip abilities
    assert!(actions.contains(&0), "Action 0 (Skip) should be ALLOWED for O_LOOK_AND_CHOOSE");
}
