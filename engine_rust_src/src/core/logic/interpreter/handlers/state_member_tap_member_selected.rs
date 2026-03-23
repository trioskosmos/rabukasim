use super::*;
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;
use crate::core::logic::models::AbilityFrame;

#[allow(clippy::too_many_arguments)]
pub fn handle_tap_member_selected(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame: &AbilityFrame,
    frame_idx: usize,
    p_idx: usize,
    a: i64,
    resolved_slot: i32,
) -> HandlerResult {
    let frame_data = frame.components();
    let is_optional = frame_data.filter.is_optional;
    let self_source_is_on_stage = ctx.area_idx >= 0 && ctx.area_idx < 3;
    let is_choice_done = ctx.choice_index == CHOICE_DONE;
    let filter_attr = frame_data.raw_attr & !crate::core::logic::filter::FILTER_STATE_FLAGS_MASK;
    let fixed_slot_matches = if resolved_slot >= 0 && resolved_slot < 3 {
        let cid = state.players[p_idx].stage[resolved_slot as usize];
        cid >= 0 && state.card_matches_filter_with_ctx(db, cid, filter_attr, ctx)
    } else {
        false
    };
    let needs_selection = (a & 0x02) != 0 || (!fixed_slot_matches && filter_attr != 0);

    if !self_source_is_on_stage && resolved_slot == 4 && !needs_selection {
        return HandlerResult::SetCond(false);
    }

    if is_optional || (a & 0x01) != 0 {
        if is_optional && ctx.v_remaining == -1 {
            if is_choice_done || ctx.choice_index == 1 {
                return HandlerResult::SetCond(false);
            }

            if ctx.choice_index != 0 {
                if matches!(
                    suspend_choice(
                        state,
                        db,
                        ctx,
                        ctx,
                        frame_idx,
                        O_TAP_MEMBER,
                        resolved_slot as i32,
                        ChoiceType::Optional,
                        a as u64,
                        -1,
                    ),
                    HandlerResult::Suspend
                ) {
                    return HandlerResult::Suspend;
                }
                return HandlerResult::Continue;
            }

            ctx.choice_index = -1;
            ctx.v_remaining = frame_data.value as i16;

            if resolved_slot >= 0 && resolved_slot < 3 && fixed_slot_matches {
                state.players[p_idx].set_tapped(resolved_slot as usize, true);
                return HandlerResult::SetCond(true);
            }

            if matches!(
                suspend_choice(
                    state,
                    db,
                    ctx,
                    ctx,
                    frame_idx,
                    O_TAP_MEMBER,
                    resolved_slot as i32,
                    ChoiceType::TapMSelect,
                    (a | 0x02) as u64,
                    frame_data.value as i16,
                ),
                HandlerResult::Suspend
            ) {
                return HandlerResult::Suspend;
            }
        }

        if is_optional && ctx.v_remaining != -1 {
            if ctx.choice_index >= 0 && ctx.choice_index < 3 {
                state.players[p_idx].set_tapped(ctx.choice_index as usize, true);
                return HandlerResult::SetCond(true);
            }
        }

        if is_choice_done || (ctx.v_remaining == -1 && ctx.choice_index == 1) {
            return HandlerResult::SetCond(false);
        }

        if needs_selection && ctx.choice_index == -1 {
            if matches!(
                suspend_choice(
                    state,
                    db,
                    ctx,
                    ctx,
                    frame_idx,
                    O_TAP_MEMBER,
                    0,
                    ChoiceType::TapMSelect,
                    (a | 0x02) as u64,
                    frame_data.value as i16,
                ),
                HandlerResult::Suspend
            ) {
                return HandlerResult::Suspend;
            }
        }

        if resolved_slot < 3 {
            state.players[p_idx].set_tapped(resolved_slot as usize, true);
        }
        return HandlerResult::SetCond(true);
    } else {
        if resolved_slot < 3 {
            state.players[p_idx].set_tapped(resolved_slot as usize, true);
        }
        return HandlerResult::SetCond(true);
    }
}
