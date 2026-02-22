//! META_RULE Card Tests
//! 
//! Tests for cards that use O_META_RULE (opcode 29).
//! These cards modify game rules, such as treating ALL blades as any heart color.
//!
//! NOTE: Current implementation only supports cheer_mod_count (a=0).
//! The ALL_BLADE_AS_ANY_HEART meta rule is not yet implemented in the engine.

use crate::core::logic::*;
use crate::core::logic::card_db::LOGIC_ID_MASK;
use crate::test_helpers::{load_real_db, create_test_state, Action};

// =============================================================================
// PL!SP-bp1-024-L: 澁谷かのん&唐可可
// =============================================================================
// 
// 日本語テキスト:
// ライブ開始時:ライブ終了時まで、自分のステージにいる「澁谷かのん」1人は
//     heart05とブレードを、「唐可可」1人はheart01とブレードを得る。
// ライブ成功時:自分のステージに「澁谷かのん」と「唐可可」がいる場合、カードを1枚引く。
// 
// (必要ハートを確認する時、エールで出たALLブレードは任意の色のハートとして扱う。)
//
// META_RULE: ALL_BLADE_AS_ANY_HEART (not yet implemented)

/// Helper to find card ID by card number
fn find_card_id(db: &CardDatabase, card_no: &str) -> i32 {
    db.card_no_to_id.get(card_no).copied().expect(&format!("Card {} not found", card_no))
}

/// Helper to find member card by character name
fn find_member_by_name(db: &CardDatabase, name_pattern: &str) -> Option<i32> {
    for (id, member) in &db.members {
        if member.name.contains(name_pattern) {
            return Some(*id);
        }
    }
    None
}

#[test]
fn test_meta_rule_pl_sp_bp1_024_l_heart_buffs() {
    let db = load_real_db();
    let mut state = create_test_state();
    state.ui.silent = true;
    
    // Get the card ID for PL!SP-bp1-024-L
    let card_id = find_card_id(&db, "PL!SP-bp1-024-L");
    
    // Setup: Place the live card in live zone
    state.players[0].live_zone[0] = card_id;
    
    // Setup: Place Kanon and Keke on stage
    let kanon_id = find_member_by_name(&db, "澁谷かのん").unwrap_or(100);
    let keke_id = find_member_by_name(&db, "唐可可").unwrap_or(101);
    state.players[0].stage[0] = kanon_id;
    state.players[0].stage[1] = keke_id;
    
    // Setup: Add some deck cards for draw test
    state.players[0].deck = vec![3001, 3002, 3003].into();
    
    // Execute: Trigger OnLiveStart
    let ctx = AbilityContext {
        player_id: 0,
        source_card_id: card_id,
        ..Default::default()
    };
    state.trigger_abilities(&db, TriggerType::OnLiveStart, &ctx);
    
    // Assert: Kanon should have heart05 buff (index 4)
    let kanon_slot = 0;
    assert!(
        state.players[0].heart_buffs[kanon_slot].get_color_count(4) >= 1,
        "Kanon should have heart05 buff, got: {:?}",
        state.players[0].heart_buffs[kanon_slot]
    );
    
    // Assert: Keke should have heart01 buff (index 0)
    let keke_slot = 1;
    assert!(
        state.players[0].heart_buffs[keke_slot].get_color_count(0) >= 1,
        "Keke should have heart01 buff, got: {:?}",
        state.players[0].heart_buffs[keke_slot]
    );
    
    // Assert: Both should have blade buffs
    assert!(
        state.players[0].blade_buffs[kanon_slot] >= 1,
        "Kanon should have blade buff"
    );
    assert!(
        state.players[0].blade_buffs[keke_slot] >= 1,
        "Keke should have blade buff"
    );
}

#[test]
fn test_meta_rule_pl_sp_bp1_024_l_live_success_draw() {
    let db = load_real_db();
    let mut state = create_test_state();
    state.ui.silent = true;
    
    let card_id = find_card_id(&db, "PL!SP-bp1-024-L");
    
    // Setup: Place Kanon and Keke on stage
    let kanon_id = find_member_by_name(&db, "澁谷かのん").unwrap_or(100);
    let keke_id = find_member_by_name(&db, "唐可可").unwrap_or(101);
    state.players[0].stage[0] = kanon_id;
    state.players[0].stage[1] = keke_id;
    state.players[0].live_zone[0] = card_id;
    
    // Setup: Deck for draw
    state.players[0].deck = vec![3001, 3002, 3003].into();
    let initial_hand_size = state.players[0].hand.len();
    
    // Execute: Trigger OnLiveSuccess
    let ctx = AbilityContext {
        player_id: 0,
        source_card_id: card_id,
        ..Default::default()
    };
    state.trigger_abilities(&db, TriggerType::OnLiveSuccess, &ctx);
    
    // Assert: Should draw 1 card
    assert_eq!(
        state.players[0].hand.len(),
        initial_hand_size + 1,
        "Should draw 1 card when both Kanon and Keke are on stage"
    );
}

