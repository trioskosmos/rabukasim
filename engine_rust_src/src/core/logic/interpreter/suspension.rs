//! # Suspension and Choice Logic
//!
//! This module contains the logic for suspending execution for user input
//! and resolving target slots.

use crate::core::logic::{GameState, CardDatabase, AbilityContext, PendingInteraction, Phase};

pub fn get_choice_text(db: &CardDatabase, ctx: &AbilityContext) -> String {
    crate::core::logic::ActionFactory::get_choice_text(db, ctx)
}

pub fn suspend_interaction(
    state: &mut GameState, 
    db: &CardDatabase, 
    ctx: &AbilityContext, 
    instr_ip: usize, 
    effect_opcode: i32, 
    target_slot: i32, 
    choice_type: &str, 
    choice_text: &str, 
    filter_attr: u64, 
    v_remaining: i16
) -> bool {
    let original_phase = if let Some(p) = ctx.original_phase {
        p
    } else if state.phase == Phase::Response {
        // Fallback for cases where context didn't carry it (e.g. root activation via trigger)
        state.interaction_stack.last()
            .map(|pi| pi.original_phase)
            .unwrap_or(state.phase)
    } else {
        state.phase
    };
    
    let mut p_ctx = ctx.clone();
    p_ctx.program_counter = instr_ip as u16;
    p_ctx.choice_index = -1; 
    p_ctx.v_remaining = v_remaining;
    p_ctx.original_phase = Some(original_phase);
    
    let original_cp = state.current_player;
    let execution_id = state.ui.current_execution_id.unwrap_or(0);

    state.interaction_stack.push(PendingInteraction {
        ctx: p_ctx,
        card_id: ctx.source_card_id,
        ability_index: ctx.ability_index,
        effect_opcode,
        target_slot,
        choice_type: choice_type.to_string(),
        filter_attr,
        choice_text: choice_text.to_string(),
        v_remaining,
        original_phase,
        original_current_player: original_cp,
        execution_id,
        ..Default::default()
    });
    state.phase = Phase::Response;
    state.current_player = ctx.player_id;

    let mut actions = Vec::with_capacity(8);
    state.generate_legal_actions(db, ctx.player_id as usize, &mut actions);
    
    // Don't skip suspension for OPTIONAL, LOOK_AND_CHOOSE, COLOR_SELECT, TAP_M_SELECT, etc.
    // These are legitimate choice types that should always suspend even with limited actions.
    let always_suspend_types = ["OPTIONAL", "LOOK_AND_CHOOSE", "COLOR_SELECT", "TAP_M_SELECT", "TAP_O", "SELECT_MEMBER", "SELECT_LIVE", "SELECT_PLAYER", "RECOV_L", "RECOV_M"];
    let should_check_skip = !always_suspend_types.contains(&choice_type);
    
    if should_check_skip && actions.len() <= 1 && (actions.is_empty() || actions.contains(&0)) && choice_type != "OPPONENT_CHOOSE" {
        if state.debug.debug_mode {
            println!("[DEBUG] Softlock prevented: {} has no legal actions. Skipping suspension.", choice_type);
        }
        state.interaction_stack.pop();
        state.phase = original_phase;
        state.current_player = original_cp;
        return false;
    }
    true
}

/// Resolves the effective slot index based on the opcode's target_slot and the current context.
/// Slot 4 often acts as a proxy for the 'Area Index' stored in the context.
pub fn resolve_target_slot(target_slot: i32, ctx: &AbilityContext) -> usize {
    if target_slot == 0 && ctx.target_slot >= 0 {
        return ctx.target_slot as usize;
    }
    if target_slot == 4 && ctx.area_idx >= 0 {
        ctx.area_idx as usize
    } else if target_slot == -1 || target_slot == 4 {
        // Fallback to 0 if we expect a slot but none is provided, or if slot 4 is passed without context
        if ctx.area_idx >= 0 { ctx.area_idx as usize } else { 0 }
    } else {
        target_slot.max(0) as usize
    }
}
