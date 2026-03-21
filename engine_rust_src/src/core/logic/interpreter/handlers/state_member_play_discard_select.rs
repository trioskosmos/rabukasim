use super::*;
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;

#[allow(clippy::too_many_arguments)]
pub fn handle_discard_selection(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    instr_ip: usize,
    target_p_idx: usize,
    filter_attr_base: u64,
    empty_slot_only: bool,
    baton_slot_only: bool,
    is_total_cost: bool,
    remaining: i16,
    s: i32,
) -> HandlerResult {
    if empty_slot_only && state.players[target_p_idx].stage.iter().all(|&c| c >= 0) {
        return HandlerResult::Continue;
    }

    let filter_attr_base = filter_attr_base & !crate::core::logic::filter::FILTER_STATE_FLAGS_MASK;

    if ctx.choice_index == -1 {
        state.players[target_p_idx].looked_cards.clear();
    }

    if state.players[target_p_idx].looked_cards.is_empty() {
        let mut filter_attr = filter_attr_base;
        if is_total_cost {
            filter_attr |= 1u64 << 60;
        }
        let matched_ids: Vec<i32> = state.players[target_p_idx]
            .discard
            .iter()
            .filter(|&&cid| {
                db.get_member(cid).is_some()
                    && (filter_attr == 0 || state.card_matches_filter_with_ctx(db, cid, filter_attr, ctx))
            })
            .cloned()
            .collect();
        state.players[target_p_idx].looked_cards.extend(matched_ids);
        if state.players[target_p_idx].looked_cards.is_empty() {
            return HandlerResult::Continue;
        }

        let mut target_ctx = ctx.clone();
        target_ctx.player_id = target_p_idx as u8;
        target_ctx.v_remaining = remaining;
        target_ctx.v_accumulated = ctx.v_accumulated;
        target_ctx.choice_index = -1;

        if matches!(suspend_choice(
            state,
            db,
            &target_ctx,
            &target_ctx,
            instr_ip,
            O_PLAY_MEMBER_FROM_DISCARD,
            s,
            ChoiceType::SelectDiscardPlay,
            filter_attr,
            remaining,
        ), HandlerResult::Suspend) {
            return HandlerResult::Suspend;
        }
    }

    let idx = ctx.choice_index as usize;
    let cards_len = state.players[target_p_idx].looked_cards.len();

    if idx < cards_len {
        let cid = state.players[target_p_idx].looked_cards[idx];
        state.players[target_p_idx].looked_cards.clear();
        state.players[target_p_idx].looked_cards.push(cid);

        let next_remaining = remaining - 1;
        let mut target_ctx = ctx.clone();
        target_ctx.player_id = target_p_idx as u8;
        target_ctx.v_remaining = next_remaining;
        target_ctx.v_accumulated = ctx.v_accumulated;
        target_ctx.choice_index = -1;

        let choice_type = if baton_slot_only {
            ChoiceType::SelectStageEmptyBaton
        } else if empty_slot_only {
            ChoiceType::SelectStageEmpty
        } else {
            ChoiceType::SelectStage
        };
        if matches!(suspend_choice(
            state,
            db,
            &target_ctx,
            &target_ctx,
            instr_ip,
            O_PLAY_MEMBER_FROM_DISCARD,
            s,
            choice_type,
            filter_attr_base,
            next_remaining,
        ), HandlerResult::Suspend) {
            return HandlerResult::Suspend;
        }
    }

    HandlerResult::Continue
}
