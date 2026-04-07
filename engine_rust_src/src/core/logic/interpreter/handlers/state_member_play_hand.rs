use super::*;
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;
use crate::core::logic::models::AbilityFrameComponents;

#[allow(clippy::too_many_arguments)]
pub fn handle_play_member_from_hand(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    _frame_data: &AbilityFrameComponents<'_>,
    frame_idx: usize,
    p_idx: usize,
    v: i32,
    a: i64,
    s: i32,
) -> HandlerResult {
    let remaining = if ctx.v_remaining == -1 {
        if v == 1 {
            1
        } else {
            2
        }
    } else {
        ctx.v_remaining
    };

    if remaining == 2 {
        if ctx.choice_index == -1 {
            if matches!(
                suspend_choice(
                    state,
                    db,
                    ctx,
                    ctx,
                    frame_idx,
                    O_PLAY_MEMBER_FROM_HAND,
                    0,
                    ChoiceType::SelectHandPlay,
                    a as u64,
                    remaining,
                ),
                HandlerResult::Suspend
            ) {
                return HandlerResult::Suspend;
            }
        }
        let h_idx = ctx.choice_index as usize;
        if h_idx < state.players[p_idx].hand.len() {
            let chosen_card_id = state.players[p_idx].hand[h_idx];
            ctx.selected_hand_idx = h_idx as i16;
            ctx.target_slot = h_idx as i16;
            ctx.target_card_id = chosen_card_id;
            ctx.selected_cards = smallvec::smallvec![chosen_card_id];
            ctx.v_remaining = 1;
            ctx.choice_index = -1;
            return handle_play_member_from_hand(state, db, ctx, _frame_data, frame_idx, p_idx, v, a, s);
        }
    } else if remaining == 1 {
        if ctx.choice_index == -1 {
            let mut next_ctx = ctx.clone();
            next_ctx.player_id = p_idx as u8;
            if ctx.selected_hand_idx >= 0 {
                let chosen_card_id = state.players[p_idx]
                    .hand
                    .get(ctx.selected_hand_idx as usize)
                    .copied()
                    .unwrap_or(-1);
                if chosen_card_id < 0 {
                    return HandlerResult::Continue;
                }
                next_ctx.target_card_id = chosen_card_id;
                next_ctx.selected_cards = smallvec::smallvec![chosen_card_id];
            } else if next_ctx.target_card_id < 0 {
                return HandlerResult::Continue;
            }
            if matches!(
                suspend_choice(
                    state,
                    db,
                    ctx,
                    &next_ctx,
                    frame_idx,
                    O_PLAY_MEMBER_FROM_HAND,
                    s,
                    ChoiceType::SelectStage,
                    a as u64,
                    remaining,
                ),
                HandlerResult::Suspend
            ) {
                return HandlerResult::Suspend;
            }
        }

        let slot_idx = ctx.choice_index as usize;
        if slot_idx < 3 {
            let h_idx = ctx.selected_hand_idx as usize;
            return state_member_play_resolve::finalize_play_member_from_hand(
                state, db, ctx, p_idx, h_idx, slot_idx,
            );
        }
    }

    HandlerResult::Continue
}
