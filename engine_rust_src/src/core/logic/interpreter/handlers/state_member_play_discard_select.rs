use super::*;
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;

fn suspend_discard_prompt(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &AbilityContext,
    frame_idx: usize,
    target_p_idx: usize,
    filter_attr: u64,
    remaining: i16,
    s: i32,
) -> HandlerResult {
    let mut target_ctx = ctx.clone();
    target_ctx.player_id = target_p_idx as u8;
    target_ctx.v_remaining = remaining;
    target_ctx.v_accumulated = ctx.v_accumulated;
    target_ctx.choice_index = -1;
    if matches!(
        suspend_choice(
            state,
            db,
            &target_ctx,
            &target_ctx,
            frame_idx,
            O_PLAY_MEMBER_FROM_DISCARD,
            s,
            ChoiceType::SelectDiscardPlay,
            filter_attr,
            remaining,
        ),
        HandlerResult::Suspend
    ) {
        HandlerResult::Suspend
    } else {
        HandlerResult::Continue
    }
}

#[allow(clippy::too_many_arguments)]
pub fn handle_discard_selection(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_idx: usize,
    target_p_idx: usize,
    filter_attr_base: u64,
    _empty_slot_only: bool,
    _baton_slot_only: bool,
    is_total_cost: bool,
    remaining: i16,
    s: i32,
) -> HandlerResult {
    let has_legal_slot = (0..3).any(|slot_idx| {
        super::discard_play_slot_is_legal(&state.players[target_p_idx], slot_idx, s)
    });
    if !has_legal_slot {
        super::clear_discard_play_buffer(state, target_p_idx);
        return HandlerResult::Continue;
    }

    let filter_attr_base = filter_attr_base & !crate::core::logic::filter::FILTER_STATE_FLAGS_MASK;

    if ctx.choice_index == -1 && ctx.v_remaining == -1 {
        state.players[target_p_idx].looked_cards.clear();
    }

    if state.players[target_p_idx].looked_cards.is_empty() {
        ctx.choice_index = -1;

        let mut filter_attr = filter_attr_base;
        if is_total_cost {
            filter_attr |= 1u64 << 60;
        }
        let mut filter_ctx = ctx.clone();
        filter_ctx.player_id = target_p_idx as u8;
        filter_ctx.v_remaining = remaining;
        filter_ctx.v_accumulated = ctx.v_accumulated;
        let matched_ids: Vec<i32> = state.players[target_p_idx]
            .discard
            .iter()
            .filter_map(|&cid| {
                let member = db.get_member(cid)?;
                let cost_ok = if is_total_cost {
                    member.cost as i16 <= remaining
                } else {
                    // For count-based play, each card uses 2 steps (select card + select slot).
                    // We only need to know that a candidate exists here; the state machine
                    // handles the exact step accounting in the placement phase.
                    true
                };

                if cost_ok
                    && !ctx.selected_cards.contains(&cid)
                    && (filter_attr == 0
                        || state.card_matches_filter_with_ctx(db, cid, filter_attr, &filter_ctx))
                {
                    Some(cid)
                } else {
                    None
                }
            })
            .collect();
        state.players[target_p_idx].looked_cards.extend(matched_ids);
        if state.players[target_p_idx].looked_cards.is_empty() {
            super::clear_discard_play_buffer(state, target_p_idx);
            return HandlerResult::Continue;
        }

        return suspend_discard_prompt(
            state,
            db,
            &filter_ctx,
            frame_idx,
            target_p_idx,
            filter_attr,
            remaining,
            s,
        );
    }

    if ctx.choice_index == -1 {
        let mut filter_attr = filter_attr_base;
        if is_total_cost {
            filter_attr |= 1u64 << 60;
        }
        return suspend_discard_prompt(
            state,
            db,
            ctx,
            frame_idx,
            target_p_idx,
            filter_attr,
            remaining,
            s,
        );
    }

    let idx = ctx.choice_index as usize;
    let cards_len = state.players[target_p_idx].looked_cards.len();

    // Handle CHOICE_DONE (99) - user wants to stop selecting cards
    if ctx.choice_index == crate::core::logic::constants::CHOICE_DONE {
        super::clear_discard_play_buffer(state, target_p_idx);
        ctx.v_remaining = 0;
        return HandlerResult::Continue;
    }

    if idx < cards_len {
        let cid = state.players[target_p_idx].looked_cards[idx];
        state.players[target_p_idx].looked_cards.remove(idx);

        let selected_cost = db
            .get_member(cid)
            .map(|member| member.cost as i16)
            .unwrap_or(0);
        let next_remaining = if is_total_cost {
            remaining.saturating_sub(selected_cost)
        } else {
            remaining.saturating_sub(1)
        };
        ctx.v_remaining = next_remaining;
        let mut target_ctx = ctx.clone();
        target_ctx.player_id = target_p_idx as u8;
        target_ctx.v_remaining = next_remaining;
        target_ctx.v_accumulated = ctx.v_accumulated;
        target_ctx.selected_cards = ctx.selected_cards.clone();
        if !target_ctx.selected_cards.contains(&cid) {
            target_ctx.selected_cards.push(cid);
        }
        if !ctx.selected_cards.contains(&cid) {
            ctx.selected_cards.push(cid);
        }
        target_ctx.choice_index = -1;
        ctx.choice_index = -1;
        ctx.target_card_id = cid;
        target_ctx.target_card_id = cid;
        if let Some(top) = state.interaction_stack.last_mut() {
            top.ctx.selected_cards = target_ctx.selected_cards.clone();
            top.ctx.target_card_id = cid;
        }

        let choice_type = super::discard_play_choice_type(s);
        if matches!(
            suspend_choice(
                state,
                db,
                &target_ctx,
                &target_ctx,
                frame_idx,
                O_PLAY_MEMBER_FROM_DISCARD,
                s,
                choice_type,
                filter_attr_base,
                next_remaining,
            ),
            HandlerResult::Suspend
        ) {
            return HandlerResult::Suspend;
        }
    }

    HandlerResult::Continue
}
