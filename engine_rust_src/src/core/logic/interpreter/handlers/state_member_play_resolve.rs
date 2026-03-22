use super::*;

#[allow(clippy::too_many_arguments)]
pub fn finalize_play_member_from_hand(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    p_idx: usize,
    h_idx: usize,
    slot_idx: usize,
) -> HandlerResult {
    if h_idx >= state.players[p_idx].hand.len() || slot_idx >= 3 {
        return HandlerResult::Continue;
    }

    let Some(cid) = state.players[p_idx].remove_hand_card(h_idx) else {
        return HandlerResult::Continue;
    };

    if let Some(old) = state.handle_member_leaves_stage(p_idx, slot_idx, db, ctx) {
        state.players[p_idx].push_discard_card(old);
    }
    state.players[p_idx].stage[slot_idx] = cid;
    state.players[p_idx].set_tapped(slot_idx, false);
    state.players[p_idx].set_moved(slot_idx, true);
    state.register_played_member(p_idx, cid, db);

    let new_ctx = AbilityContext {
        source_card_id: cid,
        player_id: p_idx as u8,
        activator_id: p_idx as u8,
        area_idx: slot_idx as i16,
        ..Default::default()
    };
    state.trigger_abilities(db, TriggerType::OnPlay, &new_ctx);
    ctx.choice_index = -1;
    ctx.v_remaining = 0;
    HandlerResult::Continue
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
) -> HandlerResult {
    if slot_idx >= 3 {
        return HandlerResult::Continue;
    }
    if (state.players[target_p_idx].prevent_play_to_slot_mask & (1 << slot_idx)) != 0
        || (empty_slot_only && state.players[target_p_idx].stage[slot_idx] != -1)
    {
        return HandlerResult::Continue;
    }

    if is_total_cost {
        if let Some(m) = db.get_member(card_id) {
            ctx.v_accumulated = (ctx.v_accumulated - m.cost as i16).max(0);
        }
    }

    if let Some(pos) = state.players[target_p_idx]
        .discard
        .iter()
        .position(|&cid| cid == card_id)
    {
        let pos = pos as usize;
        state.players[target_p_idx].remove_discard_card(pos);
        if let Some(old) = state.handle_member_leaves_stage(target_p_idx, slot_idx, db, ctx) {
            state.players[target_p_idx].push_discard_card(old);
        }
        state.players[target_p_idx].stage[slot_idx] = card_id;
        state.players[target_p_idx].set_tapped(slot_idx, true);
        state.players[target_p_idx].set_moved(slot_idx, true);
        state.register_played_member(target_p_idx, card_id, db);
        state.players[target_p_idx].prevent_play_to_slot_mask |= 1 << slot_idx;


    }

    HandlerResult::Continue
}

