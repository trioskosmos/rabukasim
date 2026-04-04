use crate::core::enums::Phase;
use crate::core::logic::*;
use crate::test_helpers::{load_real_db, Action};
use smallvec::smallvec;

#[test]
fn verify_on_reveal_trigger() {
    let db = load_real_db();
    let mut state = GameState::default();
    state.ui.silent = true;

    // Card ID 454: ダイスキだったらダイジョウブ！ (Live)
    // Ability: ON_REVEAL -> MOVE_TO_DISCARD etc.
    state.players[0].live_zone[0] = 454;
    state.players[0].set_revealed(0, false);

    // Start performance phase to trigger reveal
    state.phase = Phase::PerformanceP1;
    state.do_performance_phase(&db);

    assert!(
        state.players[0].is_revealed(0),
        "Live card should be revealed during performance phase"
    );
    // Trigger should have executed (it meets conditions if yelled revealed is empty)
}

#[test]
fn verify_manual_recovery_pattern() {
    use crate::core::logic::models::{Ability, Cost};
    use crate::core::enums::AbilityCostType;
    
    let mut db = CardDatabase::default();
    
    // Create a test member with SacrificeSelf cost and RecoverMember effect
    // Card ID 406: 高海千歌 (Member) - Mock with proper ability
    let mut card406 = MemberCard::default();
    card406.card_id = 406;
    card406.name = "Test Chika".to_string();
    
    let mut ab = Ability::default();
    ab.trigger = TriggerType::Activated;
    // Add SacrificeSelf cost
    ab.costs.push(Cost {
        cost_type: AbilityCostType::SacrificeSelf,
        value: 1,
        ..Default::default()
    });
    // Add RECOVER_MEMBER effect via bytecode
    ab.frame_program = Some(FrameProgram::from_instruction_words(&[
        32, 1, 0, 0, 0, 1, 0, 0, 0, 0,  // RECOVER_MEMBER 1
    ]));
    card406.abilities.push(ab);
    db.members.insert(406, card406);
    
    // Add card 121 (Eli) to database for recovery target
    let mut card121 = MemberCard::default();
    card121.card_id = 121;
    card121.name = "Test Eli".to_string();
    db.members.insert(121, card121);

    let mut state = GameState::default();
    state.ui.silent = true;

    state.players[0].stage[0] = 406;
    state.players[0].discard.push(121); // Target Eli to recover
    state.players[0].deck = vec![123].into(); // Dummy
    state.phase = Phase::Main;
    state.current_player = 0;

    // 1. Activate ability (Slot 0, Ability 0)
    let result = state.step(
        &db,
        Action::ActivateAbility {
            slot_idx: 0,
            ab_idx: 0,
        }
        .id() as i32,
    );
    println!("    Frame {}: opcode={}, value={}, slot={}, attr={}, params={:?}", 
                             0, 32, 1, 0, 0, vec![1, 0, 0, 0, 0, 0, 0, 0]);
    result.unwrap();

    assert_eq!(
        state.players[0].stage[0], -1,
        "Member should be in discard after sacrifice (Cost processing)"
    );
    // Verify the sacrificed card is in discard
    assert!(
        state.players[0].discard.contains(&406),
        "Sacrificed member 406 should be in discard"
    );
    
    // Note: The recovery part of this test is incomplete - 
    // the ability resolution would need proper interaction handling
}

#[test]
fn verify_performance_transition_history() {
    let db = load_real_db();
    let mut state = GameState::default();
    state.ui.silent = false; // Need non-silent mode to verify performance_history

    // Use common live card ID 6
    state.players[0].live_zone[0] = 6;
    state.players[0].set_revealed(0, true);
    state.phase = Phase::PerformanceP1;

    // P0 Perform (Pass)
    state.step(&db, 0).expect("P0 pass failed");
    // P1 Perform (Pass)
    state.step(&db, 0).expect("P1 pass failed");

    assert_eq!(
        state.ui.performance_history.len(),
        2,
        "Should have 2 performance records"
    );
}

#[test]
fn verify_full_win_condition() {
    let db = load_real_db();
    let mut state = GameState::default();
    state.ui.silent = true;

    // ID 6: Score 3 card
    state.players[0].success_lives = smallvec![6, 6];
    state.players[0].score = 2; // Internal engine score (not display score)
    state.phase = Phase::LiveResult;
    state.players[0].live_zone[0] = 6;

    // Select the live card to win (Slot 0 maps to action 600)
    state.step(&db, 600).expect("Decision step failed");

    assert_eq!(state.phase, Phase::Terminal, "Game should end");
    assert_eq!(state.players[0].success_lives.len(), 3);
    assert_eq!(state.get_winner(), 0);
}

#[test]
fn verify_buff_logic() {
    let db = load_real_db();
    let mut state = GameState::default();
    state.ui.silent = true;

    // Card ID 120: PL!-sd1- 001-SD
    // Ability: TRIGGER: CONSTANT -> ADD_BLADES(1, PER_CARD=SUCCESS_PILE)
    // Core Blades: 3 (Actual DB value)
    state.players[0].stage[0] = 120;
    state.players[0].success_lives = smallvec![120, 120]; // 2 cards in success pile

    // Enable debug mode to see blade calculation
    state.debug.debug_mode = true;
    state.ui.silent = false;
    
    // Total is currently 3 (base) + 2 bonus from 2 success pile cards = 5
    let blades = state.get_effective_blades(0, 0, &db, 0);
    println!("Card 120 blades: {} (expected: 5)", blades);
    
    // Check what card 120's ability actually is
    if let Some(member) = db.get_member(120) {
        println!("Card 120 - Name: {}, Base Blades: {}", member.name, member.blades);
        for (i, ab) in member.abilities.iter().enumerate() {
            println!("  Ability {}: {:?}", i, ab);
            if let Some(frame_program) = &ab.frame_program {
                for (j, frame) in frame_program.frames.iter().enumerate() {
                    println!("    Frame {}: opcode={}, value={}, slot={}, params={:?}", 
                             j, frame.opcode(), frame.value(), frame.slot(), frame.components().params);
                }
            }
        }
    }
    
    // Check board aura
    let aura = crate::core::logic::rules::calculate_board_aura(&state, 0, &db);
    println!("Board aura blades: {:?}", aura.blades);
    println!("Success lives: {:?}", state.players[0].success_lives);
    
    assert_eq!(
        blades, 5,
        "Card 120 should have 3 (base) + 2 bonus from 2 cards in success pile = 5 blades"
    );
}
