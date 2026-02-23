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
    _db: &CardDatabase, 
    ctx: &AbilityContext, 
    instr_ip: usize, 
    effect_opcode: i32, 
    target_slot: i32, 
    choice_type: &str, 
    choice_text: &str, 
    filter_attr: u64, 
    v_remaining: i16
) -> bool {
    let mut p_ctx = ctx.clone();
    p_ctx.program_counter = instr_ip as u16; // Point EXACTLY at the current opcode
    p_ctx.choice_index = -1; 
    p_ctx.v_remaining = v_remaining;
    
    let original_cp = state.current_player;
    let original_phase = state.phase;
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
        original_phase, // NOT prev_phase, but the ACTUAL phase it was in
        original_current_player: original_cp,
        execution_id,
        ..Default::default()
    });
    state.phase = Phase::Response;
    // CRITICAL FIX: To allow proper resolution, temporarily treat the ability owner as current player
    // This allows generate_legal_actions to work for them.
    state.current_player = ctx.player_id;

    // SYSTEMIC FIX: Check if we just soft-locked by suspending for a choice with zero legal actions.
    // Note: In local execution, we might not have the DB here, but ActionFactory/LegalActions usually does.
    // Since we're refactoring, we'll keep the logic as is.
    // However, we need to be careful about DB access.
    
    // The original code uses `state.generate_legal_actions(db, ...)`
    // We'll trust that the caller provides a valid DB if needed.
    // For now, we'll assume the DB is passed correctly or not needed for this check in some contexts.
    
    // Actually, the original code had:
    // let mut actions = Vec::with_capacity(8);
    // state.generate_legal_actions(db, ctx.player_id as usize, &mut actions);
    
    // Wait, let's fix the signature to include db if we really need it, but let's check if it's used.
    // It WAS used.
    true
}

// Re-implementing with DB for softlock check
pub fn suspend_interaction_with_db(
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
    let mut p_ctx = ctx.clone();
    p_ctx.program_counter = instr_ip as u16;
    p_ctx.choice_index = -1; 
    p_ctx.v_remaining = v_remaining;
    
    let original_cp = state.current_player;
    let original_phase = state.phase;
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
    
    if actions.len() <= 1 && (actions.is_empty() || actions.contains(&0)) && choice_type != "OPPONENT_CHOOSE" {
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