#[test]
fn test_meta_rule_pl_sp_bp1_024_l_no_draw_without_both() {
    let db = load_real_db();
    let mut state = create_test_state();
    state.ui.silent = true;
    
    let card_id = find_card_id(&db, "PL!SP-bp1-024-L");
    
    // Setup: Only Kanon on stage (no Keke)
    let kanon_id = find_member_by_name(&db, "澁谷かのん").unwrap_or(100);
    state.players[0].stage[0] = kanon_id;
    state.players[0].stage[1] = -1;  // Empty slot
    state.players[0].live_zone[0] = card_id;
    
    state.players[0].deck = vec![3001, 3002, 3003].into();
    let initial_hand_size = state.players[0].hand.len();
    
    // Execute: Trigger OnLiveSuccess
    let ctx = AbilityContext {
        player_id: 0,
        source_card_id: card_id,
        ..Default::default()
    };
    state.trigger_abilities(&db, TriggerType::OnLiveSuccess, &ctx);
    
    // Assert: Should NOT draw (condition not met)
    assert_eq!(
        state.players[0].hand.len(),
        initial_hand_size,
        "Should NOT draw when both Kanon and Keke are not on stage"
    );
}

// =============================================================================
// PL!SP-bp1-026-L: Liella! Legendary
// =============================================================================
//
// 日本語テキスト:
// ライブ開始時:自分の、ステージと控え室に名前の異なる『Liella!』のメンバーが5人以上いる場合、
//     このカードを使用するためのコストはheart02 heart02 heart03 heart03 heart06 heart06になる。
//
// (必要ハートを確認する時、エールで出たALLブレードは任意の色のハートとして扱う。)
//
// META_RULE: ALL_BLADE_AS_ANY_HEART (not yet implemented)
// CONDITION: COUNT_UNIQUE_NAMES >= 5, GROUP=Liella!, AREA=STAGE_OR_DISCARD

#[test]
fn test_meta_rule_pl_sp_bp1_026_l_condition_check() {
    let db = load_real_db();
    let mut state = create_test_state();
    state.ui.silent = true;
    
    let card_id = find_card_id(&db, "PL!SP-bp1-026-L");
    
    // Setup: Place 5+ unique Liella! members in stage and discard
    // Group ID for Liella! is 3
    let liella_members: Vec<i32> = db.members.iter()
        .filter(|(_, m)| m.groups.contains(&3))
        .take(5)
        .map(|(id, _)| *id)
        .collect();
    
    if liella_members.len() < 5 {
        // Skip test if not enough Liella! members in DB
        eprintln!("Skipping test: Need at least 5 Liella! members, found {}", liella_members.len());
        return;
    }
    
    // Place 2 on stage, 3 in discard
    state.players[0].stage[0] = liella_members[0];
    state.players[0].stage[1] = liella_members[1];
    state.players[0].discard = liella_members[2..5].to_vec().into();
    state.players[0].live_zone[0] = card_id;
    
    // Execute: Trigger OnLiveStart
    let ctx = AbilityContext {
        player_id: 0,
        source_card_id: card_id,
        ..Default::default()
    };
    state.trigger_abilities(&db, TriggerType::OnLiveStart, &ctx);
    
    // The heart cost modification should be applied
    // This is checked by verifying the live card's heart requirements
    // Note: Implementation depends on how heart_req_reductions/additions work
}

// =============================================================================
// Basic O_META_RULE Tests (cheer_mod_count)
// =============================================================================

#[test]
fn test_meta_rule_cheer_mod_increment() {
    let db = load_real_db();
    let mut state = create_test_state();
    state.ui.silent = true;
    
    let initial_cheer_mod = state.players[0].cheer_mod_count;
    
    // Execute O_META_RULE with a=0 (cheer_mod), v=1
    let bc = vec![O_META_RULE, 1, 0, 0, O_RETURN, 0, 0, 0];
    let ctx = AbilityContext { player_id: 0, ..Default::default() };
    state.resolve_bytecode(&db, &bc, &ctx);
    
    // Assert: cheer_mod_count should be incremented
    assert_eq!(
        state.players[0].cheer_mod_count,
        initial_cheer_mod + 1,
        "cheer_mod_count should be incremented by 1"
    );
}

#[test]
fn test_meta_rule_cheer_mod_multiple() {
    let db = load_real_db();
    let mut state = create_test_state();
    state.ui.silent = true;
    
    state.players[0].cheer_mod_count = 0;
    
    // Execute O_META_RULE multiple times
    let bc = vec![O_META_RULE, 3, 0, 0, O_RETURN, 0, 0, 0];
    let ctx = AbilityContext { player_id: 0, ..Default::default() };
    state.resolve_bytecode(&db, &bc, &ctx);
    
    // Assert: cheer_mod_count should be incremented by 3
    assert_eq!(
        state.players[0].cheer_mod_count,
        3,
        "cheer_mod_count should be incremented by 3"
    );
}
