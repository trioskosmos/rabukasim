use super::*;

/// Create new context for OnPlay trigger with proper phase inheritance
fn create_on_play_context(
    state: &GameState,
    ctx: &AbilityContext,
    p_idx: usize,
    card_id: i32,
    slot_idx: usize,
) -> AbilityContext {
    // Q201/Q202 Fix: Preserve original_phase for nested play phase suspension
    // When playing a member via effect, nested OnPlay trigger should inherit
    // parent's original_phase to maintain Response phase if already in Response
    let inherited_original_phase = ctx.original_phase.or_else(|| {
        // If parent doesn't have original_phase but we're in Response, capture current state
        if state.phase == Phase::Response {
            Some(Phase::Response)
        } else {
            None
        }
    });
    
    let inherited_original_player = ctx.original_current_player.or(Some(state.current_player));
    
    AbilityContext {
        source_card_id: card_id,
        player_id: p_idx as u8,
        activator_id: ctx.activator_id,
        area_idx: slot_idx as i16,
        target_slot: slot_idx as i16,
        choice_index: -1,
        trigger_type: TriggerType::OnPlay,
        original_phase: inherited_original_phase,
        original_current_player: inherited_original_player,
        ..Default::default()
    }
}

fn finish_member_play(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    p_idx: usize,
    card_id: i32,
    slot_idx: usize,
    tapped: bool,
) -> HandlerResult {
    // Handle member leaving stage and moving to discard
    if let Some(old) = state.handle_member_leaves_stage(p_idx, slot_idx, db, ctx) {
        state.players[p_idx].push_discard_card(old);
    }
    
    // Update stage state
    state.players[p_idx].set_stage_card(slot_idx, card_id);
    state.players[p_idx].set_tapped(slot_idx, tapped);
    state.players[p_idx].set_moved(slot_idx, true);
    state.sync_player_stats(db, p_idx);
    state.register_played_member(p_idx, card_id, db);
    
    // Create context for OnPlay triggers
    let new_ctx = create_on_play_context(state, ctx, p_idx, card_id, slot_idx);

    if !state.ui.silent {
        state.log(format!(
            "Rule 11.3, Rule 11.3.1, Rule 11.3.2: Broadcasting [騾具ｽｻ陜｣・ｴ] (On Play) triggers for card {}.",
            card_id
        ));
    }

    state.trigger_abilities(db, TriggerType::OnPlay, &new_ctx);
    if !state.trigger_queue.is_empty() {
        state.process_trigger_queue(db);
    }
    if !state.interaction_stack.is_empty() {
        ctx.choice_index = -1;
        ctx.v_remaining = 0;
        return HandlerResult::Suspend;
    }

    ctx.choice_index = -1;
    ctx.v_remaining = 0;
    HandlerResult::Continue
}

#[allow(clippy::too_many_arguments)]
pub fn finalize_play_member_from_hand(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    p_idx: usize,
    h_idx: usize,
    slot_idx: usize,
) -> HandlerResult {
    if slot_idx >= 3 || state.players[p_idx].is_moved(slot_idx) {
        return HandlerResult::Continue;
    }

    if ctx.target_card_id < 0 {
        return HandlerResult::Continue;
    }

    let resolved_idx = if let Some(&card_id) = state.players[p_idx].hand.get(h_idx) {
        if card_id == ctx.target_card_id {
            Some(h_idx)
        } else {
            None
        }
    } else {
        None
    }
    .or_else(|| {
        state.players[p_idx]
            .hand
            .iter()
            .position(|&card_id| card_id == ctx.target_card_id)
    });

    let Some(hand_idx) = resolved_idx else {
        return HandlerResult::Continue;
    };

    let Some(card_id) = state.players[p_idx].remove_hand_card(hand_idx) else {
        return HandlerResult::Continue;
    };

    finish_member_play(state, db, ctx, p_idx, card_id, slot_idx, false)
}

#[allow(clippy::too_many_arguments)]
pub fn finalize_play_member_from_discard(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    target_p_idx: usize,
    card_id: i32,
    slot_idx: usize,
    empty_slot_only: bool,
    is_total_cost: bool,
    enters_tapped: bool,
) -> HandlerResult {
    if slot_idx >= 3 {
        return HandlerResult::Continue;
    }
    if (state.players[target_p_idx].prevent_play_to_slot_mask() & (1 << slot_idx)) != 0
        || (empty_slot_only && state.players[target_p_idx].stage[slot_idx] != -1)
    {
        return HandlerResult::Continue;
    }

    if is_total_cost {
        if let Some(m) = db.get_member(card_id) {
            ctx.v_accumulated = (ctx.v_accumulated - m.cost as i16).max(0);
        }
    }

    let Some(pos) = state.players[target_p_idx]
        .discard
        .iter()
        .position(|&cid| cid == card_id)
    else {
        ctx.choice_index = -1;
        ctx.v_remaining = 0;
        return HandlerResult::Continue;
    };

    state.players[target_p_idx].remove_discard_card(pos);
    ctx.repeat_count = ctx.repeat_count.saturating_sub(1);
    let mask = state.players[target_p_idx].prevent_play_to_slot_mask();
    state.players[target_p_idx].set_prevent_play_to_slot_mask(mask | (1 << slot_idx) as u8);

    finish_member_play(state, db, ctx, target_p_idx, card_id, slot_idx, enters_tapped)
}
