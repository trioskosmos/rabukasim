use crate::core::logic::models::AbilityFrame;
use super::*;
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;

#[allow(clippy::too_many_arguments)]
pub fn handle_play_member_from_hand(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame: &AbilityFrame,
    frame_idx: usize,
    p_idx: usize,
    v: i32,
    a: i64,
    s: i32,
) -> HandlerResult {
    let remaining = if ctx.v_remaining == -1 {
        if v == 1 { 1 } else { 2 }
    } else {
        ctx.v_remaining
    };

    if remaining == 2 {
        if ctx.choice_index == -1 {
            if matches!(suspend_choice(
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
            ), HandlerResult::Suspend) {
                return HandlerResult::Suspend;
            }
        }
        let h_idx = ctx.choice_index as usize;
        if h_idx < state.players[p_idx].hand.len() {
            ctx.target_slot = h_idx as i16;
            ctx.v_remaining = 1;
            ctx.choice_index = -1;
            return handle_play_member_from_hand(state, db, ctx, frame, frame_idx, p_idx, v, a, s);
        }
    } else if remaining == 1 {
        if ctx.choice_index == -1 {
            let mut next_ctx = ctx.clone();
            next_ctx.player_id = p_idx as u8;
            if matches!(suspend_choice(
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
            ), HandlerResult::Suspend) {
                return HandlerResult::Suspend;
            }
        }

        let slot_idx = ctx.choice_index as usize;
        if slot_idx < 3 {
            let h_idx = ctx.target_slot as usize;
            return state_member_play_resolve::finalize_play_member_from_hand(
                state, db, ctx, p_idx, h_idx, slot_idx,
            );
        }
    }

    HandlerResult::Continue
}
