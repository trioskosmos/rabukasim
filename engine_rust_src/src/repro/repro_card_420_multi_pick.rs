use crate::core::logic::*;
use crate::core::generated_constants::{O_PLAY_MEMBER_FROM_DISCARD, ACTION_BASE_CHOICE};
use crate::core::enums::Phase;
use crate::test_helpers::load_real_db;

/// Test that O_PLAY_MEMBER_FROM_DISCARD with v=2 allows picking two cards
/// through the full interaction sequence:
///   1. Populate looked_cards -> Suspend for SELECT_DISCARD_PLAY
///   2. User picks card 1 -> Suspend for SELECT_STAGE
///   3. User picks slot -> Card placed, suspend for 2nd SELECT_DISCARD_PLAY
///   4. User picks card 2 -> Suspend for SELECT_STAGE
///   5. User picks slot -> Card placed, done
#[test]
fn test_repro_card_420_multi_pick_from_discard() {
    let db = load_real_db();
    let mut state = GameState::default();
    state.ui.silent = false;
    state.debug.debug_mode = true;

    let p_idx = 0usize;
    state.current_player = p_idx as u8;
    state.phase = Phase::Main;

    // Card 420 = PL!S-bp2-006-P (津島善子)
    // Its ability 0 bytecodes: PAY_ENERGY(4, optional) then PLAY_MEMBER_FROM_DISCARD(v=2, cost_le_4)
    let card_420_id = 420;
    let card = db.get_member(card_420_id).expect("Card 420 not found in DB");
    eprintln!("Card 420: {} ({})", card.name, card.card_no);
    assert!(!card.abilities.is_empty(), "Card 420 should have abilities");

    // Find two low-cost members for the discard pile with NO abilities
    // (to prevent nested suspensions during OnPlay triggers)
    let mut discard_members: Vec<i32> = Vec::new();
    for (_card_no, &id) in db.card_no_to_id.iter() {
        if id == card_420_id { continue; }
        if let Some(m) = db.get_member(id) {
            if m.cost <= 2 && m.abilities.is_empty() && discard_members.len() < 3 {
                discard_members.push(id);
                eprintln!("  Discard candidate: {} (cost={})", m.name, m.cost);
            }
        }
        if discard_members.len() >= 3 { break; }
    }
    assert!(discard_members.len() >= 2, "Need at least 2 vanilla low-cost members in DB");

    // Setup: empty stage, members in discard, plenty of energy
    // IMPORTANT: Populate deck to prevent deck refresh (process_rule_checks triggers
    // refresh when deck is empty + discard non-empty, which would move discard to deck)
    state.core.players[p_idx].stage = [-1, -1, -1];
    state.core.players[p_idx].discard = discard_members.clone().into();
    state.core.players[p_idx].deck = vec![9999; 5].into(); // Dummy cards to prevent deck refresh
    state.core.players[p_idx].energy_zone = vec![9000; 6].into(); // 6 energy (enough for PAY_ENERGY 4)
    state.core.players[p_idx].energy_deck = vec![9000; 5].into(); // Prevent energy deck empty issues

    // Manually push the PLAY_MEMBER_FROM_DISCARD interaction to skip the PAY_ENERGY step
    // This simulates the point where the user has already paid energy and the engine
    // is now asking them to select a member from discard.
    let filter_attr = {
        // Decode from real bytecodes: a_low=1224736768, a_high=-2147483648
        let a_low = card.abilities[0].bytecode[7] as u32;
        let a_high = card.abilities[0].bytecode[8] as u32;
        ((a_high as u64) << 32) | (a_low as u64)
    };
    let s_word = card.abilities[0].bytecode[9]; // 458756
    eprintln!("filter_attr={:#018x}, s_word={}", filter_attr, s_word);

    // Populate looked_cards with eligible members from discard
    state.core.players[p_idx].looked_cards.clear();
    for &cid in &state.core.players[p_idx].discard {
        if db.get_member(cid).is_some() && (filter_attr == 0 || state.card_matches_filter(&db, cid, filter_attr)) {
            state.core.players[p_idx].looked_cards.push(cid);
        }
    }
    let initial_looked = state.core.players[p_idx].looked_cards.len();
    eprintln!("Initial looked_cards: {} members", initial_looked);
    assert!(initial_looked >= 2, "Should have at least 2 eligible members in looked_cards");

    // Push the initial SELECT_DISCARD_PLAY interaction
    let v_remaining = 4i16; // v=2, so remaining = v*2 = 4
    let ctx = AbilityContext {
        player_id: p_idx as u8,
        activator_id: p_idx as u8,
        source_card_id: card_420_id,
        ability_index: 0,
        program_counter: 10, // IP of O_PLAY_MEMBER_FROM_DISCARD in card 420's bytecodes
        v_remaining,
        v_accumulated: 4,
        choice_index: -1,
        ..Default::default()
    };
    state.interaction_stack.push(PendingInteraction {
        ctx: ctx.clone(),
        card_id: card_420_id,
        ability_index: 0,
        effect_opcode: O_PLAY_MEMBER_FROM_DISCARD,
        target_slot: 0,
        choice_type: "SELECT_DISCARD_PLAY".to_string(),
        filter_attr,
        choice_text: String::new(),
        v_remaining,
        original_phase: Phase::Main,
        original_current_player: p_idx as u8,
        execution_id: 0,
        ..Default::default()
    });
    state.phase = Phase::Response;

    eprintln!("\n=== Step 1: Pick first card (index 0) ===");
    let pick_card_0 = ACTION_BASE_CHOICE; // Choice index 0
    state.step(&db, pick_card_0).expect("Pick card 0 failed");

    // Should now be suspended for SELECT_STAGE
    assert_eq!(state.phase, Phase::Response, "Should still be in Response for stage selection");
    let pi = state.interaction_stack.last().expect("Should have pending interaction");
    eprintln!("  Pending: type={}, v_remaining={}", pi.choice_type, pi.v_remaining);
    assert!(pi.choice_type == "SELECT_STAGE" || pi.choice_type == "SELECT_STAGE_EMPTY",
        "Should be asking for stage selection, got: {}", pi.choice_type);

    eprintln!("\n=== Step 2: Pick slot 0 ===");
    let pick_slot_0 = ACTION_BASE_CHOICE; // Slot 0
    state.step(&db, pick_slot_0).expect("Pick slot 0 failed");

    // First card should be placed on slot 0
    eprintln!("  Stage after 1st placement: {:?}", state.core.players[p_idx].stage);
    assert!(state.core.players[p_idx].stage[0] >= 0, "Slot 0 should have a member after first placement");

    // Should be suspended for 2nd SELECT_DISCARD_PLAY
    eprintln!("  Phase: {:?}, interaction_stack len: {}", state.phase, state.interaction_stack.len());
    assert_eq!(state.phase, Phase::Response, "Should be in Response for 2nd card pick");
    assert!(!state.interaction_stack.is_empty(), "Should have pending interaction for 2nd card pick");

    let pi2 = state.interaction_stack.last().expect("Should have pending interaction");
    eprintln!("  Pending: type={}, v_remaining={}", pi2.choice_type, pi2.v_remaining);
    assert_eq!(pi2.choice_type, "SELECT_DISCARD_PLAY", "Should be asking for 2nd discard play");

    // CRITICAL: Verify looked_cards have been repopulated for the 2nd round
    let looked = &state.core.players[p_idx].looked_cards;
    eprintln!("  looked_cards after 1st placement: {} cards", looked.len());
    assert!(!looked.is_empty(), "looked_cards should be repopulated for 2nd card pick (BUG FIX: was empty before)");

    eprintln!("\n=== Step 3: Pick second card (index 0) ===");
    let pick_card_1 = ACTION_BASE_CHOICE;
    state.step(&db, pick_card_1).expect("Pick card 1 failed");

    // Should be suspended for SELECT_STAGE again
    assert_eq!(state.phase, Phase::Response, "Should be in Response for 2nd stage selection");

    eprintln!("\n=== Step 4: Pick slot 1 ===");
    let pick_slot_1 = ACTION_BASE_CHOICE + 1; // Slot 1
    state.step(&db, pick_slot_1).expect("Pick slot 1 failed");

    // Both cards should now be placed on stage
    eprintln!("  Stage after 2nd placement: {:?}", state.core.players[p_idx].stage);
    assert!(state.core.players[p_idx].stage[0] >= 0, "Slot 0 should have a member");
    assert!(state.core.players[p_idx].stage[1] >= 0, "Slot 1 should have a member");

    eprintln!("\n[PASS] Multi-pick PLAY_MEMBER_FROM_DISCARD(v=2) works correctly!");
}
